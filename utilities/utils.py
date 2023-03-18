from datetime import datetime, timedelta
import pytz


def get_current_date_in_user_timezone(user_timezone=None):
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    if user_timezone is not None:
        user_timezone_obj = pytz.timezone(user_timezone)
        current_datetime_in_timezone = current_datetime.astimezone(
            user_timezone_obj)
        current_date = current_datetime_in_timezone.date()
    return current_date


def get_date_in_user_timezone(date, user_timezone):
    return date.astimezone(pytz.timezone(user_timezone))


def get_least_utc_current_date():
    current_utc_time = datetime.utcnow().time()
    current_utc_date = datetime.utcnow().date()
    if current_utc_time.hour < 11:
        return current_utc_date-timedelta(days=1)
    else:
        return current_utc_date


def get_highest_utc_current_date():
    current_utc_time = datetime.utcnow().time()
    current_utc_date = datetime.utcnow().date()
    if current_utc_time.hour > 11:
        return current_utc_date+timedelta(days=1)
    else:
        return current_utc_date
