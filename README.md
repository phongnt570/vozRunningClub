# Voz Running Club - Web App

## About

The web app is developed using Django and Python.
The app is hosted on Heroku and uses Heroku Postgres as the database.

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
