import datetime
import logging

from django.shortcuts import render
from social_django.models import UserSocialAuth

from weeklyTracking.models import WeeklyPost, ActualDonation
from weeklyTracking.templatetags.track_custom_utils import week_time_str
from weeklyTracking.utils.generics import get_available_weeks_in_db
from weeklyTracking.utils.ranking import get_ranked_users, user_rank_change
from weeklyTracking.utils.time import validate_year_week

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

    requested_week_progresses = get_ranked_users(year=requested_year, week_num=requested_week_num)
    rank_changes = user_rank_change(year=requested_year, week_num=requested_week_num)

    requested_week_start = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    requested_week_end = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 7)

    this_week_start = datetime.datetime.fromisocalendar(this_year, this_week_num, 1)

    reg_map = {}
    for weekly_progress in requested_week_progresses:
        reg_dis = weekly_progress.registered_mileage.distance
        if reg_dis not in reg_map:
            reg_map[reg_dis] = []
        reg_map[reg_dis].append(weekly_progress)

    distance2weekly_progress_list = {}
    distance2rank_change = {}
    for reg_dis in sorted(reg_map.keys(), reverse=True):
        distance2weekly_progress_list[reg_dis] = reg_map[reg_dis]
        distance2rank_change[reg_dis] = user_rank_change(year=requested_year, week_num=requested_week_num,
                                                         reg_distance=reg_dis)

    last_updated = None
    if distance2weekly_progress_list:
        last_updated = sorted([wp for wps in distance2weekly_progress_list.values() for wp in wps],
                              key=lambda x: x.last_updated)[-1].last_updated

    user_2_strava_id = {}
    all_user_ids_in_week = [wp.user.id for wps in distance2weekly_progress_list.values() for wp in wps]
    all_strava_profiles = UserSocialAuth.objects.filter(user_id__in=all_user_ids_in_week, provider="strava")
    for strava_profile in all_strava_profiles:
        user_2_strava_id[strava_profile.user_id] = strava_profile.uid

    available_weeks = {}
    for year, week_num in sorted(get_available_weeks_in_db(), reverse=True):
        value = week_time_str(year=year, week_num=week_num)
        available_weeks[(year, week_num)] = value

    # create a week summary
    total_distance = 0
    total_runs = 0
    total_donation = 0
    completed_challenges = 0
    total_challenges = 0
    for weekly_progress in requested_week_progresses:
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
        "requested_week_progresses": requested_week_progresses,
        "rank_changes": rank_changes,
        "requested_week_start": requested_week_start,
        "requested_week_end": requested_week_end,
        "distance2weekly_progress_list": distance2weekly_progress_list,
        "distance2rank_change": distance2rank_change,
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
