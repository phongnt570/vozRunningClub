release: python manage.py collectstatic --noinput
release: python manage.py migrate
release: python manage.py add_default_settings
web: gunicorn vozRunningClub.wsgi