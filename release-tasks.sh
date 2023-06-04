echo "Running release tasks"

echo "Running collectstatic"
python manage.py collectstatic --noinput

echo "Running migrate"
python manage.py migrate

echo "Running add_default_settings"
python manage.py add_default_settings
