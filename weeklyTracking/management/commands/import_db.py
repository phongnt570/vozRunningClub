import csv
import os

import requests
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from social_django.models import UserSocialAuth

from weeklyTracking.models import SettingClubDescription, UserProfile, SettingRegisteredMileage, WeeklyProgress


def do_refresh_token(refresh_token):
    if not refresh_token:
        return {}

    strava_client_id = os.environ.get("SOCIAL_AUTH_STRAVA_KEY")
    strava_client_secret = os.environ.get("SOCIAL_AUTH_STRAVA_SECRET")

    query = {
        "client_id": strava_client_id,
        "client_secret": strava_client_secret,
        "refresh_token": refresh_token,
        "grant_type": 'refresh_token'
    }
    try:
        response = requests.post("https://www.strava.com/oauth/token", params=query)

        if response.status_code == 200:
            response_json = response.json()
            print(response_json)
            return response_json
    except Exception as e:
        print(e)
        return {}

    return {}


class Command(BaseCommand):
    help = 'Import old data to database'

    def add_arguments(self, parser):
        parser.add_argument('cd', type=str)
        parser.add_argument('sr', type=str)
        parser.add_argument('wp', type=str)

    def handle(self, *args, **options):
        cd = options['cd']
        sr = options['sr']
        wp = options['wp']

        # Club Description
        self.stdout.write('Importing Club Description')
        with open(cd, 'r') as f:
            text = f.read()
            SettingClubDescription.objects.create(club_description=text)
        self.stdout.write('Importing Club Description - Done')

        # Strava Runners
        self.stdout.write('Importing Strava Runners')
        with open(sr, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                strava_id = int(row['strava_id'])
                strava_name = row['strava_name']
                first_name = " ".join(strava_name.split(" ")[:-1])
                last_name = strava_name.split(" ")[-1]
                refresh_token = row['strava_refresh_token']
                voz_name = row['voz_name']

                # create user
                try:
                    user = User.objects.get(social_auth__uid=strava_id)
                except User.DoesNotExist:
                    user = User(
                        username=f"strava_{strava_id}",
                    )
                user.first_name = first_name
                user.last_name = last_name
                user.save()

                # update user profile
                try:
                    user_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    user_profile = UserProfile(user=user)
                user_profile.voz_name = voz_name
                user_profile.save()

                # update strava profile
                try:
                    strava_profile = user.social_auth.get(provider="strava")
                except UserSocialAuth.DoesNotExist:
                    strava_profile = UserSocialAuth.objects.create(user=user,
                                                                   provider="strava",
                                                                   uid=strava_id,
                                                                   extra_data="{}")

                extra_data = do_refresh_token(refresh_token)
                strava_profile.set_extra_data(extra_data)
                strava_profile.save()
        self.stdout.write('Importing Strava Runners - Done')

        # Weekly Progress
        self.stdout.write('Importing Weekly Progress')
        with open(wp, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                strava_id = int(row['strava_id'])
                week_num = int(row['week_num'])
                year = int(row['year'])
                registered_distance = float(row['registered_distance'])
                distance = float(row['distance'])
                runs = int(row['runs'])
                longest_run = float(row['longest_run'])
                average_pace = float(row['average_pace'])
                elevation_gain = float(row['elevation_gain'])
                note = row['note']

                # get user
                user = User.objects.get(social_auth__uid=strava_id, social_auth__provider="strava")

                # get registered milage
                registered_mileage = SettingRegisteredMileage.objects.get(distance=registered_distance)

                # update weekly progress
                try:
                    weekly_progress = WeeklyProgress.objects.get(user=user, week_num=week_num, year=year)
                except WeeklyProgress.DoesNotExist:
                    weekly_progress = WeeklyProgress(user=user, week_num=week_num, year=year,
                                                     registered_mileage=registered_mileage)

                weekly_progress.registered_mileage = registered_mileage
                weekly_progress.distance = distance
                weekly_progress.runs = runs
                weekly_progress.longest_run = longest_run
                weekly_progress.average_pace = average_pace
                weekly_progress.elevation_gain = elevation_gain
                weekly_progress.note = note

                weekly_progress.save()

        self.stdout.write('Importing Weekly Progress - Done')
