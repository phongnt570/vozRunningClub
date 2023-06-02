# Voz Running Club - Web App for Tracking Weekly Progress with Registered Distances

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
5. Migrate the database

```bash
python manage.py migrate
```

6. First time running the app, run the command to add default settings

```bash
python manage.py add_default_settings
```

7. Run the app

```bash
python manage.py runserver
```

## TODO

- [x] Local CSS/JS files
- [x] Create Nav Bar, split into Home, About, and Donation
- [x] New domain name (vozrun.club)
- [x] Automatically fetching data from Strava
- [ ] Build Donation Page
- [ ] Build Admin Page
- [ ] Week summary section
