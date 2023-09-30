# Voz Running Club - Web App

## About

The web app is developed using Django and Python.
The app is hosted on Heroku and uses Heroku Postgres as the database.

## Heroku Deployment

1. Create a Heroku app
2. Go to Deploy, connect to GitHub repo
3. Go to Settings, add the following buildpacks: 
   - `heroku/chromedriver`
   - `heroku/google-chrome`
   - `heroku/python`
4. Add config vars:
   - `SOCIAL_AUTH_STRAVA_KEY`: Strava Client ID
   - `SOCIAL_AUTH_STRAVA_SECRET`: Strava Client Secret
   - `CHROMEDRIVER_PATH` = `/app/.chromedriver/bin/chromedriver`
5. Go to Resources, add Heroku Postgres add-on
6. Add Heroku Scheduler add-on, then add recurring task to update leaderboard every 10 minutes:

    ```bash
    python manage.py update_leaderboard --time_aware
    ```
   
7. Optional: Import old database:
   - Clone the repo
   - Create a private_settings.py under `vozRunningClub` folder
   - Copy contents from `settings.py` to `private_settings.py`
   - Change the SQLite database configs to the Heroku Postgres database configs
   - Run:
    
       ```bash
       DJANGO_SETTINGS_MODULE=vozRunningClub.private_settings python manage.py loaddata --format=json -i -e contenttypes db_from_server_16-09-23.json 
       ```
8. Add domain names: `www.vozrun.club` and `vozrun.club`. Enable SSL. Go to Cloudflare and add DNS records.


## Local Development

Local development uses SQLite as the database.

1. Clone the repo
2. Create a virtual Python environment (python-3.10+)
3. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```

4. Install `chromedriver` (https://chromedriver.chromium.org/) - needed for Selenium
5. First time running the app, run the release tasks:

    ```bash
    bash release-tasks.sh
    ```

6. Set the following environment variables:

   - `SOCIAL_AUTH_STRAVA_KEY`: Strava Client ID
   - `SOCIAL_AUTH_STRAVA_SECRET`: Strava Client Secret

7. Run the app

    ```bash
    python manage.py runserver
    ```

8. Setup a cron job or something similar to run the following command every 5/10/15 minutes:

    ```bash
    python manage.py update_leaderboard --time_aware
    ```

## TODO

- [x] Local CSS/JS files
- [x] Create Nav Bar, split into Home, About, and Donation
- [x] New domain name (https://www.vozrun.club)
- [x] Automatically fetching data from Strava
- [x] Add Strava OAuth
- [x] Week summary section
- [x] Week summary section - add donation proof
- [x] Build Statistics Page
- [ ] Build Admin Page
