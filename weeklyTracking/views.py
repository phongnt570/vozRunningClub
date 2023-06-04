import datetime
import json
import logging

import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import JoinChallengeForm
from .models import WeeklyProgress, SettingClubDescription, SettingRegisteredMileage, StravaRunner, \
    SettingStravaAPIClient
from .registration import handle_get_user_by_refresh_token, handle_join_challenge_request, \
    handle_strava_exchange_code
from .utils import handle_leaderboard_update_request, is_registration_open, get_current_registration_week, \
    validate_year_week, \
    get_available_weeks

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
                                                                                      "-registered_mileage__distance",
                                                                                      "runner__strava_name")

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
    if WeeklyProgress.objects.filter(week_num=requested_week_num, year=requested_year).exists():
        last_updated = WeeklyProgress.objects.filter(week_num=requested_week_num, year=requested_year).order_by(
            "-last_updated").first().last_updated

    available_weeks = {}
    for year, week_num in sorted(get_available_weeks(), reverse=True):
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
        "last_updated": last_updated,
    }

    return render(request, "weeklyTracking/leaderboard.html", context=context)


@staff_member_required
@require_POST
def post_update_leaderboard(request):
    try:
        handle_leaderboard_update_request()
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "success"})


# @staff_member_required
# def upload_file(request):
#     if request.method == "POST":
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             handle_uploaded_week_reg_file(request.FILES["file"])
#             return redirect("index")
#     else:
#         form = UploadFileForm()
#
#     return render(request, "weeklyTracking/upload.html", {"form": form})


def about(request):
    return render(request, "weeklyTracking/about.html", context={
        "club_description": SettingClubDescription.objects.get().club_description})


def top_donates(request):
    return render(request, "weeklyTracking/top_donates.html")


def registration(request):
    strava_client_id = "108204"
    callback_url = request.build_absolute_uri()

    strava_login_url = f"https://www.strava.com/oauth/authorize?client_id=" \
                       f"{strava_client_id}&response_type=code&redirect_uri=" \
                       f"{callback_url}&approval_prompt=auto&scope=read&state=test"

    strava_code = request.GET.get("code")
    refresh_token = request.session.get("user_strava_refresh_token")

    if refresh_token:  # user logged in
        try:
            strava_runner, weekly_progress = handle_get_user_by_refresh_token(refresh_token)
        except StravaRunner.DoesNotExist:
            strava_runner = None
            weekly_progress = None
    elif strava_code:  # user logged in for the first time
        strava_runner, weekly_progress = handle_strava_exchange_code(strava_code)
        # save refresh token in session cookies
        if strava_runner and weekly_progress:
            request.session["user_strava_refresh_token"] = strava_runner.strava_refresh_token
    else:  # user not logged in
        strava_runner = None
        weekly_progress = None

    # other data
    current_registration_week_start_date, current_registration_week_end_date = get_current_registration_week()
    current_registration_week_num = current_registration_week_start_date.isocalendar()[1]
    current_registration_week_year = current_registration_week_start_date.isocalendar()[0]
    available_mileages = SettingRegisteredMileage.objects.all().order_by("distance")

    return render(request, "weeklyTracking/registration.html", context={
        "strava_runner": strava_runner,
        "weekly_progress": weekly_progress,
        "strava_login_url": strava_login_url,
        "is_registration_open": is_registration_open(),
        "current_registration_week_start_date": current_registration_week_start_date,
        "current_registration_week_end_date": current_registration_week_end_date,
        "available_mileages": available_mileages,
        "current_registration_week_num": current_registration_week_num,
        "current_registration_week_year": current_registration_week_year,
        "club_description": SettingClubDescription.objects.get().club_description,
    })


@require_POST
def join_challenge(request):
    form = JoinChallengeForm(request.POST)

    if form.is_valid():
        strava_runner_id = form.cleaned_data["strava_runner_id"]
        voz_name = form.cleaned_data.get("voz_name", "")
        registered_mileage_distance = form.cleaned_data.get("registered_mileage_distance", 0)
        week_num = form.cleaned_data["week_num"]
        year = form.cleaned_data["year"]

        try:
            handle_join_challenge_request(
                strava_runner_id=strava_runner_id,
                registered_mileage_distance=registered_mileage_distance,
                voz_name=voz_name,
                year=year,
                week_num=week_num
            )
            logger.info(
                f"Updated registration for "
                f"strava={strava_runner_id} voz={voz_name} "
                f"dis={registered_mileage_distance}km "
                f"year={year} week={week_num}")
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid form"})


def get_strava_access_token(strava_runner):
    refresh_token = strava_runner.strava_refresh_token
    if not refresh_token:
        return None

    strava_client_setting = SettingStravaAPIClient.objects.get()
    strava_client_id, strava_client_secret = strava_client_setting.client_id, strava_client_setting.client_secret

    query = {
        "client_id": strava_client_id,
        "client_secret": strava_client_secret,
        "refresh_token": refresh_token,
        "grant_type": 'refresh_token'
    }
    response = requests.post("https://www.strava.com/oauth/token", params=query)

    if response.status_code == 200:
        response_json = response.json()
        return response_json["access_token"]

    return None


@require_POST
def forget_strava(request):
    data = json.loads(request.body)
    strava_runner_id = data["strava_runner_id"]

    try:
        strava_runner = StravaRunner.objects.get(strava_id=strava_runner_id)
    except StravaRunner.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Strava runner not found"})

    if strava_runner.strava_refresh_token != request.session.get("user_strava_refresh_token"):
        return JsonResponse({"status": "error", "message": "Invalid refresh token"})

    access_token = get_strava_access_token(strava_runner)
    try:
        requests.post("https://www.strava.com/oauth/deauthorize", params={"access_token": access_token})
    except Exception as e:
        logger.error(f"Error forgetting strava: {e}")

    strava_runner.strava_refresh_token = None
    strava_runner.save()

    request.session.pop("user_strava_refresh_token", None)

    return JsonResponse({"status": "success"})
