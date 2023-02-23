from datetime import datetime, timedelta
import pytz


class FiscalYear:
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
        current_dt = datetime.now(pytz.timezone(timezone))
        return self.__get_fy_year(current_dt)

    def get_fiscal_year(self, date):
        return self.__get_fy_year(date)
