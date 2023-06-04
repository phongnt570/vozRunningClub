from django.db import models

from .singleton_model import SingletonModel


class StravaRunner(models.Model):
    strava_id = models.IntegerField(primary_key=True)
    strava_name = models.CharField(max_length=64)
    strava_refresh_token = models.CharField(max_length=64, null=True, blank=True)
    voz_name = models.CharField(max_length=64)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.strava_id} | {self.strava_name} | {self.strava_refresh_token} | {self.voz_name}"


class SettingWeekBaseDonation(models.Model):
    year = models.IntegerField()
    week_num = models.IntegerField()
    distance = models.IntegerField()
    base_donation = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["distance", "year", "week_num"]

    def __str__(self):
        return f"{self.year} | {self.week_num} | {self.distance}km | {self.base_donation:,} ₫"


class SettingDefaultWeekBaseDonation(models.Model):
    distance = models.IntegerField(primary_key=True)
    base_donation = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distance}km | {self.base_donation:,} ₫"


class SettingRegisteredMileage(models.Model):
    distance = models.IntegerField(primary_key=True)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distance}km"


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


class SettingDefaultDonationByWeek(models.Model):
    year = models.IntegerField()
    week_num = models.IntegerField()
    default_donation = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["year", "week_num"]

    def __str__(self):
        return f"{self.year} | {self.week_num} | {self.default_donation:,} ₫"


class SettingClubDescription(SingletonModel):
    club_description = models.TextField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.club_description


class SettingStravaAPIClient(SingletonModel):
    client_id = models.CharField(max_length=512)
    client_secret = models.CharField(max_length=512)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_id} | {self.client_secret}"
