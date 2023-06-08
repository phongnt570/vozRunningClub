import datetime
from typing import Tuple

from django.contrib.auth.models import User

from weeklyTracking.models import WeeklyProgress, SettingRegisteredMileage


def is_registration_open():
    """
    Returns True if the current date is within the registration phase
    (i.e., from 00:00:00 Sunday until 23:59:59 Monday)
    :return: True if in registration phase, False otherwise
    """
    today = datetime.date.today()
    return today.weekday() == 6 or today.weekday() == 0


def get_current_registration_week() -> Tuple[datetime.date, datetime.date]:
    """
    Returns the start and end dates of the current registration week
    :return: Tuple of start and end dates
    """
    today = datetime.date.today()

    # If today is Sunday, the registration week is next week
    if today.weekday() == 6:
        start_date = today + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=6)

    # If today is Monday, the registration week is this week
    else:
        # Start date is the most recent Monday
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)

    return start_date, end_date


def create_or_get_weekly_progress(user: User, year: int, week_num: int) -> WeeklyProgress:
    if WeeklyProgress.objects.filter(
            user=user,
            week_num=week_num,
            year=year).exists():
        weekly_progress = WeeklyProgress.objects.get(
            user=user,
            week_num=week_num,
            year=year
        )
    else:
        weekly_progress = WeeklyProgress.objects.create(
            user=user,
            week_num=week_num,
            year=year,
            registered_mileage=SettingRegisteredMileage.objects.get(distance=0),
            distance=0,
            runs=0,
            longest_run=0,
            average_pace=0,
            elevation_gain=0,
            note="",
        )

    return weekly_progress
