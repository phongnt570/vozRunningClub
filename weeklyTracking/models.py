from django.db import models

from .singleton_model import SingletonModel


class StravaRunner(models.Model):
    strava_id = models.IntegerField(primary_key=True)
    strava_name = models.CharField(max_length=64)
    voz_name = models.CharField(max_length=64)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.strava_id} | {self.strava_name} | {self.voz_name}"


class SettingRegisteredMileage(models.Model):
    distance = models.IntegerField(primary_key=True)
    donation_per_km = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distance}km: {self.donation_per_km}đ/km"


class WeeklyProgress(models.Model):
    runner = models.ForeignKey(StravaRunner, on_delete=models.CASCADE)

    year = models.IntegerField()
    week_num = models.IntegerField()

    registered_mileage = models.ForeignKey(SettingRegisteredMileage, on_delete=models.CASCADE)

    distance = models.FloatField(default=0.0)
    runs = models.IntegerField(default=0)
    longest_run = models.FloatField(default=0.0)
    average_pace = models.FloatField(default=0.0)
    elevation_gain = models.FloatField(default=0.0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["runner", "year", "week_num"]

    def __str__(self):
        return f"{self.runner} | {self.year} | {self.week_num} | {self.registered_mileage.distance} km"


class SettingStravaClub(SingletonModel):
    club_url = models.CharField(max_length=1024)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.club_url


class SettingDefaultDonation(SingletonModel):
    default_donation = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.default_donation:,} ₫"


class SettingClubDescription(SingletonModel):
    club_description = models.TextField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.club_description
