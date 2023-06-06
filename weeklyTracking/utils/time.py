import datetime


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

    next_week = (datetime.date.today() + datetime.timedelta(days=7)).isocalendar()
    next_week_monday = datetime.datetime.fromisocalendar(next_week[0], next_week[1], 1)

    if requested_first_weekday > next_week_monday:
        print(requested_first_weekday, next_week_monday)
        return False

    return True


def get_last_week_year_and_week_num():
    ic_last_week = (datetime.date.today() + datetime.timedelta(days=-7)).isocalendar()
    return ic_last_week[0], ic_last_week[1]
