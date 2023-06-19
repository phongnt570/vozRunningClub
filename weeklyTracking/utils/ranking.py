from typing import Dict, List

from django.db.models import Q

from weeklyTracking.models import WeeklyProgress
from weeklyTracking.utils.time import get_last_week_year_and_week_num


def get_ranked_users(year: int, week_num: int, reg_distance: float = None) -> List[WeeklyProgress]:
    if reg_distance is None:
        return WeeklyProgress.objects.filter(Q(year=year) & Q(week_num=week_num) & (
                Q(distance__gt=0) | Q(registered_mileage__distance__gt=0))).order_by("-distance",
                                                                                     "-registered_mileage__distance",
                                                                                     "user__first_name")
    else:
        return WeeklyProgress.objects.filter(Q(year=year) & Q(week_num=week_num) & (
                Q(distance__gt=0) | Q(registered_mileage__distance__gt=0)) & Q(
            registered_mileage__distance=reg_distance)).order_by("-distance",
                                                                 "-registered_mileage__distance",
                                                                 "user__first_name")


def user_rank_change(year: int, week_num: int, reg_distance: float = None) -> Dict[int, int]:
    cur_week_progresses = get_ranked_users(year=year, week_num=week_num, reg_distance=reg_distance)

    last_week_year, last_week_num = get_last_week_year_and_week_num(year=year, week_num=week_num)
    last_week_progresses = get_ranked_users(year=last_week_year, week_num=last_week_num, reg_distance=reg_distance)

    cur_week_progresses_dict = {progress.user.id: i for i, progress in enumerate(cur_week_progresses)}
    last_week_progresses_dict = {progress.user.id: i for i, progress in enumerate(last_week_progresses)}

    res = {}
    for user_id in cur_week_progresses_dict:
        if user_id in last_week_progresses_dict:
            res[user_id] = last_week_progresses_dict[user_id] - cur_week_progresses_dict[user_id]

    return res
