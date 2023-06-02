from django.core.management import BaseCommand

from weeklyTracking.utils import handle_leaderboard_update_request


class Command(BaseCommand):
    def handle(self, *args, **options):
        handle_leaderboard_update_request()
        return
