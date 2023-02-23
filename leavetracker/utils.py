import pytz
from datetime import datetime


def calculate_overall_approval_status(status_list):
    unique_list = set(status_list)
    print(unique_list, status_list)
    if "C" in unique_list:
        return "C"
    if "R" in unique_list:
        return "R"
    if "P" in unique_list:
        return "P"
    if "A" in unique_list:
        return "A"


def data_group_by(data, splitByKey, groupByKey, newKey):
    group_by = {}
    for item in data:
        splitByKeyString = str(item[splitByKey])
        if splitByKeyString not in group_by:
            group_by[splitByKeyString] = item
            group_by[splitByKeyString][newKey] = []
        group_by[splitByKeyString][newKey].append(item[groupByKey])
    return group_by


def get_current_date(user_timezone=None):
    current_date = datetime.now().date()
    if user_timezone is not None:
        employee_timezone = pytz.timezone(user_timezone)
        current_date_in_timezone = datetime.now(employee_timezone)
        current_date = current_date_in_timezone.date()
    return current_date


def get_present_datetime_in_user_timezone(timezone):
    if timezone is not None:
        return datetime.now(pytz.timezone(timezone))
    else:
        return datetime.now()
