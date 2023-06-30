import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from weeklyTracking.forms import UserProfileForm
from weeklyTracking.models import WeeklyProgress, UserProfile, SettingStravaClub
from weeklyTracking.utils.strava_auth_model import get_strava_profile, check_strava_connection, check_strava_club_joined

logger = logging.getLogger(__name__)


@login_required
def profile(request):
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]

    strava_profile = get_strava_profile(request.user)
    strava_connected = check_strava_connection(request.user)
    strava_club_joined = check_strava_club_joined(request.user, save=True)

    strava_club_url = SettingStravaClub.objects.get().club_url

    weekly_progresses = WeeklyProgress.objects.filter(user=request.user).order_by("-year", "-week_num")

    weekly_progresses_json = []
    for weekly_progress in weekly_progresses:
        weekly_progresses_json.append({
            "week_num": weekly_progress.week_num,
            "year": weekly_progress.year,
            "distance": weekly_progress.distance,
            "registered_mileage": weekly_progress.registered_mileage.distance,
        })

    return render(request, "weeklyTracking/profile.html", context={
        "user_profile": user_profile,
        "strava_connected": strava_connected,
        "strava_club_joined": strava_club_joined,
        "strava_club_url": strava_club_url,
        "strava_profile": strava_profile,
        "weekly_progresses": weekly_progresses,
        "weekly_progresses_json": json.dumps([wp for wp in reversed(weekly_progresses_json)]),
    })


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
