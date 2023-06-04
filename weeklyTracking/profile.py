
import datetime
import logging
import requests

from .models import StravaRunner, WeeklyProgress, SettingRegisteredMileage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
this_year = datetime.date.today().isocalendar()[0]
this_week_num = datetime.date.today().isocalendar()[1]

def handle_join_challenge_request(registered_mileage_distance, voz_name, strava_refresh_token):
    runner = StravaRunner.objects.get(strava_refresh_token=strava_refresh_token)
    
    if voz_name:
        runner.voz_name = voz_name
    runner.save()
    if registered_mileage_distance:
         
        registered_mileages =  SettingRegisteredMileage.objects.get(distance=registered_mileage_distance)
        if WeeklyProgress.objects.filter(runner=runner, week_num=this_week_num, year=this_year).exists():
                obj = WeeklyProgress.objects.get(runner=runner, week_num=this_week_num, year=this_year)
                if obj.registered_mileage.distance == 0:
                    obj.registered_mileage = registered_mileages
                    obj.save()
        else:
            WeeklyProgress.objects.create(
                    runner=runner,
                    week_num=this_week_num,
                    year=this_year,
                    registered_mileage=registered_mileages,
                    distance=0,
                    runs=0,
                    longest_run=0,
                    average_pace=0,
                    elevation_gain=0
                )

def handle_get_user_by_refresh_token(refresh_token):
    context = {}
    context["refresh_token"] = refresh_token
    obj = StravaRunner.objects.get(strava_refresh_token=context["refresh_token"])
    context["athlete_id"] = obj.strava_id
    context["voz_name"] = obj.voz_name
    context["strava_name"] = obj.strava_name
    if WeeklyProgress.objects.filter(runner_id=obj.strava_id, week_num =this_week_num, year=this_year).exists():
        progress = WeeklyProgress.objects.get(runner_id=obj.strava_id, week_num =this_week_num, year=this_year)
        context["registered_mileage"] = f'{progress.registered_mileage.distance}km'

    return context

def handle_strava_exchange_code(exchange_code):
    strava_client_id = "108204"
    strava_client_key = "a603ad31780bd0e3ceee0edeefec3c7122bc2156"
    context = {}
    query = {
            "client_id":strava_client_id,
            "client_secret": strava_client_key,
            "code": exchange_code,
            "grant_type": 'authorization_code'
        }
    response = requests.post("https://www.strava.com/oauth/token",params = query)
    if response.status_code == 200:
        result  = response.json()
        context["refresh_token"] = result["refresh_token"]
        context["athlete_id"] = result["athlete"]["id"]
        context["voz_name"] = ""
        context["strava_name"] = result["athlete"]["firstname"] + " " +result["athlete"]["lastname"]
        context["registered_mileage"] = f'{SettingRegisteredMileage.objects.get(distance=0).distance}km'

        if not StravaRunner.objects.filter(strava_id=context["athlete_id"]).exists():
            StravaRunner.objects.create(
                strava_id= context["athlete_id"],
                strava_name = context["strava_name"],
                voz_name = "",
                strava_refresh_token = context["refresh_token"]
            )
        else :
            obj = StravaRunner.objects.get(strava_id=context["athlete_id"])
            obj.strava_refresh_token = context["refresh_token"]
            context["voz_name"] = obj.voz_name
            if WeeklyProgress.objects.filter(runner_id=context["athlete_id"], week_num =this_week_num, year=this_year).exists():
                progress = WeeklyProgress.objects.get(runner_id=context["athlete_id"], week_num =this_week_num, year=this_year)
                context["registered_mileage"] = f'{progress.registered_mileage.distance}km'
            obj.save()

    return context