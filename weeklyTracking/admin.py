from django.contrib import admin

from weeklyTracking.models import WeeklyProgress, SettingStravaClub, SettingRegisteredMileage, \
    SettingDefaultDonation, SettingClubDescription, SettingWeekBaseDonation, SettingDefaultWeekBaseDonation, \
    SettingDefaultDonationByWeek, UserProfile, WeeklyPost, ActualDonation

admin.site.register(WeeklyProgress)
admin.site.register(SettingStravaClub)
admin.site.register(SettingRegisteredMileage)
admin.site.register(SettingDefaultDonation)
admin.site.register(SettingClubDescription)
admin.site.register(SettingWeekBaseDonation)
admin.site.register(SettingDefaultWeekBaseDonation)
admin.site.register(SettingDefaultDonationByWeek)
admin.site.register(UserProfile)
admin.site.register(WeeklyPost)
admin.site.register(ActualDonation)
