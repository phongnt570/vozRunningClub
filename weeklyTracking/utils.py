import datetime
import logging
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from .models import StravaRunner, WeeklyProgress, SettingStravaClub, SettingRegisteredMileage

logging.basicConfig(filename="weeklyTracking.log", level=logging.INFO)
logger = logging.getLogger(__name__)


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
    if "GOOGLE_CHROME_BIN" in os.environ:
        print("in heroku")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH", "chromedriver"),
                                  chrome_options=chrome_options)
    else:
        print("not in heroku")
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


def update_week_progress(runners):
    for runner in runners:
        if not StravaRunner.objects.filter(strava_id=runner["id"]).exists():
            StravaRunner.objects.create(
                strava_id=runner["id"],
                strava_name=runner["name"],
                voz_name="",
            )

        if WeeklyProgress.objects.filter(runner_id=runner["id"], week_num=runner["week_num"],
                                         year=runner["year"]).exists():
            obj = WeeklyProgress.objects.get(runner_id=runner["id"], week_num=runner["week_num"], year=runner["year"])
            obj.distance = runner["distance"]
            obj.runs = runner["runs"]
            obj.longest_run = runner["longest_run"]
            obj.average_pace = runner["average_pace"]
            obj.elevation_gain = runner["elevation_gain"]
            obj.save()
        else:
            WeeklyProgress.objects.create(
                runner_id=runner["id"],
                week_num=runner["week_num"],
                year=runner["year"],
                registered_mileage=SettingRegisteredMileage.objects.get(distance=0),
                distance=runner["distance"],
                runs=runner["runs"],
                longest_run=runner["longest_run"],
                average_pace=runner["average_pace"],
                elevation_gain=runner["elevation_gain"]
            )
