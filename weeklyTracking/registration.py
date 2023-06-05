import logging
from typing import Tuple

import requests

from .models import StravaRunner, WeeklyProgress, SettingRegisteredMileage, SettingStravaAPIClient
from .utils import get_current_registration_week

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_join_challenge_request(strava_runner_id, registered_mileage_distance, voz_name, year, week_num):
    runner = StravaRunner.objects.get(strava_id=strava_runner_id)

    if type(voz_name) == str:
        runner.voz_name = voz_name.strip()
        runner.save()

    registered_mileage = SettingRegisteredMileage.objects.get(distance=registered_mileage_distance)

    if WeeklyProgress.objects.filter(runner=runner, week_num=week_num, year=year).exists():
        weekly_progress = WeeklyProgress.objects.get(runner=runner, week_num=week_num, year=year)
        weekly_progress.registered_mileage = registered_mileage
        weekly_progress.save()
    else:
        WeeklyProgress.objects.create(
            runner=runner,
            week_num=week_num,
            year=year,
            registered_mileage=registered_mileage,
            distance=0,
            runs=0,
            longest_run=0,
            average_pace=0,
            elevation_gain=0
        )


def handle_get_user_by_refresh_token(strava_refresh_token: str) -> Tuple[StravaRunner, WeeklyProgress]:
    """
    This is invoked when a user is logged in and the page "Registration" is loaded.
    :param strava_refresh_token:
    :return:
    """

    start_date, end_date = get_current_registration_week()
    this_year = start_date.isocalendar()[0]
    this_week_num = start_date.isocalendar()[1]

    strava_runner = StravaRunner.objects.get(strava_refresh_token=strava_refresh_token)

    if WeeklyProgress.objects.filter(
            runner=strava_runner,
            week_num=this_week_num,
            year=this_year).exists():
        progress = WeeklyProgress.objects.get(
            runner=strava_runner,
            week_num=this_week_num,
            year=this_year)
    else:
        progress = WeeklyProgress.objects.create(
            runner=strava_runner,
            week_num=this_week_num,
            year=this_year,
            registered_mileage=SettingRegisteredMileage.objects.get(distance=0),
            distance=0,
            runs=0,
            longest_run=0,
            average_pace=0,
            elevation_gain=0
        )

    return strava_runner, progress


def handle_strava_exchange_code(exchange_code: str) -> Tuple[StravaRunner, WeeklyProgress]:
    """
    This is invoked when a user is logging in for the first time, which means it has been redirected from Strava.
    :param exchange_code:
    :return:
    """
    start_date, end_date = get_current_registration_week()
    this_year = start_date.isocalendar()[0]
    this_week_num = start_date.isocalendar()[1]

    strava_client_setting = SettingStravaAPIClient.objects.get()
    strava_client_id, strava_client_secret = strava_client_setting.client_id, strava_client_setting.client_secret

    query = {
        "client_id": strava_client_id,
        "client_secret": strava_client_secret,
        "code": exchange_code,
        "grant_type": 'authorization_code'
    }
    response = requests.post("https://www.strava.com/oauth/token", params=query)

    strava_runner = None
    weekly_progress = None

    if response.status_code == 200:
        response_json = response.json()

        strava_runner_id = response_json["athlete"]["id"]
        strava_name = f"{response_json['athlete']['firstname']} {response_json['athlete']['lastname']}"
        user_strava_refresh_token = response_json["refresh_token"]

        # Get or create StravaRunner
        if not StravaRunner.objects.filter(strava_id=strava_runner_id).exists():
            strava_runner = StravaRunner.objects.create(
                strava_id=strava_runner_id,
                strava_name=strava_name,
                voz_name="",
            )
        else:
            strava_runner = StravaRunner.objects.get(strava_id=strava_runner_id)
            strava_runner.strava_name = strava_name

        # Update StravaRunner with new refresh token
        strava_runner.strava_refresh_token = user_strava_refresh_token
        strava_runner.save()

        # Get or create WeeklyProgress
        if WeeklyProgress.objects.filter(runner_id=strava_runner_id, week_num=this_week_num,
                                         year=this_year).exists():
            weekly_progress = WeeklyProgress.objects.get(
                runner_id=strava_runner_id,
                week_num=this_week_num,
                year=this_year
            )
        else:
            weekly_progress = WeeklyProgress.objects.create(
                runner_id=strava_runner_id,
                week_num=this_week_num,
                year=this_year,
                registered_mileage=SettingRegisteredMileage.objects.get(distance=0),
                distance=0,
                runs=0,
                longest_run=0,
                average_pace=0,
                elevation_gain=0
            )

    return strava_runner, weekly_progress
