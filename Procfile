release: python manage.py migrate
release: python manage.py add_default_settings
release: python manage.py collectstatic --noinput
web: gunicorn vozRunningClub.wsgi