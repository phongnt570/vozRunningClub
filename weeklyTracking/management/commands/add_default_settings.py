from django.core.management import BaseCommand

from weeklyTracking.models import SettingDefaultDonation, SettingClubDescription, SettingStravaClub, \
    SettingDefaultWeekBaseDonation, SettingRegisteredMileage, SettingStravaAPIClient


class Command(BaseCommand):
    def handle(self, *args, **options):
        # set SettingDefaultDonation to 100,000
        if not SettingDefaultDonation.objects.filter().exists():
            SettingDefaultDonation.objects.create(default_donation=100000)

        # set SettingClubDescription to "This is the default club description"
        if not SettingClubDescription.objects.filter().exists():
            SettingClubDescription.objects.create(club_description="This is the default club description")

        # set StravaClub to "https://www.strava.com/clubs/1140105"
        if not SettingStravaClub.objects.filter().exists():
            SettingStravaClub.objects.create(club_url="https://www.strava.com/clubs/1140105")

        # set SettingDefaultWeekBaseDonation 0km - 0đ, 30km - 1,000đ, 50km - 5,000đ, 70km - 10,000đ, 100km - 20,000đ
        if not SettingDefaultWeekBaseDonation.objects.filter().exists():
            SettingDefaultWeekBaseDonation.objects.create(distance=0, base_donation=0)
            SettingDefaultWeekBaseDonation.objects.create(distance=30, base_donation=1000)
            SettingDefaultWeekBaseDonation.objects.create(distance=50, base_donation=5000)
            SettingDefaultWeekBaseDonation.objects.create(distance=70, base_donation=10000)
            SettingDefaultWeekBaseDonation.objects.create(distance=100, base_donation=20000)

        # add SettingRegisteredMileage 0, 30, 50, 70, 100
        if not SettingRegisteredMileage.objects.filter().exists():
            SettingRegisteredMileage.objects.create(distance=0)
            SettingRegisteredMileage.objects.create(distance=30)
            SettingRegisteredMileage.objects.create(distance=50)
            SettingRegisteredMileage.objects.create(distance=70)
            SettingRegisteredMileage.objects.create(distance=100)

        # SettingStravaAPIClient
        if not SettingStravaAPIClient.objects.filter().exists():
            SettingStravaAPIClient.objects.create(
                client_id="108204",
                client_secret="a603ad31780bd0e3ceee0edeefec3c7122bc2156",
            )
