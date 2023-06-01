import math

from django import template

from weeklyTracking.models import WeeklyProgress, SettingDefaultDonation

register = template.Library()


def missing_distance(week_progress: WeeklyProgress):
    return max(0.0, week_progress.registered_mileage.distance - week_progress.distance)


@register.filter
def missing_distance_str(week_progress: WeeklyProgress):
    d = max(0.0, week_progress.registered_mileage.distance - week_progress.distance)
    if week_progress.registered_mileage.distance == 0:
        return "--"

    if d == 0:
        return "Completed!"
    
    return f"{d:.1f} km"


@register.filter
def pace_format(seconds: int):
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


@register.filter
def donation(week_progress: WeeklyProgress):
    reg_dis = int(week_progress.registered_mileage.distance)
    donation_per_km = week_progress.registered_mileage.donation_per_km

    if reg_dis == 0:
        return "--"

    if reg_dis > 0 and week_progress.distance == 0:
        amount = SettingDefaultDonation.objects.get().default_donation
    else:
        amount = donation_per_km * missing_distance(week_progress)

    return f"{math.ceil(amount):,} ₫"
