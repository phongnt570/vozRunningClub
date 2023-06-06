import datetime
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from .forms import WeeklyRegistrationForm, UserProfileForm
from .models import WeeklyProgress, SettingClubDescription, SettingRegisteredMileage, UserProfile
from .utils.generics import get_available_weeks_in_db
from .utils.registration import is_registration_open, get_current_registration_week, create_or_get_weekly_progress
from .utils.strava_auth_model import get_strava_profile
from .utils.time import validate_year_week

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def leaderboard(request):
    requested_year = request.GET.get("year")
    requested_week_num = request.GET.get("week")

    this_year = datetime.date.today().isocalendar()[0]
    this_week_num = datetime.date.today().isocalendar()[1]

    if not validate_year_week(requested_year, requested_week_num):
        requested_year = this_year
        requested_week_num = this_week_num
    else:
        requested_year = int(requested_year)
        requested_week_num = int(requested_week_num)

    requested_week_data = WeeklyProgress.objects.filter(week_num=requested_week_num,
                                                        year=requested_year).order_by("-distance",
                                                                                      "-registered_mileage__distance")

    requested_week_start = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    requested_week_end = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 7)

    this_week_start = datetime.datetime.fromisocalendar(this_year, this_week_num, 1)

    reg_map = {}
    for week_progress in requested_week_data:
        reg_dis = week_progress.registered_mileage.distance
        if reg_dis not in reg_map:
            reg_map[reg_dis] = []
        reg_map[reg_dis].append(week_progress)

    sorted_reg_map = {}
    for key in sorted(reg_map.keys(), reverse=True):
        sorted_reg_map[key] = reg_map[key]

    last_updated = None
    if sorted_reg_map:
        last_updated = sorted([wp for wps in sorted_reg_map.values() for wp in wps], key=lambda x: x.last_updated)[
            -1].last_updated

    user_2_strava_id = {}
    all_user_ids_in_week = [wp.user.id for wps in sorted_reg_map.values() for wp in wps]
    all_strava_profiles = UserSocialAuth.objects.filter(user_id__in=all_user_ids_in_week, provider="strava")
    for strava_profile in all_strava_profiles:
        user_2_strava_id[strava_profile.user_id] = strava_profile.uid

    available_weeks = {}
    for year, week_num in sorted(get_available_weeks_in_db(), reverse=True):
        if year == this_year and week_num == this_week_num:
            value = "This week"
        else:
            start_date = datetime.datetime.fromisocalendar(year, week_num, 1)
            end_date = datetime.datetime.fromisocalendar(year, week_num, 7)
            if end_date == this_week_start + datetime.timedelta(days=-1):
                value = "Last week"
            elif start_date == this_week_start + datetime.timedelta(days=7):
                value = "Next week"
            else:
                value = f"Week: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

        available_weeks[(year, week_num)] = value

    context = {
        "requested_year": requested_year,
        "requested_week_num": requested_week_num,
        "requested_week_data": requested_week_data,
        "requested_week_start": requested_week_start,
        "requested_week_end": requested_week_end,
        "reg_map": sorted_reg_map,
        "is_this_week": requested_week_start == this_week_start,
        "is_last_week": requested_week_end == this_week_start + datetime.timedelta(days=-1),
        "available_weeks": available_weeks,
        "user_2_strava_id": user_2_strava_id,
        "last_updated": last_updated,
    }

    return render(request, "weeklyTracking/leaderboard.html", context=context)


def about(request):
    return render(request, "weeklyTracking/about.html", context={
        "club_description": SettingClubDescription.objects.get().club_description})


def top_donates(request):
    return render(request, "weeklyTracking/top_donates.html")


def registration(request):
    # other data
    current_registration_week_start_date, current_registration_week_end_date = get_current_registration_week()
    current_registration_week_num = current_registration_week_start_date.isocalendar()[1]
    current_registration_week_year = current_registration_week_start_date.isocalendar()[0]
    available_mileages = SettingRegisteredMileage.objects.all().order_by("distance")

    weekly_progress = None
    if request.user.is_authenticated:
        if get_strava_profile(request.user):
            weekly_progress = create_or_get_weekly_progress(user=request.user, week_num=current_registration_week_num,
                                                            year=current_registration_week_year)
        UserProfile.objects.get_or_create(user=request.user)

    return render(request, "weeklyTracking/registration.html", context={
        "weekly_progress": weekly_progress,
        "is_registration_open": is_registration_open(),
        "current_registration_week_start_date": current_registration_week_start_date,
        "current_registration_week_end_date": current_registration_week_end_date,
        "available_mileages": available_mileages,
        "current_registration_week_num": current_registration_week_num,
        "current_registration_week_year": current_registration_week_year,
        "club_description": SettingClubDescription.objects.get().club_description,
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
            weekly_progress.registered_mileage_distance = registered_mileage_distance

        weekly_progress.note = note
        weekly_progress.save()

        return JsonResponse({"status": "success"})

    else:
        return JsonResponse({"status": "error", "message": "Invalid form"})


# @require_POST
@require_POST
def disconnect_strava(request):
    return JsonResponse({"status": "success"})


@login_required
def profile(request):
    UserProfile.objects.get_or_create(user=request.user)
    return render(request, "weeklyTracking/profile.html")


@login_required
@require_POST
def update_profile(request):
    form = UserProfileForm(request.POST)

    if form.is_valid():
        user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
        user_profile.voz_name = form.cleaned_data.get("voz_name", "")
        user_profile.save()

        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid form"})


@login_required
@require_POST
def update_strava(request):
    try:
        strava_profile = get_strava_profile(request.user)
        if not strava_profile:
            return JsonResponse({"status": "error", "message": "You need to connect your Strava account first"})
        try:
            strategy = load_strategy()
            access_token = strava_profile.get_access_token(strategy)
            backend = strava_profile.get_backend_instance(strategy)
            user_details = backend.user_data(access_token=access_token)
        except Exception as e:
            raise e
            # return JsonResponse(
            #     {"status": "error", "message": "Strava authentication failed! Please log out and try again."})

        request.user.first_name = user_details.get("firstname", "")
        request.user.last_name = user_details.get("lastname", "")
        request.user.save()

        return JsonResponse({
            "status": "success",
            "strava_name": request.user.get_full_name()
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Error: {str(e)}"})
