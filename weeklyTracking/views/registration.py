import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from weeklyTracking.forms import WeeklyRegistrationForm
from weeklyTracking.models import SettingClubDescription, SettingRegisteredMileage, UserProfile, SettingStravaClub
from weeklyTracking.utils.donation import update_donation
from weeklyTracking.utils.registration import is_registration_open, get_current_registration_week, \
    create_or_get_weekly_progress
from weeklyTracking.utils.strava_auth_model import get_strava_profile, check_strava_connection, check_strava_club_joined

logger = logging.getLogger(__name__)


def registration(request):
    current_registration_week_start_date, current_registration_week_end_date = get_current_registration_week()
    current_registration_week_num = current_registration_week_start_date.isocalendar()[1]
    current_registration_week_year = current_registration_week_start_date.isocalendar()[0]
    available_mileages = SettingRegisteredMileage.objects.all().order_by("distance")

    weekly_progress = None
    strava_connected = False
    strava_profile = None
    strava_club_joined = False
    strava_club_url = SettingStravaClub.objects.get().club_url

    if request.user.is_authenticated:
        if get_strava_profile(request.user):
            weekly_progress = create_or_get_weekly_progress(user=request.user, week_num=current_registration_week_num,
                                                            year=current_registration_week_year)
        UserProfile.objects.get_or_create(user=request.user)

        strava_connected = check_strava_connection(request.user)
        strava_profile = get_strava_profile(request.user)
        strava_club_joined = check_strava_club_joined(request.user, save=True)

    return render(request, "weeklyTracking/registration.html", context={
        "weekly_progress": weekly_progress,
        "is_registration_open": is_registration_open(),
        "current_registration_week_start_date": current_registration_week_start_date,
        "current_registration_week_end_date": current_registration_week_end_date,
        "available_mileages": available_mileages,
        "current_registration_week_num": current_registration_week_num,
        "current_registration_week_year": current_registration_week_year,
        "club_description": SettingClubDescription.objects.get().club_description,
        "strava_connected": strava_connected,
        "strava_profile": strava_profile,
        "strava_club_joined": strava_club_joined,
        "strava_club_url": strava_club_url,
    })


@require_POST
@login_required
def weekly_registration(request):
    if not get_strava_profile(request.user):
        return JsonResponse({"status": "error", "message": "You need to connect your Strava account first"})

    form = WeeklyRegistrationForm(request.POST)

    if form.is_valid():
        registered_mileage_distance = form.cleaned_data.get("registered_mileage_distance", 0)
        week_num = form.cleaned_data["week_num"]
        year = form.cleaned_data["year"]
        note = form.cleaned_data.get("note", "")

        current_registration_week_start_date, current_registration_week_end_date = get_current_registration_week()
        current_registration_week_num = current_registration_week_start_date.isocalendar()[1]
        current_registration_week_year = current_registration_week_start_date.isocalendar()[0]

        if week_num != current_registration_week_num or year != current_registration_week_year:
            return JsonResponse({"status": "error", "message": "Invalid week/year"})

        weekly_progress = create_or_get_weekly_progress(user=request.user, week_num=week_num, year=year)

        if is_registration_open():
            weekly_progress.registered_mileage = SettingRegisteredMileage.objects.get(
                distance=registered_mileage_distance)
            update_donation(weekly_progress)

        weekly_progress.note = note
        weekly_progress.save()

        return JsonResponse({"status": "success"})

    else:
        return JsonResponse({"status": "error", "message": "Invalid form"})
