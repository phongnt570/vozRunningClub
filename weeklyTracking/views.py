import datetime
import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from social_django.models import UserSocialAuth

from .forms import WeeklyRegistrationForm, UserProfileForm
from .models import WeeklyProgress, SettingClubDescription, SettingRegisteredMileage, UserProfile, SettingStravaClub, \
    WeeklyPost, ActualDonation
from .utils.donation import update_donation
from .utils.generics import get_available_weeks_in_db
from .utils.registration import is_registration_open, get_current_registration_week, create_or_get_weekly_progress
from .utils.strava_auth_model import get_strava_profile, check_strava_connection, check_strava_club_joined
from .utils.time import validate_year_week, get_last_week_year_and_week_num

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

    requested_week_data = WeeklyProgress.objects.filter(Q(year=requested_year) & Q(week_num=requested_week_num) & (
                Q(distance__gt=0) | Q(registered_mileage__distance__gt=0))).order_by("-distance",
                                                                                     "-registered_mileage__distance")

    requested_week_start = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    requested_week_end = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 7)

    this_week_start = datetime.datetime.fromisocalendar(this_year, this_week_num, 1)

    reg_map = {}
    for weekly_progress in requested_week_data:
        reg_dis = weekly_progress.registered_mileage.distance
        if reg_dis not in reg_map:
            reg_map[reg_dis] = []
        reg_map[reg_dis].append(weekly_progress)

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
            value = "Tuần này"
        else:
            start_date = datetime.datetime.fromisocalendar(year, week_num, 1)
            end_date = datetime.datetime.fromisocalendar(year, week_num, 7)
            if end_date == this_week_start + datetime.timedelta(days=-1):
                value = "Tuần trước"
            elif start_date == this_week_start + datetime.timedelta(days=7):
                value = "Tuần sau"
            else:
                value = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

        available_weeks[(year, week_num)] = value

    # create a week summary
    total_distance = 0
    total_runs = 0
    total_donation = 0
    completed_challenges = 0
    total_challenges = 0
    for weekly_progress in requested_week_data:
        total_distance += weekly_progress.distance
        total_runs += weekly_progress.runs
        if weekly_progress.registered_mileage.distance > 0:
            total_donation += weekly_progress.donation
            total_challenges += 1
            if weekly_progress.distance >= weekly_progress.registered_mileage.distance:
                completed_challenges += 1
    week_summary = {
        "total_distance": total_distance,
        "total_runs": total_runs,
        "total_donation": total_donation,
        "completed_challenges": completed_challenges,
        "total_challenges": total_challenges,
    }

    try:
        actual_donation = ActualDonation.objects.get(week_num=requested_week_num, year=requested_year)
    except ActualDonation.DoesNotExist:
        actual_donation = None

    try:
        weekly_post = WeeklyPost.objects.get(week_num=requested_week_num, year=requested_year)
    except WeeklyPost.DoesNotExist:
        weekly_post = None

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
        "week_summary": week_summary,
        "actual_donation": actual_donation,
        "donation_diff": actual_donation.amount - total_donation if actual_donation else None,
        "weekly_post": weekly_post,
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


@login_required
def profile(request):
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]

    strava_profile = get_strava_profile(request.user)
    strava_connected = check_strava_connection(request.user)
    strava_club_joined = check_strava_club_joined(request.user, save=True)

    strava_club_url = SettingStravaClub.objects.get().club_url

    this_year = datetime.date.today().isocalendar()[0]
    this_week_num = datetime.date.today().isocalendar()[1]
    current_week = create_or_get_weekly_progress(user=request.user, week_num=this_week_num, year=this_year)

    # total_donation_till_now = 0
    # for wp in WeeklyProgress.objects.filter(user=request.user):
    #     if wp.week_num == this_week_num and wp.year == this_year:
    #         continue
    #     total_donation_till_now += wp.donation

    weekly_progresses = WeeklyProgress.objects.filter(user=request.user).order_by("-year", "-week_num")

    return render(request, "weeklyTracking/profile.html", context={
        "user_profile": user_profile,
        "strava_connected": strava_connected,
        "strava_club_joined": strava_club_joined,
        "strava_club_url": strava_club_url,
        "strava_profile": strava_profile,
        "current_week": current_week,
        # "total_donation_till_now": total_donation_till_now,
        "weekly_progresses": weekly_progresses,
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


def statistics(request):
    this_year, this_week_num, _ = datetime.date.today().isocalendar()
    last_week_year, last_week_num = get_last_week_year_and_week_num()

    week_summaries = {}

    for wp in WeeklyProgress.objects.all():
        key = (wp.year, wp.week_num)

        if key not in week_summaries:
            start_date = datetime.datetime.fromisocalendar(wp.year, wp.week_num, 1)
            end_date = datetime.datetime.fromisocalendar(wp.year, wp.week_num, 7)

            time = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            if wp.week_num == this_week_num and wp.year == this_year:
                time = "Tuần này"
            elif wp.week_num == last_week_num and wp.year == last_week_year:
                time = "Tuần trước"

            week_summaries[key] = {
                "year": wp.year,
                "week_num": wp.week_num,
                "time": time,
                "runners": 0,
                "runs": 0,
                "distance": 0,
                "registrations": 0,
                "completed": 0,
                "donation": 0,
            }

        if wp.distance > 0 or wp.registered_mileage.distance > 0:
            week_summaries[key]["runners"] += 1
        week_summaries[key]["runs"] += wp.runs
        week_summaries[key]["distance"] += wp.distance
        if wp.registered_mileage.distance > 0:
            week_summaries[key]["registrations"] += 1
            if wp.distance >= wp.registered_mileage.distance:
                week_summaries[key]["completed"] += 1
        week_summaries[key]["donation"] += wp.donation

    for _, ws in week_summaries.items():
        try:
            ws["actual_donation"] = ActualDonation.objects.get(year=ws["year"], week_num=ws["week_num"]).amount
        except ActualDonation.DoesNotExist:
            ws["actual_donation"] = 0
        ws["donation_diff"] = ws["actual_donation"] - ws["donation"]
        if ws["year"] == this_year and ws["week_num"] == this_week_num:
            ws["donation_diff"] = 0

    all_time = {
        "runs": sum([ws["runs"] for _, ws in week_summaries.items()]),
        "distance": sum([ws["distance"] for _, ws in week_summaries.items()]),
        "actual_donation": sum([ws["actual_donation"] for _, ws in week_summaries.items()]),
    }

    context = {
        "all_time": all_time,
        "week_summaries": sorted(week_summaries.values(), key=lambda x: (x["year"], x["week_num"]), reverse=True),
    }

    return render(request, "weeklyTracking/statistics.html", context=context)
