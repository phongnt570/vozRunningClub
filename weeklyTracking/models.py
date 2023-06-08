from django.contrib.auth.models import User
from django.db import models

from .singleton_model import SingletonModel


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, related_name="profile")

    strava_club_joined = models.BooleanField(default=False)

    voz_name = models.CharField(max_length=64, blank=True, default="")

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} | voz_name: {self.voz_name}"


class SettingWeekBaseDonation(models.Model):
    year = models.IntegerField()
    week_num = models.IntegerField()
    distance = models.IntegerField()
    base_donation = models.IntegerField()

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["distance", "year", "week_num"]
        indexes = [
            models.Index(fields=["year", "week_num"]),
            models.Index(fields=["distance", "year", "week_num"]),
        ]

    def __str__(self):
        return f"{self.year} | {self.week_num} | {self.distance} km | {self.base_donation:,} ₫"


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
        return f"{self.distance} km"


class WeeklyProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_progress")

    year = models.IntegerField()
    week_num = models.IntegerField()

    registered_mileage = models.ForeignKey(SettingRegisteredMileage, on_delete=models.CASCADE)

    distance = models.FloatField(default=0.0)
    runs = models.IntegerField(default=0)
    longest_run = models.FloatField(default=0.0)
    average_pace = models.FloatField(default=0.0)
    elevation_gain = models.FloatField(default=0.0)

    note = models.TextField(blank=True, default="")

    donation = models.IntegerField(default=0)
    actual_donation = models.IntegerField(default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "year", "week_num"]
        indexes = [
            models.Index(fields=["year", "week_num"]),
            models.Index(fields=["user", "year", "week_num"]),
            models.Index(fields=["year", "week_num", "distance"]),
            models.Index(fields=["year", "week_num", "donation"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.year} | {self.week_num} | {self.registered_mileage.distance} km"


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
        indexes = [
            models.Index(fields=["year", "week_num"]),
        ]

    def __str__(self):
        return f"{self.year} | {self.week_num} | {self.default_donation:,} ₫"


class SettingClubDescription(SingletonModel):
    club_description = models.TextField()

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.club_description
