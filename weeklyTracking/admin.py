from django.contrib import admin

from weeklyTracking.models import StravaRunner, WeeklyProgress, SettingStravaClub, SettingRegisteredMileage, \
    SettingDefaultDonation, SettingClubDescription

admin.site.register(StravaRunner)
admin.site.register(WeeklyProgress)
admin.site.register(SettingStravaClub)
admin.site.register(SettingRegisteredMileage)
admin.site.register(SettingDefaultDonation)
admin.site.register(SettingClubDescription)
