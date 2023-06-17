import datetime

from django.core.management import BaseCommand

from weeklyTracking.models import WeeklyProgress


class Command(BaseCommand):
    def handle(self, *args, **options):
        today = datetime.date.today()
        # only copy data from the previous week when the today is Saturday
        if today.weekday() != 5:
            self.stdout.write("Today is not Sunday, finish here.")
            return

        # get the current week
        this_year, this_week_num, _ = today.isocalendar()
        current_wps = WeeklyProgress.objects.filter(year=this_year, week_num=this_week_num)

        # get the new week
        new_week_year, new_week_num, _ = (today + datetime.timedelta(days=7)).isocalendar()
        new_wps = []
        for wp in current_wps:
            new_wps.append(
                WeeklyProgress(
                    user=wp.user,
                    year=new_week_year,
                    week_num=new_week_num,
                    registered_mileage=wp.registered_mileage,
                )
            )

        # bulk create
        self.stdout.write(f"Copying {len(new_wps)} WeeklyProgress objects to the new week...")
        WeeklyProgress.objects.bulk_create(new_wps, ignore_conflicts=True)
        self.stdout.write("Done.")
