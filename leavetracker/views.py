from .utils import get_header_footer, get_leave_period_type_label, data_group_by, FiscalYearInfo
from .constants import basic_table_style, style_title, style_body, style_not_found_text, leave_request_columns, leave_count_columns, absentees_columns, absentees_excel_columns
from .validations import validate_my_groups_report_section_id
from .queries import get_employee, get_fiscal_month, get_my_teams, get_absentees_from_my_team, get_team_members, get_subscribed_teams, filter_leave_dates_by_type, get_leave_count, get_absentees_from_subscribed_groups, get_all_teams, get_leaves, get_approvals, get_is_user_team_admin
from .permissions import IsEmployee
from .models import Announcement, AnnouncementViewedEmployee, Domain, Employee, Approver, FiscalYear, LeaveApproval, LeaveDate, LeaveDuration, LeaveType, Role, SubscribeTeam, Team, TeamMember, LTAccountPreference
from .serializers import SimpleAnnouncementSerializer, AnnouncementSerializer, CreateAnnouncementSerializer, AbsenteesDetailSerializer, ApprovalInfoSerializer, ApproverSerializer, CreateLeaveRequestSerializer, CreateTeamMemberSerializer, CreateTeamSerializer, EmployeeSerializer, MyEmployeeAccountsSerializer, RetrieveTeamSerializer, GroupsLeaveCountSerializer, LeaveBalanceSerializer, LeaveDatesSerializer, LeaveDurationSerializer, LeaveTypeSerializer, SimpleAllTeamSerializer, SimpleDomainSerializer, SimpleEmployeeSerializer, SimpleLeaveRequestSerializer, LeaveRequestSerializer, ListSubscribeTeamSerializer, MyInfoSerializer, CreateApproverSerializer, SimpleRoleSerializer, SimpleTeamSerializer, SimpleUserSerializer, SubscribeEmployeeSerializer, SubscribeSerializer, SubscribeTeamSerializer, TeamAnalysisMembersSerializer, TeamAnalysisSerializer, AbsenteesTeamSerializer,  TeamMemberSerializer, TeamSerializer, ApprovalSerializer, UpdateApprovalSerializer, UpdateTeamMemberSerializer, UpdateTeamSerializer
from project.models import Project
from project.serializers import SimpleProjectSerializer
from utilities.utils import get_current_date_in_user_timezone, get_date_in_user_timezone, get_least_utc_current_date, get_highest_utc_current_date
from utilities.error import CustomApiResponseError
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, IntegerField, Prefetch
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import ListModelMixin, UpdateModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import inch
from datetime import datetime
from openpyxl import Workbook
import logging
import io

logger = logging.getLogger(__name__)


class EmployeeAccountPreference(APIView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request):
        user = self.request.user
        try:
            employee = get_employee(user)
            serializer = SimpleProjectSerializer(employee.project)
            return Response(serializer.data)
        except:
            return Response(status=404, data={'code': 'PREF.NOT.FOUND',
                                              'message': "No user account preference found or Employee acct/Project is inactive"})

    def post(self, request):
        user = self.request.user
        data = self.request.data
        project_id = data.get('project_id')
        if project_id is not None:
            try:
                project = Project.objects.get(id=project_id, status='A')
                Employee.objects.get(
                    user=user, project=project, status='A')
                preference, created = LTAccountPreference.objects.get_or_create(
                    user=user, defaults={'project': project})
                if not created:
                    preference.project = project
                    preference.save()
                return Response(status=200, data={"status": "ok"})
            except:
                return Response(status=400, data={'message': "No active employee account/project found"})
        else:
            return Response(status=400, data={'message': "Please share project id"})


class MyAccountsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = MyEmployeeAccountsSerializer

    def get_queryset(self):
        return Employee.objects.filter(user=self.request.user, status="A").select_related('project')


class EmployeeViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAuthenticated, IsEmployee]
    filter_backends = [SearchFilter]
    search_fields = ['user__email', 'user__username']

    @action(detail=False, methods=['get'])
    def me(self, request):
        current_employee = get_employee(self.request.user)
        employee = Employee.objects.prefetch_related('approvers__approver__user')\
            .select_related('user').select_related('domain').select_related('role')\
            .prefetch_related('role__role_access__access').select_related('project').filter(
            user_id=current_employee.user, project=current_employee.project).first()
        serializer = MyInfoSerializer(employee)
        return Response(serializer.data)

    def get_serializer_class(self):
        return SimpleEmployeeSerializer

    def get_queryset(self):
        logger.info("fetching all employees")
        current_employee = get_employee(self.request.user)
        return Employee.objects.select_related('user')\
            .filter(project=current_employee.project, status='A')\
            .exclude(user=current_employee.user)


class RoleViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    serializer_class = SimpleRoleSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return Role.objects.filter(project=current_employee.project)


class DomainViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    serializer_class = SimpleDomainSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return Domain.objects.filter(project=current_employee.project)


class LeaveTypeViewset(ListModelMixin, GenericViewSet):
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return LeaveType.objects.filter(project=current_employee.project, status="A")


class LeaveDurationViewset(ListModelMixin, GenericViewSet):
    serializer_class = LeaveDurationSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return LeaveDuration.objects.filter(project=current_employee.project, status="A")


class ApproverViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request.user)
        serializer = CreateApproverSerializer(
            data=request.data, many=True, context={'employee': current_employee, "data_length": len(request.data)})
        serializer.is_valid(raise_exception=True)
        new_approver = serializer.save()
        result = ApproverSerializer(new_approver, many=True)
        return Response(result.data)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateApproverSerializer
        return ApproverSerializer

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return Approver.objects.select_related('approver__user').filter(employee=current_employee)


class LeaveRequestViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return get_leaves(current_employee)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLeaveRequestSerializer
        return LeaveRequestSerializer

    def get_serializer_context(self):
        return {"user": self.request.user}

    def list(self, request, *args, **kwargs):
        user = self.request.user
        query_params = request.query_params
        leave_period_param = query_params.get('period')
        current_date = get_current_date_in_user_timezone(
            user.timezone)
        filtered_queryset = self.get_queryset().filter(to_date__gte=current_date)
        if leave_period_param is not None:
            if leave_period_param == 'prev':
                filtered_queryset = self.get_queryset().filter(
                    to_date__lt=current_date)
        serializer = self.get_serializer(filtered_queryset, many=True, context={
                                         "user": self.request.user})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request.user)
        serializer = CreateLeaveRequestSerializer(
            data=request.data, context={"employee": current_employee})
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        serializer = LeaveRequestSerializer(request, context={
            "user": self.request.user})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        current_date = get_current_date_in_user_timezone(user.timezone)
        obj = self.get_object()
        if obj.status != 'P':
            return Response(data={
                "message": "Leave is not in pending status"
            }, status=400)
        if not (obj.from_date > current_date and obj.to_date > current_date):
            return Response(data={
                "message": "Cannot delete request having from date less than current date"
            }, status=400)

        return super().destroy(request, *args, **kwargs)


class LeaveDatesViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        get_leaves(current_employee, self.kwargs['request_pk'])
        return LeaveDate.objects.filter(request_number=self.kwargs['request_pk'])

    def get_serializer_class(self):
        return LeaveDatesSerializer


class ApprovalInfoViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        get_leaves(current_employee, self.kwargs['request_pk'])
        queryset = LeaveApproval.objects.select_related('approver__user').filter(request_number__employee=current_employee)\
            .filter(request_number=self.kwargs['request_pk'])
        return queryset

    def get_serializer_class(self):
        return ApprovalInfoSerializer


class ApprovalViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get',  'patch']

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        return get_approvals(current_employee)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateApprovalSerializer
        return ApprovalSerializer

    def list(self, request, *args, **kwargs):
        query_params = request.query_params
        approval_status = query_params.get('status')
        period = query_params.get('period')
        approval_list = []
        least_utc_date = get_least_utc_current_date()
        highest_utc_date = get_highest_utc_current_date()
        if period == 'prev':
            filtered_queryset = self.get_queryset().filter(
                request_number__from_date__lt=highest_utc_date)
        else:
            filtered_queryset = self.get_queryset().filter(
                request_number__from_date__gte=least_utc_date)
        for approval in filtered_queryset:
            timezone = approval.request_number.employee.user.timezone
            current_date_in_employee_timezone = get_current_date_in_user_timezone(
                timezone)
            if period == 'prev':
                if approval.request_number.from_date < current_date_in_employee_timezone:
                    approval_list.append(approval)
            else:
                if approval.request_number.from_date >= current_date_in_employee_timezone:
                    approval_list.append(approval)
        if approval_status is not None:
            status_list = []
            if approval_status == 'actioned':
                status_list = ['A', 'R']
            elif approval_status == 'not-actioned':
                status_list = ['P']
            approval_list = filter(
                lambda approval: approval.approver_status in status_list, approval_list)
        serializer = self.get_serializer(approval_list, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        current_employee = get_employee(self.request.user)
        serializer = UpdateApprovalSerializer(instance, data=request.data, context={
                                              'approval_id': self.kwargs.get('pk'), 'employee_id': current_employee})
        serializer.is_valid(raise_exception=True)
        approval = serializer.save()
        result_serializer = ApprovalSerializer(approval)
        return Response(result_serializer.data)


class LeaveApprovalInfoViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        get_approvals(current_employee, self.kwargs['approval_pk'])
        queryset = LeaveApproval.objects.select_related(
            'approver__user').filter(request_number__leave_approval__id=self.kwargs['approval_pk'])\
            .filter(request_number__leave_approval__approver=current_employee)
        return queryset

    def get_serializer_class(self):
        return ApprovalInfoSerializer


class MyTeamViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        employee = get_employee(self.request.user)
        queryset = Team.objects\
            .filter(project=employee.project)\
            .annotate(member_count=Count('team_members')).filter(
                team_members__employee=employee)
        if self.action == 'retrieve':
            queryset = Team.objects\
                .prefetch_related(Prefetch('team_members', queryset=TeamMember.objects.select_related("employee", "employee__user")))\
                .filter(
                    team_members__employee=employee, project=employee.project)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTeamSerializer
        if self.request.method == "PATCH":
            return UpdateTeamSerializer
        if self.action == 'list':
            return SimpleTeamSerializer
        if self.action == 'retrieve':
            return RetrieveTeamSerializer

        return TeamSerializer

    def get_serializer_context(self):
        current_employee = get_employee(self.request.user)
        team_id = self.kwargs.get('pk')
        return {'user': self.request.user, 'employee': current_employee, 'is_current_user_team_admin': get_is_user_team_admin(team_id, current_employee)}

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request.user)
        serializer = CreateTeamSerializer(
            data=request.data, context={"employee": current_employee})
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        result = self.get_queryset().filter(pk=request.pk).first()
        serializer = SimpleTeamSerializer(result)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        current_employee = get_employee(self.request.user)
        team_id = self.kwargs['pk']
        serializer = UpdateTeamSerializer(
            instance=self.get_object(), data=request.data, context={'employee': current_employee, 'is_user_team_admin': get_is_user_team_admin(
                team_id, current_employee)})
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        result = self.get_queryset().filter(pk=request.pk).first()
        serializer = SimpleTeamSerializer(result)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        current_employee = get_employee(self.request.user)
        team_id = self.kwargs['pk']
        is_current_user_team_admin = get_is_user_team_admin(
            team_id, current_employee)
        if not is_current_user_team_admin:
            return Response(status=400, data='you are not an admin')

        return super().destroy(request, *args, **kwargs)


class MyTeamMemberViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        current_employee = get_employee(self.request.user)
        get_my_teams(current_employee, self.kwargs['myteam_pk'])
        return TeamMember.objects.select_related('employee__user')\
            .filter(team=self.kwargs['myteam_pk'], team__project=current_employee.project,
                    team__team_members__employee=current_employee)

    def create(self, request, *args, **kwargs):
        employee = get_employee(self.request.user)
        serializer = CreateTeamMemberSerializer(
            data=request.data, many=True, context={"team_id": self.kwargs['myteam_pk'],
                                                   'employee': employee}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        total_members = TeamMember.objects.filter(
            team=self.kwargs['myteam_pk'])
        resultSerializer = TeamMemberSerializer(total_members, many=True, context={'employee': employee,
                                                                                   'is_current_user_team_admin':
                                                                                   get_is_user_team_admin(self.kwargs.get('myteam_pk'), employee)})
        return Response({'id': self.kwargs['myteam_pk'], "team_members": resultSerializer.data, "member_count": len(total_members)})

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTeamMemberSerializer
        if self.request.method == "PATCH":
            return UpdateTeamMemberSerializer
        return TeamMemberSerializer

    def get_serializer_context(self):
        employee = get_employee(self.request.user)
        return {"team_id": self.kwargs.get('myteam_pk'), "team_member_id": self.kwargs.get('pk'),
                'employee': employee,
                'is_current_user_team_admin': get_is_user_team_admin(self.kwargs['myteam_pk'], employee)}

    def destroy(self, request, *args, **kwargs):
        employee = get_employee(self.request.user)
        team_id = self.kwargs['myteam_pk']
        requested_member = self.get_object()
        is_current_user_team_admin = get_is_user_team_admin(
            team_id, employee)
        if not is_current_user_team_admin:
            return Response(status=400, data='you are not an admin')
        team_members = TeamMember.objects.filter(team__project=employee.project,
                                                 team_id=team_id)
        if len(team_members) <= 2:
            return Response("Minimum 2 members should be present in the group", status=400)

        if employee == requested_member.employee:
            if len(team_members.filter(role='A')) <= 1:
                return Response("Select someone as admin before you exit", status=400)

        return super().destroy(request, *args, **kwargs)


class AllTeamViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        return get_all_teams(employee)

    @ action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        employee = get_employee(self.request.user)
        get_all_teams(employee, pk)
        serializer = SubscribeTeamSerializer(data=request.data,
                                             context={'employee': employee,
                                                      "team_id": pk, 'subscribe': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "ok"})

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        employee = get_employee(self.request.user)
        get_all_teams(employee, pk)
        serializer = SubscribeTeamSerializer(
            data=request.data,
            context={'employee': employee, "team_id": pk, 'subscribe': False})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "ok"})

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RetrieveTeamSerializer
        return SimpleAllTeamSerializer

    def get_serializer_context(self):
        return {'user': self.request.user}


class AllTeamMemberViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):

    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        get_all_teams(employee, self.kwargs['allteam_pk'])
        return TeamMember.objects.filter(team=self.kwargs['allteam_pk']).exclude(team__team_members__employee=employee)

    def get_serializer_class(self):
        return TeamMemberSerializer

    def get_serializer_context(self):
        return {"team_id": self.kwargs['allteam_pk']}


class SubscribedTeamViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        return SubscribeTeam.objects.select_related('team').filter(employee=employee)

    def get_serializer_class(self):
        return ListSubscribeTeamSerializer
 # not-verified


class AbsenteesViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request.user)
        return TeamMember.objects.select_related('team').select_related('employee__user').filter(
            team__subscribed_teams__employee=employee).exclude(employee=employee)

    def get_serializer_class(self):
        return AbsenteesTeamSerializer

    def list(self, request, *args, **kwargs):
        query_params = request.query_params
        date_string = query_params.get('date')
        try:
            date = datetime.strptime(date_string, '%Y-%m-%d')
        except:
            return Response("Date required", status=404)
        queryset = self.get_queryset()
        if date is not None:
            queryset = queryset.filter(
                employee__leave_request__leave_dates__date=date)
        employee_id = query_params.get('emp')
        if employee_id is not None:
            absentee = queryset.filter(employee=employee_id)
            serializer = AbsenteesDetailSerializer(absentee, many=True)
            data = serializer.data
            result = data_group_by(data, 'employee', 'team', 'team_list')
            absentee_info = result.get(employee_id)
            if absentee_info is not None:
                query_set = LeaveDate.objects.filter(
                    date__gt=date, request_number__employee=employee_id)
                leave_dates_serializer = LeaveDatesSerializer(
                    query_set, many=True)
                absentee_info['upcoming_leaves'] = [leave['date']
                                                    for leave in leave_dates_serializer.data]
                return Response(absentee_info)
            return Response(data={"detail": "Not found"}, status=404)

        serializer = AbsenteesTeamSerializer(queryset, many=True)
        group_by = {}
        data = serializer.data
        for item in data:
            if item['employee'] not in group_by:
                group_by[item['employee']] = item
                group_by[item['employee']]['team_list'] = []
            group_by[item['employee']]['team_list'].append(item['team'])
        return Response(list(group_by.values()))


class GroupsLeaveCountViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_serializer_class(self):
        return GroupsLeaveCountSerializer

    def get_queryset(self):
        employee = get_employee(self.request.user)
        return SubscribeTeam.objects.select_related('team').filter(employee=employee)

    def list(self, request, *args, **kwargs):
        query_param = self.request.query_params
        date_string = query_param.get('date')
        try:
            date = datetime.strptime(date_string, '%Y-%m-%d')
        except:
            return Response("Date required")
        queryset = self.get_queryset()
        queryset = queryset.filter(team__team_members__employee__leave_request__leave_dates__date=date).annotate(
            leave_count=Count('team__team_members__employee__leave_request')).order_by('team__name')[:5]
        serializer = GroupsLeaveCountSerializer(queryset, many=True)
        return Response(serializer.data)


class TeamAnalysisViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request.user)
        return get_my_teams(employee)

    def get_serializer_class(self):
        return TeamAnalysisSerializer


class TeamAnalysisMembersViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request.user)
        team_id = self.kwargs['teamanalysis_pk']
        get_my_teams(employee, team_id)
        base_query = get_team_members(team_id, employee)
        filtered_query = filter_leave_dates_by_type(
            base_query, self.request.query_params)
        return get_leave_count(filtered_query)

    def get_serializer_class(self):
        return TeamAnalysisMembersSerializer


class LeaveBalanceViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    @ action(detail=False, methods=['get'])
    def total(self, request):
        employee = get_employee(self.request.user)
        employee_timezone = employee.user.timezone
        present_date = get_current_date_in_user_timezone(employee_timezone)
        year = present_date.year
        fiscal_month = FiscalYear.objects.get(project=employee.project)
        fiscal_year = FiscalYearInfo(fiscal_month.month)
        current_fiscal_year = fiscal_year.get_fy_period(year)
        leave_taken = LeaveDate.objects.filter(date__gte=current_fiscal_year['start_dt'],
                                               date__lte=current_fiscal_year['end_dt'],
                                               request_number__employee=employee, request_number__type__status='A').aggregate(leave_taken=Count('date'))
        total = LeaveType.objects.filter(project=employee.project, status='A').aggregate(
            total=Sum('days'))
        return Response({"leave_taken": leave_taken.get('leave_taken'), "total": total.get('total')})

    def get_queryset(self):
        employee = get_employee(self.request.user)
        employee_timezone = employee.user.timezone
        current_date = get_current_date_in_user_timezone(employee_timezone)
        fy = self.request.query_params.get('fy')
        fiscal_month = get_fiscal_month(employee.project)
        fiscal_year = FiscalYearInfo(fiscal_month)
        year = current_date.year
        if(fy):
            year = int(fy)
        current_fiscal_year = fiscal_year.get_fy_period(year)
        leave_taken = ExpressionWrapper(
            Count('leave_request__leave_dates__date', filter=Q(
                Q(leave_request__status='A') | Q(leave_request__status='P'),
                leave_request__employee=employee,
                leave_request__leave_dates__date__gte=current_fiscal_year['start_dt'],
                leave_request__leave_dates__date__lte=current_fiscal_year['end_dt'])),
            output_field=IntegerField())
        balance = ExpressionWrapper(
            F('days')-F('leave_taken'), output_field=IntegerField())
        return LeaveType.objects.prefetch_related('project__fiscal_year')\
            .filter(project=employee.project, status='A').annotate(leave_taken=leave_taken)\
            .annotate(balance=balance)

    def get_serializer_class(self):
        return LeaveBalanceSerializer


class FinancialYear(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        user = self.request.user
        current_employee = get_employee(user)
        fiscal_month = get_fiscal_month(current_employee.project)
        fiscal_year_info = FiscalYearInfo(fiscal_month)
        current_fiscal_year = fiscal_year_info.get_current_fiscal_year(
            user.timezone)
        return Response(current_fiscal_year)


class FinancialYearList(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get(self, request):
        user = self.request.user
        current_employee = get_employee(user)
        current_date = get_current_date_in_user_timezone(user.timezone)
        created_on_date = get_date_in_user_timezone(
            current_employee.created_on, user.timezone)
        fiscal_month = get_fiscal_month(current_employee.project)
        fiscal_year = FiscalYearInfo(fiscal_month)
        fy_list = fiscal_year.get_fy_list(created_on_date, current_date)
        return Response(fy_list)


class MyGroupsReport(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request):
        employee = get_employee(self.request.user)
        project_name = employee.project.name
        allowed_section_list = [1, 2]
        query_params = self.request.query_params
        sections = query_params.get('sections')
        team_id = query_params.get('team', '')
        section_params = []
        team = ''
        team = get_my_teams(employee, team_id)
        try:
            section_params = validate_my_groups_report_section_id(
                sections, allowed_section_list)
        except CustomApiResponseError as e:
            return Response(data=e.data, status=e.status)

        # initialize report
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.25*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)

        # Create a list of flowables to build the PDF content
        flowables = []
        # add group title to report:
        flowables.append(Paragraph(team.name, style_title))
        # adding each sections in report
        if 1 in section_params:
            date_string = query_params.get('date')
            if date_string is None:
                date = get_current_date_in_user_timezone(
                    employee.user.timezone)
            else:
                date = datetime.strptime(date_string, "%d-%m-%Y")
            leave_request_queryset = get_absentees_from_my_team(team.id, date)
            dictArr = leave_request_queryset.select_related('employee__user').values(
                'employee__user__username', 'employee__user__email', 'request_number', 'from_date', 'type__code', 'duration__code')
            values = [[column['get_content'](obj) if column.get("get_content") is not None else
                       obj[column['key']] for column in leave_request_columns] for obj in dictArr]
            label = [column['label'] for column in leave_request_columns]
            data = [label]
            data.extend(values)
        # Add the text
            flowables.append(
                Paragraph(f'Leaves as of {date.strftime("%d %b %y")}', style_body))
            flowables.append(Spacer(1, 0.15*inch))
            if not len(values):
                flowables.append(
                    Paragraph(f'No Leaves found', style_not_found_text))
        # Add the table
            else:
                table = Table(data)
                table.setStyle(TableStyle(basic_table_style))
                flowables.append(table)
            flowables.append(Spacer(1, 0.15*inch))

        if 2 in section_params:
            base_query = get_team_members(team.id, employee)
            filtered_query = filter_leave_dates_by_type(
                base_query, query_params)
            employees_leave_count_queryset = get_leave_count(filtered_query)

            dictArr = employees_leave_count_queryset.values(
                'employee__user__username', 'employee__user__email', 'leave_count')
            values = [[column['get_content'](obj) if column.get("get_content") is not None else
                       obj[column['key']] for column in leave_count_columns] for obj in dictArr]
            label = [column['label'] for column in leave_count_columns]
            data = [label]
            data.extend(values)
            flowables.append(
                Paragraph(f'Leave count as of {get_leave_period_type_label(query_params)}', style_body))
            flowables.append(Spacer(1, 0.15*inch))
            if not len(values):
                flowables.append(
                    Paragraph(f'No Leave counts found', style_not_found_text))
        # Add the table
            else:
                table = Table(data)
                table.setStyle(TableStyle(basic_table_style))
                flowables.append(table)
            flowables.append(Spacer(1, 0.15*inch))

        doc.build(flowables, onFirstPage=lambda canvas, doc: get_header_footer(
            canvas, doc, project_name),
            onLaterPages=lambda canvas, doc: get_header_footer(
            canvas, doc, project_name))
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='my_groups_leave_analysis.pdf')


class AllGroupsReport(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request):
        employee = get_employee(self.request.user)
        project_name = employee.project.name
        query_params = self.request.query_params
        date_string = query_params.get('date')
        date = ''
        try:
            date = datetime.strptime(date_string, "%d-%m-%Y")
        except:
            return Response(status=404, data='Date Required')
        subscribed_teams = get_subscribed_teams(employee)
        is_absentees_available = False
        absentees = get_absentees_from_subscribed_groups(employee, date).values("employee__user__username",
                                                                                'employee__user__email',
                                                                                'type__code',
                                                                                "duration__code",
                                                                                "employee__teams__team__name",
                                                                                "employee__teams__team__id")
        # initialize report
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.25*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
        # Create a list of flowables to build the PDF content
        flowables = []
        if not len(subscribed_teams):
            return Response(status=400, data='please subscribe atleast one team to generate report')
        # add group title to report:
        title = f'Absentees as of {date.strftime("%d %b %y")}'
        flowables.append(Paragraph(title, style_title))
        for team in subscribed_teams:
            team__absentees = list(
                filter(lambda absentees: absentees["employee__teams__team__id"] == team.id, absentees))
            values = [[column['get_content'](obj) if column.get("get_content") is not None else
                       obj[column['key']] for column in absentees_columns] for obj in team__absentees]
            label = [column['label'] for column in absentees_columns]
            data = [label]
            data.extend(values)
            if len(values):
                if not is_absentees_available:
                    is_absentees_available = True
                flowables.append(
                    Paragraph(f'{team.name}', style_body))
                flowables.append(Spacer(1, 0.15*inch))
                table = Table(data)
                table.setStyle(TableStyle(basic_table_style))
                flowables.append(table)
                flowables.append(Spacer(1, 0.15*inch))
            if not is_absentees_available:
                flowables.append(Spacer(1, 0.15*inch))
                flowables.append(
                    Paragraph(f'No absentees found in subscribed groups', style_not_found_text))

        doc.build(flowables, onFirstPage=lambda canvas, doc: get_header_footer(canvas, doc, project_name),
                  onLaterPages=lambda canvas, doc: get_header_footer(canvas, doc, project_name))
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='all_group_leave_analysis.pdf')


class AllGroupsExcelReport(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request):
        buffer = io.BytesIO()
        wb = Workbook()
        employee = get_employee(self.request.user)
        query_params = self.request.query_params
        date_string = query_params.get('date')
        try:
            date = datetime.strptime(date_string, "%d-%m-%Y")
        except:
            return Response("Date required", status=404)
        sheet = wb.active
        sheet.title = date_string
        absentees = get_absentees_from_subscribed_groups(employee, date).values("employee__user__username",
                                                                                'employee__user__email',
                                                                                'type__code',
                                                                                "duration__code",
                                                                                "employee__teams__team__name",
                                                                                "employee__teams__team__id")
        # Write the table headers
        sheet['A1'] = 'Name'
        sheet['B1'] = 'Email'
        sheet['C1'] = 'Leave Type'
        sheet['D1'] = 'Leave Duration'
        sheet['E1'] = 'Group'
        values = [[obj[column['key']]
                   for column in absentees_excel_columns] for obj in absentees]
        for record in values:
            sheet.append(record)
        wb.save(buffer)
        buffer.seek(0)
        return FileResponse(buffer,  content_type='application/vnd.ms-excel',
                            as_attachment=True, filename='absentees.xlsx')


class AnnouncementViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get', 'post']

    @action(detail=False, methods=['post'])
    def viewed_by(self, request):
        user = self.request.user
        employee = get_employee(user)
        queryset = self.get_queryset()
        announcement_viewed_records = []
        for announcement in queryset:
            try:
                AnnouncementViewedEmployee.objects.get(
                    announcement=announcement, employee=employee)
            except:
                i = AnnouncementViewedEmployee(
                    employee=employee, announcement=announcement)
                announcement_viewed_records.append(i)
        AnnouncementViewedEmployee.objects.bulk_create(
            announcement_viewed_records)
        serializer = SimpleAnnouncementSerializer(
            queryset, many=True, context={"employee": employee})
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAnnouncementSerializer
        if self.action == 'retrieve':
            return AnnouncementSerializer
        return SimpleAnnouncementSerializer

    def get_queryset(self):
        user = self.request.user
        employee = get_employee(user)
        date = get_current_date_in_user_timezone(user.timezone)
        return Announcement.objects.prefetch_related('announcement_viewed_by')\
            .filter(announcement_team__team__team_members__employee=employee, expiry_date__gte=date)\
            .order_by('-id', '-created_on').distinct('id')

    def get_serializer_context(self):
        user = self.request.user
        employee = get_employee(user)
        return {"employee": employee}

    def create(self, request, *args, **kwargs):
        employee = get_employee(self.request.user)
        serializer = CreateAnnouncementSerializer(
            data=request.data, context={'employee': employee})
        serializer.is_valid(raise_exception=True)
        new_announcement = serializer.save()
        result = SimpleAnnouncementSerializer(new_announcement)
        return Response(result.data)
