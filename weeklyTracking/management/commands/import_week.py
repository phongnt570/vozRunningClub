import csv

from django.core.management.base import BaseCommand

from weeklyTracking.models import StravaRunner, WeeklyProgress, SettingRegisteredMileage


class Command(BaseCommand):
    help = "Import Weekly Registration to DB"

    def add_arguments(self, parser):
        parser.add_argument("infile", type=str)

    def handle(self, *args, **options):
        infile = options["infile"]

        self.stdout.write(f"Reading \"{infile}\"")
        with open(infile, "r") as f:
            reader = csv.DictReader(f)
            input_rows = [row for row in reader]
        self.stdout.write(self.style.SUCCESS(f"Read {len(input_rows)} rows"))

        new_runners = []
        for row in input_rows:
            strava_id = int(row["strava_id"])
            strava_name = row["strava_name"]
            voz_name = row["voz_name"]

            if not StravaRunner.objects.filter(strava_id=strava_id).exists():
                new_runners.append(StravaRunner(strava_id=strava_id, strava_name=strava_name, voz_name=voz_name))
            else:
                runner = StravaRunner.objects.get(strava_id=strava_id)
                if strava_name:
                    runner.strava_name = strava_name
                if voz_name:
                    runner.voz_name = voz_name
                runner.save()

        if new_runners:
            self.stdout.write(f"Adding {len(new_runners)} new runners")
            StravaRunner.objects.bulk_create(new_runners)
            self.stdout.write(self.style.SUCCESS("Done adding new runners"))

        registered_mileages = {}
        for mileage in SettingRegisteredMileage.objects.all():
            registered_mileages[mileage.distance] = mileage

        self.stdout.write("Updating weekly progress")
        for row in input_rows:
            strava_id = int(row["strava_id"])
            week_num = int(row["week_num"])
            year = int(row["year"])
            registered_mileage = registered_mileages[int(row["registered_distance"])]

            runner = StravaRunner.objects.get(strava_id=strava_id)
            WeeklyProgress.objects.update_or_create(
                runner=runner,
                week_num=week_num,
                year=year,
                registered_mileage=registered_mileage,
            )
        self.stdout.write(self.style.SUCCESS("Done!!!"))
