from .models import Employee, LTAccountPreference, LatestLeaveRequestNumber, LeaveRequest, LeaveApproval, FiscalYear, Team, SubscribeTeam, TeamMember
from django.db.models import Prefetch
from django.db.models import Exists, OuterRef
from django.db.models import Value, Count
from django.http import Http404
from django.db.models.aggregates import Max
import calendar


def get_my_teams(employee, team_id=None):
    queryset = Team.objects.filter(team_members__employee=employee)
    if team_id is not None:
        try:
            queryset.get(id=team_id)
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
            queryset.get(id=team_id)
        except:
            raise Http404("Team not found")
    return queryset


def get_employee(request):
    user = request.user
    preference = LTAccountPreference.objects.get(user=user)
    return Employee.objects.get(
        user=user, project=preference.project, status='A')


def get_fiscal_month(project):
    fiscal_year, created = FiscalYear.objects.get_or_create(
        project=project, defaults={'month': calendar.month_abbr[1]})
    return fiscal_year.month


def get_leaves(employee, leave_id=None):
    queryset = LeaveRequest.objects.prefetch_related('leave_dates').select_related('type')\
        .select_related('duration').filter(employee=employee)
    if leave_id is not None:
        try:
            queryset.get(id=leave_id)
        except:
            raise Http404("leave not found")
    return queryset


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


def get_is_user_team_admin(team_id, employee):
    if team_id is not None:
        print(team_id, employee)
        return TeamMember.objects.filter(
            team__id=team_id, employee=employee, role='A').first()
    return None


def get_latest_leave_request_no(project):
    base_req_no = 1000
    existing_req_no = base_req_no
    existing_req_details = LeaveRequest.objects.filter(
        employee__project=project).aggregate(max_req_no=Max('request_number'))
    print(existing_req_details)
    if existing_req_details.get("max_req_no"):
        existing_req_no = existing_req_details.get("max_req_no")
    latest_req_no, created = LatestLeaveRequestNumber.objects.get_or_create(
        project=project, defaults={'request_id': existing_req_no})
    return latest_req_no.request_id
