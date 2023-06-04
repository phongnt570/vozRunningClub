import csv
import datetime
import logging
import os
from io import StringIO
from typing import List, Dict, Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from .models import StravaRunner, WeeklyProgress, SettingStravaClub, SettingRegisteredMileage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_year_week(requested_year, requested_week_num):
    try:
        requested_year = int(requested_year)
        requested_week_num = int(requested_week_num)
    except (ValueError, TypeError):
        return False

    try:
        requested_first_weekday = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    except ValueError:
        return False

    next_week = (datetime.date.today() + datetime.timedelta(days=7)).isocalendar()
    next_week_monday = datetime.datetime.fromisocalendar(next_week[0], next_week[1], 1)

    if requested_first_weekday > next_week_monday:
        print(requested_first_weekday, next_week_monday)
        return False

    return True


def get_available_weeks():
    available_weeks = set()
    for week_progress in WeeklyProgress.objects.all():
        available_weeks.add((week_progress.year, week_progress.week_num))
    return available_weeks


def get_last_week():
    ic_last_week = (datetime.date.today() + datetime.timedelta(days=-7)).isocalendar()
    return ic_last_week[0], ic_last_week[1]


def get_elevation_gain(text):
    if text == "--":
        return 0.0
    else:
        return float(text.split()[0].replace(",", ""))


def get_average_pace_in_seconds(minute_second):
    if minute_second == "--":
        return 0.0
    else:
        minute, second = minute_second.split(":")
        return 60 * float(minute) + float(second)


def get_strava_leaderboards():
    if "GOOGLE_CHROME_BIN" in os.environ:  # Heroku
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH", "chromedriver"),
                                  chrome_options=chrome_options)
    else:
        driver = webdriver.Chrome()

    # get URL of Strava club
    club_url = SettingStravaClub.objects.get().club_url

    # navigate to Strava group page
    driver.get(club_url)

    # get "This Week's Leaderboard"
    try:
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, "div.leaderboard > table > tbody")))
    except TimeoutException:
        logger.info("Request Timed Out")

    # get this week's leaderboard
    ic = datetime.date.today().isocalendar()
    this_year, this_week_num = ic[0], ic[1]

    this_week_runners = get_data_from_driver(driver, year=this_year, week_num=this_week_num)

    # get last week's leaderboard
    last_week_btn = driver.find_element(By.CSS_SELECTOR, "span.button.last-week")
    last_week_btn.click()

    last_week_year, last_week_num = get_last_week()

    last_week_runners = get_data_from_driver(driver, year=last_week_year, week_num=last_week_num)

    driver.close()

    return this_week_runners, last_week_runners


def get_data_from_driver(driver, year, week_num):
    table = driver.find_element(By.CSS_SELECTOR, "div.leaderboard > table > tbody").get_attribute("innerHTML")
    soup = BeautifulSoup(table, "html.parser")

    # Example table row:
    #
    # <tr>
    # <td class="rank">1</td>
    # <td class="athlete">
    # <div class="avatar avatar-athlete avatar-sm">
    # <a class="avatar-content" href="/athletes/48089747">
    # <div class="avatar-img-wrapper avatar-default">
    #
    # <img alt="Minh Đức L." src="/assets/avatar/athlete/medium.png" title="Minh Đức L.">
    # </div>
    # </a>
    # </div>
    # <a class="athlete-name minimal" href="/athletes/48089747">
    # Minh Đức L.
    # </a>
    # </td>
    # <td class="distance highlighted-column">40.6 <abbr class="unit short" title="kilometers">km</abbr></td>
    # <td class="num-activities">2</td>
    # <td class="longest-activity">
    # 20.3 <abbr class="unit short" title="kilometers">km</abbr>
    # </td>
    # <td class="average-pace">5:35 <abbr class="unit short" title="minutes per kilometer">/km</abbr></td>
    # <td class="elev-gain">--</td>
    # </tr>

    runners = []
    for row in soup.find_all("tr"):
        runner = {
            "id": int(row.find("td", class_="athlete").find("a")["href"].split("/")[-1]),
            "name": row.find("a", class_="athlete-name").text.strip(),
            "distance": float(row.find("td", class_="distance").text.split()[0]),
            "runs": int(row.find("td", class_="num-activities").text),
            "longest_run": float(row.find("td", class_="longest-activity").text.split()[0]),
            "average_pace": get_average_pace_in_seconds(
                row.find("td", class_="average-pace").text.split("/")[0].strip()),
            "elevation_gain": get_elevation_gain(row.find("td", class_="elev-gain").text.strip()),
            "year": year,
            "week_num": week_num
        }

        runners.append(runner)

    return runners


def update_week_progress(strava_runners: List[Dict], remove_non_strava_runners: bool = False):
    if not strava_runners:
        return

    if len(set([runner["year"] for runner in strava_runners])) != 1:
        raise ValueError("All runners must be from the same year")

    if len(set([runner["week_num"] for runner in strava_runners])) != 1:
        raise ValueError("All runners must be from the same week")

    year = strava_runners[0]["year"]
    week_num = strava_runners[0]["week_num"]

    for runner in strava_runners:
        if not StravaRunner.objects.filter(strava_id=runner["id"]).exists():
            StravaRunner.objects.create(
                strava_id=runner["id"],
                strava_name=runner["name"],
                voz_name="",
            )

        if WeeklyProgress.objects.filter(runner_id=runner["id"], week_num=week_num, year=year).exists():
            obj = WeeklyProgress.objects.get(runner_id=runner["id"], week_num=week_num, year=year)
            obj.distance = runner["distance"]
            obj.runs = runner["runs"]
            obj.longest_run = runner["longest_run"]
            obj.average_pace = runner["average_pace"]
            obj.elevation_gain = runner["elevation_gain"]
            obj.save()
        else:
            WeeklyProgress.objects.create(
                runner_id=runner["id"],
                week_num=week_num,
                year=year,
                registered_mileage=SettingRegisteredMileage.objects.get(distance=0),
                distance=runner["distance"],
                runs=runner["runs"],
                longest_run=runner["longest_run"],
                average_pace=runner["average_pace"],
                elevation_gain=runner["elevation_gain"]
            )

    # Check if any runners have been removed from the real-time Strava leaderboard
    # If so, delete them from the database
    if not remove_non_strava_runners:
        return
    db_progress = WeeklyProgress.objects.filter(year=year, week_num=week_num)
    db_ids = set([obj.runner_id for obj in db_progress])
    strava_ids = set([runner["id"] for runner in strava_runners])
    removed_ids = db_ids - strava_ids
    if removed_ids:
        print(f"Removing {len(removed_ids)} runners from the database: {removed_ids}")
        WeeklyProgress.objects.filter(runner_id__in=removed_ids, year=year, week_num=week_num).delete()


def handle_leaderboard_update_request():
    logger.info("Fetching Strava Leaderboards")
    this_week_runners, last_week_runners = get_strava_leaderboards()

    # check if the leaderboard has been updated for the new week
    # issues happen on sunday night (time zone issues?)
    db_this_week_progress = WeeklyProgress.objects.filter(
        year=last_week_runners[0]["year"],
        week_num=last_week_runners[0]["week_num"]).order_by("-distance").all()
    db_this_week_runners = [{"id": obj.runner_id, "distance": obj.distance, "runs": obj.runs} for obj in
                            db_this_week_progress]
    simplified_this_week_runners = [{"id": runner["id"], "distance": runner["distance"], "runs": runner["runs"]} for
                                    runner in this_week_runners]
    if simplified_this_week_runners[:10] == db_this_week_runners[:10]:
        logger.info("Leaderboard has not been updated for the new week")
        return

    logger.info("Updating Week Progress Table")
    update_week_progress(this_week_runners, remove_non_strava_runners=True)
    # update_week_progress(last_week_runners, remove_non_strava_runners=False)
    logger.info("Leaderboard update complete")


def handle_uploaded_week_reg_file(f):
    logger.info("Handling uploaded file")
    reader = csv.DictReader(StringIO(f.read().decode("utf-8")))
    input_rows = [row for row in reader]
    logger.info(f"Read {len(input_rows)} rows from file")

    new_runners = []
    for row in input_rows:
        strava_id = int(row["strava_id"])
        strava_name = row["strava_name"]
        voz_name = row["voz_name"]

        if not StravaRunner.objects.filter(strava_id=strava_id).exists():
            new_runners.append(StravaRunner(strava_id=strava_id, strava_name=strava_name, voz_name=voz_name))
        else:
            runner = StravaRunner.objects.get(strava_id=strava_id)
            if strava_name:
                runner.strava_name = strava_name
            if voz_name:
                runner.voz_name = voz_name
            runner.save()

    if new_runners:
        logger.info(f"Adding {len(new_runners)} new runners")
        StravaRunner.objects.bulk_create(new_runners)
        logger.info("Done adding new runners")

    registered_mileages = {}
    for mileage in SettingRegisteredMileage.objects.all():
        registered_mileages[mileage.distance] = mileage

    logger.info("Updating weekly progress")
    for row in input_rows:
        strava_id = int(row["strava_id"])
        week_num = int(row["week_num"])
        year = int(row["year"])
        registered_mileage = registered_mileages[int(row["registered_distance"])]

        runner = StravaRunner.objects.get(strava_id=strava_id)

        if WeeklyProgress.objects.filter(runner=runner, week_num=week_num, year=year).exists():
            obj = WeeklyProgress.objects.get(runner=runner, week_num=week_num, year=year)
            obj.registered_mileage = registered_mileage
            obj.save()
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
    logger.info("Done!!!")


def is_registration_open():
    """
    Returns True if the current date is within the registration phase
    (i.e., from 00:00:00 Sunday until 23:59:59 Monday)
    :return: True if in registration phase, False otherwise
    """
    today = datetime.date.today()

    # If today is Sunday, check if it's after 00:00:00
    if today.weekday() == 6:
        return datetime.datetime.now().time() >= datetime.time(0, 0, 0)

    # If today is Monday, check if it's before 23:59:59
    if today.weekday() == 0:
        return datetime.datetime.now().time() <= datetime.time(23, 59, 59)

    # Otherwise, it's not Sunday or Monday, so we're not in the registration phase
    return False


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
