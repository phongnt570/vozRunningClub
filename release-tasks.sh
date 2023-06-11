echo "Running release tasks"

echo "Running collectstatic"
python manage.py collectstatic --noinput

echo "Running migrate"
python manage.py migrate

echo "Running add_default_settings"
python manage.py add_default_settings

echo "Running update_leaderboard"
python manage.py update_leaderboard --time_aware

echo "Done running release tasks"
