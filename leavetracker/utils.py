import pytz
from datetime import datetime, timedelta
from utilities.utils import get_current_date_in_user_timezone


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


def get_server_time():
    return datetime.now()


def get_server_time_in_string():
    utc_datetime = get_server_time()
    return utc_datetime.strftime('%Y-%m-%d %H:%M:%S')


def get_header_footer(canvas, doc, project_name=''):
    canvas.saveState()
    # header
    x1, y1 = 20, 765
    x2, y2 = 600, 765
    canvas.line(x1, y1, x2, y2)
    header_text = "Track it"
    canvas.setFont('Helvetica', 12)
    canvas.drawString(20, 770, project_name)
    canvas.drawString(550, 770, header_text)
    canvas.setStrokeColorRGB(0, 0, 0)  # black
    canvas.setLineWidth(1)
    # footer
    # Draw a line from (x1, y1) to (x2, y2)
    x1, y1 = 20, 35
    x2, y2 = 600, 35
    canvas.line(x1, y1, x2, y2)
    footer_text = f'Report generated on {get_server_time_in_string()}'
    canvas.setFont('Helvetica', 10)
    canvas.drawString(400, 20, footer_text)
    canvas.restoreState()


def get_leave_period_type_label(query_params):
    type = query_params.get('type')
    if type is not None:
        if type == 'date':
            start_date = datetime.strptime(
                query_params.get("start-date"), '%d-%m-%Y')
            end_date = datetime.strptime(
                query_params.get("end-date"), '%d-%m-%Y')
            return f'''{start_date.strftime("%d %b %y")} to {end_date.strftime("%d %b %y")}'''
        if type == 'month':
            return f'''{query_params.get("month")}, {query_params.get("year")}'''
        if type == 'year':
            return f'''{query_params.get("year")}'''


class FiscalYearInfo:
    def __init__(self, month):
        self.month = month
        self.month_int = datetime.strptime(month, '%b').strftime("%m")

    def get_fy_period(self, fiscal_year):
        period = {}
        start_year = fiscal_year
        if int(self.month_int) > 6:
            start_year = fiscal_year-1
        end_year = start_year+1
        period['start_dt'] = datetime.strptime(
            f"{start_year}-{self.month_int}", '%Y-%m').date()
        period['end_dt'] = datetime.strptime(
            f"{end_year}-{self.month_int}", '%Y-%m').date()-timedelta(days=1)
        return period

    def __get_fy_year(self, date):
        year = date.year
        month = date.strftime("%m")
        period = {}
        fiscal_year = year
        if month > self.month_int and int(self.month_int) > 6:
            fiscal_year = year+1
        if month < self.month_int and int(self.month_int) <= 6:
            fiscal_year = year-1
        period['fiscal_year'] = fiscal_year
        period['range'] = self.get_fy_period(fiscal_year)
        return period

    def get_fy_list(self, start_dt, end_dt):
        start_year = self.__get_fy_year(start_dt)
        end_year = self.__get_fy_year(end_dt)
        fy_list = []
        if start_year['fiscal_year'] == end_year['fiscal_year']:
            return [end_year['fiscal_year']]
        for x in range(start_year['fiscal_year'], end_year['fiscal_year']+1):
            fy_list.append(x)
        return fy_list

    def get_current_fiscal_year(self, timezone):
        current_dt = get_current_date_in_user_timezone(timezone)
        return self.__get_fy_year(current_dt)

    def get_fiscal_year(self, date):
        return self.__get_fy_year(date)
