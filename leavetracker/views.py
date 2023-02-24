import pytz
from .query_methods import get_my_teams, get_all_teams, get_leaves, get_approvals, get_employee, get_fiscal_month, get_is_user_team_admin
from .utils import get_current_date, get_present_datetime_in_user_timezone
from django.db.models import Prefetch
from datetime import datetime, timedelta
from project.utils import FiscalYear as Fiscalyear
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import ListModelMixin, UpdateModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from leavetracker.permissions import IsEmployee
from leavetracker.utils import data_group_by
from project.models import Project
from project.serializers import SimpleProjectSerializer
from .models import Domain, Employee, Approver, FiscalYear, LeaveApproval, LeaveDate, LeaveDuration, LeaveType, Role, SubscribeTeam, Team, TeamMember, LTAccountPreference
from .serializers import AbsenteesDetailSerializer, ApprovalInfoSerializer, ApproverSerializer, CreateLeaveRequestSerializer, CreateTeamMemberSerializer, CreateTeamSerializer, EmployeeSerializer, MyEmployeeAccountsSerializer, RetrieveTeamSerializer, GroupsLeaveCountSerializer, LeaveBalanceSerializer, LeaveDatesSerializer, LeaveDurationSerializer, LeaveTypeSerializer, SimpleAllTeamSerializer, SimpleDomainSerializer, SimpleEmployeeSerializer, SimpleLeaveRequestSerializer, LeaveRequestSerializer, ListSubscribeTeamSerializer, MyInfoSerializer, CreateApproverSerializer, SimpleRoleSerializer, SimpleTeamSerializer, SimpleUserSerializer, SubscribeEmployeeSerializer, SubscribeSerializer, SubscribeTeamSerializer, TeamAnalysisMembersSerializer, TeamAnalysisSerializer, AbsenteesTeamSerializer,  TeamMemberSerializer, TeamSerializer, ApprovalSerializer, UpdateApprovalSerializer, UpdateTeamMemberSerializer, UpdateTeamSerializer
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, IntegerField, DateField, Func
from rest_framework.views import APIView
from leavetracker.utils import get_current_date
import logging


logger = logging.getLogger(__name__)


class MyAccountsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = MyEmployeeAccountsSerializer

    def get_queryset(self):
        return Employee.objects.filter(user=self.request.user, status="A").select_related('project')


class EmployeeAccountPreference(APIView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request):
        user = self.request.user
        try:
            preference = LTAccountPreference.objects.get(user=user)
            try:
                project = preference.project
                if(project.status != 'A'):
                    return Response(status=404, data={'code': 'PREF.PRJCT.NOT.FOUND', 'message': "No active project found with given preference"})
                Employee.objects.get(
                    user=user, project=project, status='A')
                serializer = SimpleProjectSerializer(project)
                return Response(serializer.data)
            except:
                return Response(status=404, data={'code': 'PREF.EMP/PRJCT.NOT.FOUND', 'message': "No active project/employee account found with given preference"})
        except:
            return Response(status=404, data={'code': 'PREF.NOT.FOUND', 'message': "No user account preference found"})

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


class EmployeeViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    http_method_names = ['get', 'head', 'options']
    filter_backends = [SearchFilter]
    search_fields = ['user__email', 'user__username']
    permission_classes = [IsAuthenticated, IsEmployee]

    @action(detail=False, methods=['get'])
    def me(self, request):
        current_employee = get_employee(self.request)
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
        current_employee = get_employee(self.request)
        return Employee.objects.select_related('user')\
            .filter(project=current_employee.project, status='A')\
            .exclude(user=current_employee.user)


class RoleViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    serializer_class = SimpleRoleSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return Role.objects.filter(project=current_employee.project)


class DomainViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    serializer_class = SimpleDomainSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return Domain.objects.filter(project=current_employee.project)


class LeaveTypeViewset(ListModelMixin, GenericViewSet):
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return LeaveType.objects.filter(project=current_employee.project, status="A")


class LeaveDurationViewset(ListModelMixin, GenericViewSet):
    serializer_class = LeaveDurationSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return LeaveDuration.objects.filter(project=current_employee.project, status="A")


class ApproverViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request)
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
        current_employee = get_employee(self.request)
        return Approver.objects.select_related('approver__user').filter(employee=current_employee)


class LeaveRequestViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return get_leaves(current_employee)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLeaveRequestSerializer
        return LeaveRequestSerializer

    def get_serializer_context(self):
        return {"user": self.request.user}

    def list(self, request, *args, **kwargs):
        query_params = request.query_params
        leave_period_param = query_params.get('period')
        current_date = get_current_date(self.request.user.timezone)
        filtered_queryset = self.get_queryset().filter(to_date__gte=current_date)
        if leave_period_param is not None:
            if leave_period_param == 'prev':
                filtered_queryset = self.get_queryset().filter(
                    to_date__lt=current_date)
        serializer = self.get_serializer(filtered_queryset, many=True, context={
                                         "user": self.request.user})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request)
        serializer = CreateLeaveRequestSerializer(
            data=request.data, context={"employee": current_employee})
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        serializer = LeaveRequestSerializer(request, context={
            "user": self.request.user})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        current_date = get_current_date(user.timezone)
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
        current_employee = get_employee(self.request)
        get_leaves(current_employee, self.kwargs['request_pk'])
        return LeaveDate.objects.filter(request_number=self.kwargs['request_pk'])

    def get_serializer_class(self):
        return LeaveDatesSerializer


class ApprovalInfoViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
        get_leaves(current_employee, self.kwargs['request_pk'])
        queryset = LeaveApproval.objects.select_related('approver__user').filter(request_number__employee=current_employee)\
            .filter(request_number=self.kwargs['request_pk'])
        return queryset

    def get_serializer_class(self):
        return ApprovalInfoSerializer


class ApprovalViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get',  'patch']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateApprovalSerializer
        return ApprovalSerializer

    def list(self, request, *args, **kwargs):
        query_params = request.query_params
        approval_status = query_params.get('status')
        period = query_params.get('period')
        least_utc_date = datetime.utcnow()-timedelta(days=1)
        filtered_queryset = self.get_queryset().filter(
            request_number__from_date__gte=least_utc_date)
        if period == 'prev':
            filtered_queryset = self.get_queryset().filter(
                request_number__from_date__lt=least_utc_date)

        if approval_status is not None:
            if approval_status == 'A':
                filtered_queryset = filtered_queryset.filter(
                    approver_status="A")
            elif approval_status == 'A,R':
                filtered_queryset = filtered_queryset.filter(
                    Q(approver_status="A") | Q(approver_status="R"))
            elif approval_status == 'P':
                filtered_queryset = filtered_queryset.filter(
                    approver_status="P")
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        current_employee = get_employee(self.request)
        serializer = UpdateApprovalSerializer(instance, data=request.data, context={
                                              'approval_id': self.kwargs.get('pk'), 'employee_id': current_employee})
        serializer.is_valid(raise_exception=True)
        approval = serializer.save()
        result_serializer = ApprovalSerializer(approval)
        return Response(result_serializer.data)

    def get_queryset(self):
        current_employee = get_employee(self.request)
        return get_approvals(current_employee)


class LeaveApprovalInfoViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        current_employee = get_employee(self.request)
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

    def get_queryset(self):
        employee = get_employee(self.request)
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
        current_employee = get_employee(self.request)
        team_id = self.kwargs.get('pk')
        return {'user': self.request.user, 'employee': current_employee, 'is_current_user_team_admin': get_is_user_team_admin(team_id, current_employee)}

    def create(self, request, *args, **kwargs):
        current_employee = get_employee(self.request)
        serializer = CreateTeamSerializer(
            data=request.data, context={"employee": current_employee})
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        result = self.get_queryset().filter(pk=request.pk).first()
        serializer = SimpleTeamSerializer(result)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        current_employee = get_employee(self.request)
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
        current_employee = get_employee(self.request)
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
        current_employee = get_employee(self.request)
        get_my_teams(current_employee, self.kwargs['myteam_pk'])
        return TeamMember.objects.select_related('employee__user')\
            .filter(team=self.kwargs['myteam_pk'], team__project=current_employee.project,
                    team__team_members__employee=current_employee)

    def create(self, request, *args, **kwargs):
        employee = get_employee(self.request)
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
        employee = get_employee(self.request)
        return {"team_id": self.kwargs.get('myteam_pk'), "team_member_id": self.kwargs.get('pk'),
                'employee': employee,
                'is_current_user_team_admin': get_is_user_team_admin(self.kwargs['myteam_pk'], employee)}

    def destroy(self, request, *args, **kwargs):
        employee = get_employee(self.request)
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
        print(requested_member.employee == employee)

        if employee == requested_member.employee:
            if len(team_members.filter(role='A')) <= 1:
                return Response("Select someone as admin before you exit", status=400)

        return super().destroy(request, *args, **kwargs)


class AllTeamViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        employee = get_employee(self.request)
        return get_all_teams(employee)

    @ action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        employee = get_employee(self.request)
        get_all_teams(employee, pk)
        serializer = SubscribeTeamSerializer(data=request.data,
                                             context={'employee': employee,
                                                      "team_id": pk, 'subscribe': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "ok"})

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        employee = get_employee(self.request)
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
        employee = get_employee(self.request)
        get_all_teams(employee, self.kwargs['allteam_pk'])
        return TeamMember.objects.filter(team=self.kwargs['allteam_pk']).exclude(team__team_members__employee=employee)

    def get_serializer_class(self):
        return TeamMemberSerializer

    def get_serializer_context(self):
        return {"team_id": self.kwargs['allteam_pk']}


class SubscribedTeamViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get_queryset(self):
        employee = get_employee(self.request)
        return SubscribeTeam.objects.select_related('team').filter(employee=employee)

    def get_serializer_class(self):
        return ListSubscribeTeamSerializer
 # not-verified


class AbsenteesViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request)
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
            return Response([])
        queryset = self.get_queryset()

        if date is not None:
            queryset = queryset.filter(
                employee__leave_request__leave_dates__date=date)
            print(queryset)
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


class GraphViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_serializer_class(self):
        return GroupsLeaveCountSerializer

    def get_queryset(self):
        query_param = self.request.query_params
        date_string = query_param.get('date')
        try:
            date = datetime.strptime(date_string, '%Y-%m-%d')
        except:
            return Response([])
        employee = get_employee(self.request)
        return SubscribeTeam.objects.select_related('team').filter(
            employee=employee,
            team__team_members__employee__leave_request__leave_dates__date=date).annotate(
            leave_count=Count('team__team_members__employee__leave_request')).order_by('team__name')[:5]

    @ action(detail=False, methods=['get'])
    def groups_leave_count(self, request):
        queryset = self.get_queryset()
        serializer = GroupsLeaveCountSerializer(queryset, many=True)
        return Response(serializer.data)


class TeamAnalysisViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request)
        return get_my_teams(employee)

    def get_serializer_class(self):
        return TeamAnalysisSerializer


class TeamAnalysisMembersViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get_queryset(self):
        employee = get_employee(self.request)
        get_my_teams(employee, self.kwargs['teamanalysis_pk'])
        base_query = TeamMember.objects.select_related('employee__user').filter(
            team=self.kwargs['teamanalysis_pk'], team__project=employee.project)
        type = self.request.query_params.get('type')
        if type is not None:
            if type == 'year':
                year = self.request.query_params.get('year')
                if year is not None:
                    base_query = base_query.filter(
                        employee__leave_request__leave_dates__date__year=year)
            if type == 'month':
                year = self.request.query_params.get('year')
                month = self.request.query_params.get('month')
                if year is not None and month is not None:
                    base_query = base_query.filter(
                        employee__leave_request__leave_dates__date__year=year,
                        employee__leave_request__leave_dates__date__month=month)
            if type == 'date':
                start_date = self.request.query_params.get('start-date')
                end_date = self.request.query_params.get('end-date')
                if start_date is not None and end_date is not None:
                    base_query = base_query.filter(
                        employee__leave_request__leave_dates__date__gte=start_date,
                        employee__leave_request__leave_dates__date__lte=end_date)

        return base_query.annotate(
            leave_count=Count('employee__leave_request__leave_dates')).order_by('-leave_count')[:5]

    def get_serializer_class(self):
        return TeamAnalysisMembersSerializer


class LeaveBalanceViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmployee]

    @ action(detail=False, methods=['get'])
    def total(self, request):
        employee = get_employee(self.request)
        employee_timezone = employee.user.timezone
        present_date = get_present_datetime_in_user_timezone(employee_timezone)
        year = present_date.year
        fiscal_month = FiscalYear.objects.get(project=employee.project)
        fiscal_year = Fiscalyear(fiscal_month.month)
        current_fiscal_year = fiscal_year.get_fy_period(year)
        leave_taken = LeaveDate.objects.filter(date__gte=current_fiscal_year['start_dt'],
                                               date__lte=current_fiscal_year['end_dt'],
                                               request_number__employee=employee, request_number__type__status='A').aggregate(leave_taken=Count('date'))
        total = LeaveType.objects.filter(project=employee.project, status='A').aggregate(
            total=Sum('days'))
        return Response({"leave_taken": leave_taken.get('leave_taken'), "total": total.get('total')})

    def get_queryset(self):
        employee = get_employee(self.request)
        employee_timezone = employee.user.timezone
        present_date = get_present_datetime_in_user_timezone(employee_timezone)
        fy = self.request.query_params.get('fy')
        fiscal_month = get_fiscal_month(employee.project)
        fiscal_year = Fiscalyear(fiscal_month)
        year = present_date.year
        if(fy):
            year = int(fy)
        current_fiscal_year = fiscal_year.get_fy_period(year)
        leave_taken = ExpressionWrapper(
            Count('leave_request__leave_dates__date', filter=Q(
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
    http_method_names = ['get']

    def get(self, request):
        current_employee = get_employee(self.request)
        employee_timezone = current_employee.user.timezone
        fiscal_month = get_fiscal_month(current_employee.project)
        fiscal_year = Fiscalyear(fiscal_month)
        current_fiscal_year = fiscal_year.get_current_fiscal_year(
            employee_timezone)
        return Response(current_fiscal_year)


class FinancialYearList(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    http_method_names = ['get']

    def get(self, request):
        current_employee = get_employee(self.request)
        employee_timezone = current_employee.user.timezone
        present_date = get_present_datetime_in_user_timezone(employee_timezone)
        created_on_date = current_employee.created_on.astimezone(
            pytz.timezone(employee_timezone))
        fiscal_month = get_fiscal_month(current_employee.project)
        fiscal_year = Fiscalyear(fiscal_month)
        fy_list = fiscal_year.get_fy_list(created_on_date, present_date)
        return Response(fy_list)
