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
./release-tasks.sh
```

6. Run the app

```bash
python manage.py runserver
```

## TODO

- [x] Local CSS/JS files
- [x] Create Nav Bar, split into Home, About, and Donation
- [x] New domain name (https://www.vozrun.club)
- [x] Automatically fetching data from Strava
- [x] Add Strava OAuth
- [ ] Build Top-donates Page
- [ ] Build Admin Page
- [ ] Week summary section
