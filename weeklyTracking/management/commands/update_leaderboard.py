from django.core.management import BaseCommand

from weeklyTracking.utils.strava_web_scrape import handle_leaderboard_update_request


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--time_aware",
            action="store_true",
            help="used for concurrent requests"
        )

    def handle(self, *args, **options):
        time_aware = options["time_aware"]
        handle_leaderboard_update_request(time_aware=time_aware)
        return
