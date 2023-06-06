from weeklyTracking.models import WeeklyProgress


def get_available_weeks_in_db():
    available_weeks = set()
    for week_progress in WeeklyProgress.objects.all():
        available_weeks.add((week_progress.year, week_progress.week_num))
    return available_weeks
