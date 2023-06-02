import datetime
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import UploadFileForm
from .models import WeeklyProgress, SettingClubDescription
from .utils import handle_uploaded_week_reg_file, \
    handle_leaderboard_update_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_year_week(requested_year, requested_week_num):
    try:
        requested_year = int(requested_year)
        requested_week_num = int(requested_week_num)
    except (ValueError, TypeError):
        return False

    try:
        requested_first_weekday = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    except ValueError:
        return False

    if requested_first_weekday > datetime.datetime.now():
        return False

    return True


def get_available_weeks():
    available_weeks = set()
    for week_progress in WeeklyProgress.objects.all():
        available_weeks.add((week_progress.year, week_progress.week_num))
    return available_weeks


def leaderboard(request):
    requested_year = request.GET.get("year")
    requested_week_num = request.GET.get("week")

    this_year = datetime.date.today().isocalendar()[0]
    this_week_num = datetime.date.today().isocalendar()[1]

    if not validate_year_week(requested_year, requested_week_num):
        requested_year = this_year
        requested_week_num = this_week_num
    else:
        requested_year = int(requested_year)
        requested_week_num = int(requested_week_num)

    requested_week_data = WeeklyProgress.objects.filter(week_num=requested_week_num,
                                                        year=requested_year).order_by("-distance",
                                                                                      "-registered_mileage__distance",
                                                                                      "runner__strava_name")

    requested_week_start = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 1)
    requested_week_end = datetime.datetime.fromisocalendar(requested_year, requested_week_num, 7)

    this_week_start = datetime.datetime.fromisocalendar(this_year, this_week_num, 1)

    reg_map = {}
    for week_progress in requested_week_data:
        reg_dis = week_progress.registered_mileage.distance
        if reg_dis not in reg_map:
            reg_map[reg_dis] = []
        reg_map[reg_dis].append(week_progress)

    sorted_reg_map = {}
    for key in sorted(reg_map.keys(), reverse=True):
        sorted_reg_map[key] = reg_map[key]

    last_updated = None
    if WeeklyProgress.objects.filter(week_num=requested_week_num, year=requested_year).exists():
        last_updated = WeeklyProgress.objects.filter(week_num=requested_week_num, year=requested_year).order_by(
            "-last_updated").first().last_updated

    available_weeks = {}
    for year, week_num in sorted(get_available_weeks(), reverse=True):
        if year == this_year and week_num == this_week_num:
            value = "This week"
        else:
            start_date = datetime.datetime.fromisocalendar(year, week_num, 1)
            end_date = datetime.datetime.fromisocalendar(year, week_num, 7)
            if end_date == this_week_start + datetime.timedelta(days=-1):
                value = "Last week"
            else:
                value = f"Week {week_num} ({start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')})"

        available_weeks[(year, week_num)] = value

    context = {
        "requested_year": requested_year,
        "requested_week_num": requested_week_num,
        "requested_week_data": requested_week_data,
        "requested_week_start": requested_week_start,
        "requested_week_end": requested_week_end,
        "reg_map": sorted_reg_map,
        "is_this_week": requested_week_start == this_week_start,
        "is_last_week": requested_week_end == this_week_start + datetime.timedelta(days=-1),
        "available_weeks": available_weeks,
        "last_updated": last_updated,
    }

    return render(request, "weeklyTracking/leaderboard.html", context=context)


@staff_member_required
@require_POST
def update(request):
    try:
        handle_leaderboard_update_request()
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "success"})


@staff_member_required
def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_week_reg_file(request.FILES["file"])
            return redirect("index")
    else:
        form = UploadFileForm()

    return render(request, "weeklyTracking/upload.html", {"form": form})


def about(request):
    return render(request, "weeklyTracking/about.html", context={
        "club_description": SettingClubDescription.objects.get().club_description})


def top_donates(request):
    return render(request, "weeklyTracking/top_donates.html")
