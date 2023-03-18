from .query_methods import get_my_projects
from .models import Project, ProjectAdmin, ProjectAdminAccess, ProjectAdminRole, ProjectAdminRoleAccess, ProjectOwner
from .permissions import IsProjectOwner, IsProjectMember, is_user_has_module_permission, is_user_project_member, is_authenticated_user, is_user_project_member_has_permission
from .serializers import CreateAdminRoleSerializer, ProjectAccessSerializer, AdminRoleSerializer, \
    SimpleAdminRoleSerializer, AdminSerializer, CreateAdminSerializer, CreateProjectSerializer, \
    AdminRoleAccessSerializer, ProjectAdminAccessSerializer, ProjectAdminSerializer,\
    ProjectOwnerSerializer, ProjectSerializer, UpdateAdminSerializer, CreateEmployeeSerializer, \
    UpdateEmployeeSerializer, UpdateEmployeeStatusSerializer, CreateDomainSerializer, CreateRoleSerializer, CreateLeaveTypeSerializer, CreateLeaveDurationSerializer
from leavetracker.models import Access, Domain, Employee, FiscalYear, LeaveDuration, LeaveType, Role, RoleAccess
from leavetracker.serializers import SimpleRoleSerializer, CreateRoleAccessSerializer, DomainSerializer, EmployeeSerializer, FiscalYearSerializer, LeaveDurationSerializer, LeaveTrackerAccessSerializer, LeaveTypeSerializer, RoleAccessSerializer, RoleSerializer
from django.db.models.aggregates import Count
from django.db.models import Value
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
import calendar


class LeaveTrackerAccessViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    def get_queryset(self):
        return Access.objects.all()

    def get_serializer_class(self):
        return LeaveTrackerAccessSerializer


class ProjectAccessViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    def get_queryset(self):
        return ProjectAdminAccess.objects.all()

    def get_serializer_class(self):
        return ProjectAccessSerializer


class ProjectViewSet(ModelViewSet):
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_has_module_permission('CREATE_PROJECT')
        else:
            return is_authenticated_user()

    def get_queryset(self):
        return get_my_projects(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateProjectSerializer
        return ProjectSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user}

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsProjectMember])
    def myprofile(self, request, **kwargs):
        admin = None
        owner = None
        admin_record = ProjectAdmin.objects.filter(
            project=self.kwargs['pk'], user=self.request.user).first()
        if admin_record is not None:
            admin = ProjectAdminSerializer(admin_record).data
        owner_record = ProjectOwner.objects.filter(
            project=self.kwargs['pk'], user=self.request.user).first()
        if owner_record is not None:
            owner = ProjectOwnerSerializer(owner_record).data
        return Response({'id': self.request.user.email, 'admin': admin, 'owner': owner})

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsProjectMember])
    def section_counts(self, request, **kwargs):
        employee = Employee.objects.filter(
            project_id=self.kwargs['pk'], status='A').aggregate(employee=Count('id'))
        role = Role.objects.filter(
            project_id=self.kwargs['pk']).aggregate(role=Count('id'))
        domain = Domain.objects.filter(
            project_id=self.kwargs['pk']).aggregate(domain=Count('id'))
        leave_type = LeaveType.objects.filter(
            project_id=self.kwargs['pk'], status='A').aggregate(leave_type=Count('id'))
        leave_duration = LeaveDuration.objects.filter(
            project_id=self.kwargs['pk'], status='A').aggregate(leave_duration=Count('id'))
        admin = ProjectAdmin.objects.filter(
            project_id=self.kwargs['pk']).aggregate(admin=Count('id'))
        admin_role = ProjectAdminRole.objects.filter(
            project_id=self.kwargs['pk']).aggregate(admin_role=Count('id'))
        return Response({**employee, **role, **domain, **leave_type, **leave_duration, **admin, **admin_role})


class EmployeeViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['user__email', 'user__username']
    http_method_names = ['get', 'post', 'put', 'patch', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_project_member_has_permission('EMPLOYEE_NEW')
        if self.request.method == 'PATCH' or self.request.method == "PUT":
            return is_user_project_member_has_permission('EMPLOYEE_EDIT')
        return is_user_project_member()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateEmployeeSerializer
        if self.request.method == "PUT":
            return UpdateEmployeeSerializer
        if self.request.method == 'PATCH':
            return UpdateEmployeeStatusSerializer
        return EmployeeSerializer

    def get_serializer_context(self):
        return {'project_id': self.kwargs.get('project_pk'), 'user_id': self.request.user}

    def get_queryset(self):
        return Employee.objects.select_related('user').select_related('role').select_related('domain')\
            .filter(project=self.kwargs['project_pk'], status='A').annotate(is_close=Value(True))


class RoleViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_project_member_has_permission('ROLE_NEW')
        if self.request.method == 'PATCH':
            return is_user_project_member_has_permission('ROLE_EDIT')
        if self.request.method == 'DELETE':
            return is_user_project_member_has_permission('ROLE_DLT')
        return is_user_project_member()

    def get_queryset(self):
        return Role.objects.filter(project=self.kwargs['project_pk']).annotate(is_delete=Value(True), manage_access=Value(True))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRoleSerializer
        if self.action == 'retrieve':
            return RoleSerializer
        else:
            return SimpleRoleSerializer

    def get_serializer_context(self):
        return {'project_id': self.kwargs.get('project_pk'), 'user_id': self.request.user}

    @action(detail=True, methods=['get', 'post'])
    def access(self, request, **kwargs):
        if(request.method == 'GET'):
            queryset = RoleAccess.objects.filter(
                role=kwargs.get('pk'))
            serializer = RoleAccessSerializer(queryset, many=True)
            return Response(serializer.data)

        if(request.method == 'POST'):
            serializer = CreateRoleAccessSerializer(
                data=request.data, context={
                    'user_id': self.request.user,
                    'role_id': kwargs.get('pk'),
                    'project_id': kwargs.get('project_pk'), })
            serializer.is_valid(raise_exception=True)
            new_data = serializer.save()
            new_serializer = RoleAccessSerializer(new_data, many=True)
            return Response(new_serializer.data)


class DomainViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_project_member_has_permission('DOMAIN_NEW')
        if self.request.method == 'PATCH':
            return is_user_project_member_has_permission('DOMAIN_EDIT')
        if self.request.method == 'DELETE':
            return is_user_project_member_has_permission('DOMAIN_DLT')
        return is_user_project_member()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateDomainSerializer
        else:
            return DomainSerializer

    def get_queryset(self):
        return Domain.objects.filter(project=self.kwargs['project_pk']).annotate(is_delete=Value(True))

    def get_serializer_context(self):
        return {'project_id': self.kwargs.get('project_pk'), 'user_id': self.request.user}


class LeaveTypeViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    http_method_names = ['get', 'post', 'patch', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_project_member_has_permission("LEAVE_TYPE_NEW")
        if self.request.method == 'PATCH':
            return is_user_project_member_has_permission("LEAVE_TYPE_EDIT")
        return is_user_project_member()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLeaveTypeSerializer
        return LeaveTypeSerializer

    def get_queryset(self):
        return LeaveType.objects.filter(project=self.kwargs['project_pk'], status="A").annotate(is_close=Value(True))

    def get_serializer_context(self):
        return {'project_id': self.kwargs.get('project_pk'), 'user_id': self.request.user}


class LeaveDurationViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    http_method_names = ['get', 'post', 'patch', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return is_user_project_member_has_permission("LEAVE_DURATION_NEW")
        if self.request.method == 'PATCH':
            return is_user_project_member_has_permission("LEAVE_DURATION_EDIT")
        return is_user_project_member()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateLeaveDurationSerializer
        return LeaveDurationSerializer

    def get_queryset(self):
        return LeaveDuration.objects.filter(project=self.kwargs['project_pk'], status="A").annotate(is_close=Value(True))

    def get_serializer_context(self):
        return {"project_id": self.kwargs['project_pk'], 'user_id': self.request.user}


class AdminViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['user__username', 'user__email']
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        return ProjectAdmin.objects.select_related('user')\
            .filter(project__id=self.kwargs['project_pk']).annotate(is_delete=Value(True))

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAdminSerializer
        if self.request.method == "PATCH":
            return UpdateAdminSerializer
        return AdminSerializer

    def get_serializer_context(self):
        return {'project_id': self.kwargs.get('project_pk'), 'user_id': self.request.user}


class AdminRoleViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']
    permission_classes = [IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        return ProjectAdminRole.objects.prefetch_related('project_admin_access__access_code')\
            .filter(project__id=self.kwargs['project_pk']).annotate(is_delete=Value(True), manage_access=Value(True))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAdminRoleSerializer
        if self.action == 'retrieve':
            return AdminRoleSerializer
        return SimpleAdminRoleSerializer

    def get_serializer_context(self):
        return {
            'project_id': self.kwargs['project_pk'],
            'user_id': self.request.user
        }

    @action(detail=True, methods=['get', 'post'])
    def access(self, request, **kwargs):
        if(request.method == 'GET'):
            queryset = ProjectAdminRoleAccess.objects.filter(
                role__project__id=self.kwargs['project_pk'], role__id=kwargs.get('pk'))
            serializer = AdminRoleAccessSerializer(queryset, many=True)
            return Response(serializer.data)

        if(request.method == 'POST'):
            serializer = ProjectAdminAccessSerializer(
                data=request.data, context={'role_id': kwargs.get('pk'),
                                            'project_id': kwargs.get('project_pk'),
                                            'user_id': self.request.user.email})
            serializer.is_valid(raise_exception=True)
            new_data = serializer.save()
            serializer_resp = AdminRoleAccessSerializer(new_data, many=True)
            return Response(serializer_resp.data)


class FYMonth(APIView):
    permission_classes = [IsAuthenticated, IsProjectOwner]

    def get(self, request, project_pk):
        project = Project.objects.get(id=project_pk)
        fy_start_month, created = FiscalYear.objects.get_or_create(
            project=project, defaults={'month': calendar.month_abbr[1]})
        return Response(datetime.strptime(fy_start_month.month, "%b").month)

    def patch(self, request, project_pk):
        data = request.data.get('month_id')
        project = Project.objects.get(id=project_pk)
        if data is not None:
            month_id = int(data)
            if not (int(month_id) >= 1 or int(month_id) <= 12):
                return Response("id not within month range", status=400)
            fy_start_month, created = FiscalYear.objects.get_or_create(
                project=project, defaults={'month': calendar.month_abbr[month_id]})
            if not created:
                fy_start_month = FiscalYear.objects.filter(
                    project=project).update(month=calendar.month_abbr[month_id])

        return Response(month_id)
