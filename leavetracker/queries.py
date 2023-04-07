from .models import LTAccountPreference, Announcement, Employee, FiscalYear, Team, LeaveRequest, TeamMember, LatestLeaveRequestNumber, LeaveDate, LeaveApproval,  SubscribeTeam
from django.db.models import Prefetch
from django.db.models import Exists, OuterRef
from django.db.models import Value, Count
from django.http import Http404
from django.db.models.aggregates import Max
from datetime import datetime
import calendar


def get_fiscal_month(project):
    fiscal_year, created = FiscalYear.objects.get_or_create(
        project=project, defaults={'month': calendar.month_abbr[1]})
    return fiscal_year.month


def get_employee(user):
    preference = LTAccountPreference.objects.select_related(
        'project').get(user=user)
    return Employee.objects.select_related('project').select_related('user').get(
        user=user, project=preference.project, project__status='A', status='A')


def get_absentees_from_my_team(team_id, date):
    queryset = LeaveRequest.objects.filter(
        employee__teams__team=team_id, leave_dates__date=date, status='A')
    return queryset


def get_absentees_from_subscribed_groups(employee, date):
    queryset = LeaveRequest.objects.select_related('employee__user').select_related('employee__teams__team')\
        .filter(employee__teams__team__subscribed_teams__employee=employee)\
        .filter(leave_dates__date=date, status='A')
    return queryset


def get_leaves(employee, leave_id=None):
    queryset = LeaveRequest.objects.prefetch_related('leave_dates').select_related('type')\
        .select_related('duration').filter(employee=employee)
    if leave_id is not None:
        try:
            queryset.get(id=leave_id)
        except:
            raise Http404("leave not found")
    return queryset


def get_latest_leave_request_no(project):
    base_req_no = 1000
    existing_req_no = base_req_no
    existing_req_details = LeaveRequest.objects.filter(
        employee__project=project).aggregate(max_req_no=Max('request_number'))
    if existing_req_details.get("max_req_no"):
        existing_req_no = existing_req_details.get("max_req_no")
    latest_req_no, created = LatestLeaveRequestNumber.objects.get_or_create(
        project=project, defaults={'request_id': existing_req_no})
    return latest_req_no.request_id


def filter_leave_dates_by_type(base_query, query_params):
    type = query_params.get('type')
    if type is not None:
        if type == 'year':
            year = query_params.get('year')
            if year is not None:
                return base_query.filter(
                    employee__leave_request__leave_dates__date__year=year,
                    employee__leave_request__status='A'
                )
        if type == 'month':
            year = query_params.get('year')
            month = query_params.get('month')
            if year is not None and month is not None:
                return base_query.filter(
                    employee__leave_request__leave_dates__date__year=year,
                    employee__leave_request__leave_dates__date__month=month,
                    employee__leave_request__status='A')
        if type == 'date':
            start_date = query_params.get('start-date')
            end_date = query_params.get('end-date')
            if start_date is not None and end_date is not None:
                start_date = datetime.strptime(start_date, '%d-%m-%Y')
                end_date = datetime.strptime(end_date, '%d-%m-%Y')
                return base_query.filter(
                    employee__leave_request__leave_dates__date__gte=start_date,
                    employee__leave_request__leave_dates__date__lte=end_date,
                    employee__leave_request__status='A')
    return base_query.none()


def get_leave_count(query):
    return query.annotate(
        leave_count=Count('employee__leave_request__leave_dates')).order_by('-leave_count')[:5]


def get_approvals(employee, approval_id=None):
    queryset = LeaveApproval.objects.select_related("request_number")\
        .prefetch_related("request_number__leave_dates").select_related("request_number__employee__user")\
        .select_related("request_number__type").select_related("request_number__duration")\
        .select_related('approver__user').filter(approver=employee)

    if approval_id is not None:
        try:
            queryset.get(id=approval_id)
        except:
            raise Http404("approval not found")
    return queryset


def get_my_teams(employee, team_id=None):
    queryset = Team.objects.filter(team_members__employee=employee)
    if team_id is not None:
        try:
            return queryset.get(id=team_id)
        except:
            raise Http404("Team not found")
    return queryset


def get_all_teams(employee, team_id=None):
    queryset = Team.objects.prefetch_related(Prefetch('team_members',
                                                      queryset=TeamMember.objects.select_related("employee", "employee__user")))\
        .filter(project=employee.project)\
        .exclude(team_members__employee=employee).annotate(member_count=Count('team_members'))\
        .annotate(subscribed=Exists(SubscribeTeam.objects.filter(team=OuterRef('id'), employee=employee)))\
        .annotate(enable_subscription=Value(True))
    if team_id is not None:
        try:
            return queryset.get(id=team_id)
        except:
            raise Http404("Team not found")
    return queryset


def get_subscribed_teams(employee):
    queryset = Team.objects.filter(
        subscribed_teams__employee=employee)
    return queryset


def get_team_members(team_id, employee):
    return TeamMember.objects.select_related('employee__user').filter(team=team_id, team__project=employee.project)


def get_is_user_team_admin(team_id, employee):
    if team_id is not None:
        return TeamMember.objects.filter(
            team__id=team_id, employee=employee, role='A').first()
    return None
