import datetime
import json
import logging

from django.shortcuts import render

from weeklyTracking.models import WeeklyProgress, ActualDonation
from weeklyTracking.templatetags.track_custom_utils import week_time_str

logger = logging.getLogger(__name__)


def statistics(request):
    this_year, this_week_num, _ = datetime.date.today().isocalendar()

    week_summaries = {}

    for wp in WeeklyProgress.objects.all():
        key = (wp.year, wp.week_num)

        if key not in week_summaries:
            time = week_time_str(year=wp.year, week_num=wp.week_num)

            week_summaries[key] = {
                "year": wp.year,
                "week_num": wp.week_num,
                "time": time,
                "runners": 0,
                "runs": 0,
                "distance": 0,
                "registrations": 0,
                "completed": 0,
                "donation": 0,
            }

        if wp.distance > 0 or wp.registered_mileage.distance > 0:
            week_summaries[key]["runners"] += 1
        week_summaries[key]["runs"] += wp.runs
        week_summaries[key]["distance"] += wp.distance
        if wp.registered_mileage.distance > 0:
            week_summaries[key]["registrations"] += 1
            if wp.distance >= wp.registered_mileage.distance:
                week_summaries[key]["completed"] += 1
        week_summaries[key]["donation"] += wp.donation

    for _, ws in week_summaries.items():
        try:
            ws["actual_donation"] = ActualDonation.objects.get(year=ws["year"], week_num=ws["week_num"]).amount
        except ActualDonation.DoesNotExist:
            ws["actual_donation"] = 0
        ws["donation_diff"] = ws["actual_donation"] - ws["donation"]
        if ws["year"] == this_year and ws["week_num"] == this_week_num:
            ws["donation_diff"] = 0

    all_time = {
        "runs": sum([ws["runs"] for _, ws in week_summaries.items()]),
        "distance": sum([ws["distance"] for _, ws in week_summaries.items()]),
        "actual_donation": sum([ws["actual_donation"] for _, ws in week_summaries.items()]),
    }

    sorted_week_summaries = sorted(week_summaries.values(), key=lambda x: (x["year"], x["week_num"]), reverse=True)

    context = {
        "all_time": all_time,
        "week_summaries": sorted_week_summaries,
        "week_summaries_json": json.dumps([w for w in reversed(sorted_week_summaries)]),
    }

    return render(request, "weeklyTracking/statistics.html", context=context)
