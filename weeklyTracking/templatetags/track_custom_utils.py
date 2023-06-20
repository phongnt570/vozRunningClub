import datetime

from django import template
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

from weeklyTracking.models import WeeklyProgress
from weeklyTracking.utils.time import get_last_week_year_and_week_num

register = template.Library()


def missing_distance(week_progress: WeeklyProgress):
    return max(0.0, week_progress.registered_mileage.distance - week_progress.distance)


@register.filter
def missing_distance_str(week_progress: WeeklyProgress):
    d = max(0.0, week_progress.registered_mileage.distance - week_progress.distance)
    if week_progress.registered_mileage.distance == 0:
        return "--"

    if d == 0:
        return "Đã xong!"

    return f"{d:.1f} <span class='d-none d-md-inline'>km</span>"


@register.filter
def pace_format(seconds: int):
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


# @register.filter
# def donation(week_progress: WeeklyProgress):
#     reg_dis = int(week_progress.registered_mileage.distance)
#     if SettingWeekBaseDonation.objects.filter(distance=reg_dis, year=week_progress.year,
#                                               week_num=week_progress.week_num).exists():
#         donation_per_km = SettingWeekBaseDonation.objects.get(distance=reg_dis, year=week_progress.year,
#                                                               week_num=week_progress.week_num).base_donation
#     else:
#         donation_per_km = SettingDefaultWeekBaseDonation.objects.get(distance=reg_dis).base_donation
#
#     if reg_dis == 0:
#         return "--"
#
#     if reg_dis > 0 and week_progress.distance == 0:
#         if SettingDefaultDonationByWeek.objects.filter(year=week_progress.year,
#                                                        week_num=week_progress.week_num).exists():
#             amount = SettingDefaultDonationByWeek.objects.get(year=week_progress.year,
#                                                               week_num=week_progress.week_num).default_donation
#         else:
#             amount = SettingDefaultDonation.objects.get().default_donation
#     else:
#         amount = donation_per_km * missing_distance(week_progress)
#
#     return f"{math.ceil(amount):,} ₫"


@register.filter
def get_strava_id(user: User):
    try:
        return user.social_auth.get(provider="strava").uid
    except UserSocialAuth.DoesNotExist:
        return None


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def week_time_str(year: int, week_num: int) -> str:
    start_date = datetime.datetime.fromisocalendar(year, week_num, 1)
    end_date = datetime.datetime.fromisocalendar(year, week_num, 7)

    this_year, this_week_num, _ = datetime.datetime.now().isocalendar()
    last_week_year, last_week_num = get_last_week_year_and_week_num()

    if year == this_year and week_num == this_week_num:
        return "Tuần này"

    if year == last_week_year and week_num == last_week_num:
        return "Tuần trước"

    return f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"


@register.filter
def absolute(value):
    return abs(value)
