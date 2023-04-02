from rest_framework import serializers
from core.models import User
from project.models import Project, ProjectAdmin, ProjectAdminAccess, ProjectAdminAccess, ProjectAdminRole, ProjectAdminRoleAccess, ProjectInfo, ProjectOwner
from django.db import transaction
from django.db.models import Q
from leavetracker.models import Employee, Role, Domain, LeaveType, LeaveDuration
from project.validations import RoleDomainValidation, AdminRoleValidation


class ProjectSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "status"]


class SimpleProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ["id", "name"]


class CreateProjectSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "status"]

    def create(self, validated_data):
        with transaction.atomic():
            data = validated_data
# Creating Project
            new_project = Project()
            new_project.name = data['name']
            new_project.description = data['description']
            new_project.save()
# Creating project info
            new_project_info = ProjectInfo()
            new_project_info.project = new_project
            new_project_info.created_by = self.context['user_id']
            new_project_info.save()

# Creating project owner for new project
            project_owner = ProjectOwner()
            project_owner.project = new_project
            project_owner.user = self.context['user_id']
            project_owner.save()

            return new_project


class CreateEmployeeSerializer(serializers.Serializer, RoleDomainValidation):
    email = serializers.EmailField()
    role = serializers.CharField(default=None, allow_blank=True)
    domain = serializers.CharField(default=None, allow_blank=True)

    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('user Not found')
        return email

    def validate(self, data):
        project_id = self.context.get('project_id')
        email = data.get('email')
        if email and Employee.objects.filter(project=project_id, user__email=email).exists():
            raise serializers.ValidationError(
                {"code": 'EMP.ACT.ALREADY.FOUND', "detail": "Employee account already exists for this user"})
        return data

    def save(self, **kwargs):
        with transaction.atomic():
            data = self.validated_data
            project_id = self.context.get('project_id')
            project = Project.objects.get(id=project_id)
            user = User.objects.get(email=data.get('email'))
            new_employee = Employee()
            new_employee.project = project
            new_employee.user = user
            if data.get('role'):
                role = Role.objects.get(
                    code=data.get('role'), project=project_id)
                new_employee.role = role
            if data.get('domain'):
                domain = Domain.objects.get(
                    code=data.get('domain'), project=project_id)
                new_employee.domain = domain
            self.instance = new_employee.save()
            return self.instance


class UpdateEmployeeSerializer(serializers.Serializer, RoleDomainValidation):
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(
        source='role.code', default=None, allow_blank=True)
    domain = serializers.CharField(
        source='domain.code', default=None, allow_blank=True)

    def update(self, instance, validated_data):
        project_id = self.context.get('project_id')
        employee = Employee.objects.get(
            user__email=instance, project=project_id)
        update_employee = employee
        if validated_data.get('role', {}).get('code') is not None:
            if(validated_data.get('role', {}).get('code') == ""):
                update_employee.role = None
            else:
                role = Role.objects.get(
                    code=validated_data.get('role', {}).get('code'), project=project_id)
                update_employee.role = role
        if validated_data.get('domain', {}).get('code') is not None:
            if(validated_data.get('domain', {}).get('code') == ""):
                update_employee.domain = None
            else:
                domain = Domain.objects.get(
                    code=validated_data.get('domain', {}).get('code'), project=project_id)
                update_employee.domain = domain
        update_employee.save()
        return update_employee


class UpdateEmployeeStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['status']


class CreateDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["name", "code"]

    def validate_code(self, code):
        project_id = self.context.get('project_id')
        if Domain.objects.filter(project=project_id, code=code).exists():
            raise serializers.ValidationError("domain Code already exists")
        return code

    def create(self, validated_data):
        project_instance = Project.objects.get(id=self.context["project_id"])
        new_doamin = Domain()
        new_doamin.code = validated_data['code']
        new_doamin.name = validated_data['name']
        new_doamin.project = project_instance
        new_doamin.save()
        return new_doamin


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name', 'code']

    def validate(self, data):
        if Role.objects.filter(project=self.context["project_id"], code=data['code']).exists():
            raise serializers.ValidationError("role code already exists")
        return data

    def create(self, validated_data):
        project_instance = Project.objects.get(id=self.context["project_id"])
        new_role = Role()
        new_role.code = validated_data['code']
        new_role.name = validated_data['name']
        new_role.project = project_instance
        new_role.save()
        return new_role


class CreateLeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['code', 'name', 'hours', 'days']

    def validate_code(self, code):
        project_id = self.context.get('project_id')
        if LeaveType.objects.filter(project=project_id, code=code).exists():
            raise serializers.ValidationError("leave type code already exists")
        return code

    def create(self, validated_data):
        project_instance = Project.objects.get(id=self.context["project_id"])
        new_leave_type = LeaveType()
        new_leave_type.code = validated_data['code']
        new_leave_type.name = validated_data['name']
        new_leave_type.hours = validated_data['hours']
        new_leave_type.days = validated_data['days']
        new_leave_type.project = project_instance
        new_leave_type.save()
        return new_leave_type


class CreateLeaveDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDuration
        fields = ['code', 'name', 'hours', 'status']

    def validate_code(self, code):
        if LeaveDuration.objects.filter(project=self.context["project_id"], code=code).exists():
            raise serializers.ValidationError(
                "leave duration Code already exists")
        return code

    def create(self, validated_data):
        project_instance = Project.objects.get(id=self.context["project_id"])
        new_leave_duration = LeaveDuration()
        new_leave_duration.code = validated_data['code']
        new_leave_duration.name = validated_data['name']
        new_leave_duration.hours = validated_data['hours']
        new_leave_duration.project = project_instance
        new_leave_duration.save()
        return new_leave_duration


class RoleAccessListField(serializers.RelatedField):
    def to_representation(self, value):
        return value.access_code.code


class AdminRoleAccessSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='access_code.code')
    name = serializers.CharField(source='access_code.name')

    class Meta:
        model = ProjectAdminRoleAccess
        fields = ["code", "name"]


class SimpleAdminRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAdminRole
        fields = ['id', 'code', 'name']


class AdminRoleSerializer(serializers.ModelSerializer):
    is_delete = serializers.BooleanField(read_only=True)
    manage_access = serializers.BooleanField(read_only=True)
    access = AdminRoleAccessSerializer(
        source='project_admin_access', many=True, read_only=True)

    class Meta:
        model = ProjectAdminRole
        fields = ['id', 'code', 'name', 'access', 'is_delete', 'manage_access']


class CreateAdminRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAdminRole
        fields = ['code', 'name']

    def validate(self, data):
        project_id = self.context.get("project_id")
        if ProjectAdminRole.objects.filter(code=data['code'], project=project_id).exists():
            raise serializers.ValidationError("Role already exists")
        return data

    def create(self, validated_data):
        project_id = self.context.get("project_id")
        project = Project.objects.get(id=project_id)
        new_project_admin_role = ProjectAdminRole()
        new_project_admin_role.name = validated_data.get('name')
        new_project_admin_role.code = validated_data.get('code')
        new_project_admin_role.project = project
        new_project_admin_role.save()
        return new_project_admin_role


class CreateAdminSerializer(serializers.Serializer, AdminRoleValidation):
    email = serializers.EmailField()
    role = serializers.CharField(default=None, allow_blank=True)

    def validate_email(self, email):
        project_id = self.context.get("project_id")
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("given email not found")
        if ProjectAdmin.objects.filter(project=project_id, user__email=email).exists():
            raise serializers.ValidationError("given email already a admin")
        if ProjectOwner.objects.filter(project=project_id, user__email=email).exists():
            raise serializers.ValidationError(
                "given email already a owner of this project")
        return email

    def save(self, **kwargs):
        with transaction.atomic():
            # adding new admin
            project_id = self.context.get("project_id")
            validated_data = self.validated_data
            new_admin = ProjectAdmin()
            new_admin.project = Project.objects.get(pk=project_id)
            new_admin.user = User.objects.get(
                email=validated_data.get("email"))
            if validated_data.get('role') is not None:
                new_admin.role = ProjectAdminRole.objects.get(
                    code=validated_data.get('role'), project=project_id)
            new_admin.save()


class UpdateAdminSerializer(serializers.ModelSerializer, AdminRoleValidation):
    role = serializers.CharField(source='role.code')

    class Meta:
        model = ProjectAdmin
        fields = ['role']

    def update(self, instance, validated_data):
        project_id = self.context.get("project_id")
        instance.role = ProjectAdminRole.objects.get(project=project_id,
                                                     code=validated_data['role']['code'])
        instance.save()
        return instance


class ProjectAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAdminAccess
        fields = ["id", "code", "name"]


class ProjectAdminAccessSerializer(serializers.Serializer):
    access_code_list = serializers.ListSerializer(
        child=serializers.CharField(), allow_empty=False)

    def validate_access_code_list(self, access_code_list):
        if ProjectAdminAccess.objects.filter(code__in=access_code_list).count() != len(access_code_list):
            raise serializers.ValidationError(
                "some access codes present in the list are not available in DB")
        return access_code_list

    def validate(self, data):
        role_id = self.context.get("role_id")
        project_id = self.context.get("project_id")
        if not ProjectAdminRole.objects.filter(project=project_id, id=role_id).exists():
            raise serializers.ValidationError(
                "role not found")
        return data

    def save(self, **kwargs):
        role_id = self.context.get("role_id")
        project_id = self.context.get("project_id")
        validated_data = self.validated_data
        role = ProjectAdminRole.objects.get(id=role_id, project=project_id)
        existing_access = ProjectAdminRoleAccess.objects.filter(role=role)
        existing_access.delete()

        new_access_list = ProjectAdminAccess.objects.filter(
            code__in=validated_data.get("access_code_list"))

        new_admin_access_list = [ProjectAdminRoleAccess(
            role=role, access_code=access_instance) for access_instance in new_access_list]
        self.instance = ProjectAdminRoleAccess.objects.bulk_create(
            new_admin_access_list)
        return self.instance


class ProjectOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOwner
        fields = ['id']


class ProjectAdminSerializer(serializers.ModelSerializer):
    role = AdminRoleSerializer()

    class Meta:
        model = ProjectAdmin
        fields = ['id', 'role']


class SimpleAdminSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    name = serializers.EmailField(source='user.username')

    class Meta:
        model = ProjectAdmin
        fields = ['id', 'email', 'name']


class AdminSerializer(serializers.ModelSerializer):
    is_delete = serializers.BooleanField(read_only=True)
    email = serializers.EmailField(source='user.email')
    name = serializers.EmailField(source='user.username')
    role = serializers.CharField(source='role.code', default=None)

    class Meta:
        model = ProjectAdmin
        fields = ['id', 'email', 'name', 'role', 'is_delete']
