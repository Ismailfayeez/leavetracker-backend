
from core.models import User
from rest_framework import serializers
from leavetracker.utils import calculate_overall_approval_status
from leavetracker.validations import BaseTeamValidation
from project.serializers import ProjectSerializer
from .models import Announcement, AnnouncementTeam, AnnouncementViewedEmployee, Access, Domain, Employee, Approver, EmployeeAccessList, FiscalYear, LeaveApproval, LeaveDate, LeaveDuration, LeaveRequest, LatestLeaveRequestNumber, LeaveType, Role, RoleAccess, Team, TeamMember, SubscribeTeam, EmployeeAccess
from django.db import transaction
from .services import generate_request_number
from project.query_methods import get_my_projects
from .queries import get_my_teams
import pytz
from datetime import datetime
from utilities.utils import get_current_date_in_user_timezone


class MyEmployeeAccountsSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name')

    class Meta:
        model = Employee
        fields = ["id", "project", "project_name"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number']


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username']


class EmployeeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.code', default=None)
    domain = serializers.CharField(source='domain.code', default=None)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_close = serializers.BooleanField(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'email', 'username', 'role',
                  'domain', 'is_close']


# used


class SimpleEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    name = serializers.CharField(source='user.username')

    class Meta:
        model = Employee
        fields = ['id', 'email', 'name', 'created_on']


class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = "__all__"

# used


class LeaveTrackerAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Access
        fields = "__all__"


class RoleAccessListField(serializers.RelatedField):
    def to_representation(self, value):
        return value.access.code


class SimpleRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "code"]


class SimpleDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "name", "code"]


class RoleAccessSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='access.name')
    code = serializers.CharField(source='access.code')

    class Meta:
        model = RoleAccess
        fields = ['code', 'name']


class RoleSerializer(serializers.ModelSerializer):
    is_delete = serializers.BooleanField(read_only=True)
    manage_access = serializers.BooleanField(read_only=True)
    access = RoleAccessSerializer(
        source='role_access', many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'is_delete', 'access', 'manage_access']


class CreateRoleAccessSerializer(serializers.Serializer):
    access_code_list = serializers.ListSerializer(
        child=serializers.CharField(), allow_empty=False)

    def validate(self, data):
        user_id = self.context.get("user_id")
        role_id = self.context.get("role_id")
        project_id = self.context["project_id"]
        get_my_projects(user_id, project_id)
        if not Role.objects.filter(project=project_id, id=role_id).exists():
            raise serializers.ValidationError(
                "role not available in the project")

        return data

    def validate_access_code_list(self, access_code_list):
        if Access.objects.filter(code__in=access_code_list).count() != len(access_code_list):
            raise serializers.ValidationError(
                "some access codes present in the list are not available in DB")
        return access_code_list

    def save(self, **kwargs):
        role_id = self.context.get("role_id")
        validated_data = self.validated_data
        role = Role.objects.get(id=role_id)
        existing_access = RoleAccess.objects.filter(
            role=role_id)
        existing_access.delete()
        new_access_list = Access.objects.filter(
            code__in=validated_data.get("access_code_list"))

        new_role_access_list = [RoleAccess(role=role,
                                           access=access_instance) for access_instance in new_access_list]
        self.instance = RoleAccess.objects.bulk_create(
            new_role_access_list)
        return self.instance


class SimpleLeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['code', 'name']


class LeaveTypeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display')
    is_close = serializers.BooleanField(read_only=True)

    class Meta:
        model = LeaveType
        fields = ['id', 'code', 'name', 'hours', 'days', 'status', 'is_close']


class SimpleLeaveDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDuration
        fields = ['code', 'name']


class LeaveDurationSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)
    is_close = serializers.BooleanField(read_only=True)

    class Meta:
        model = LeaveDuration
        fields = ['id', 'code', 'name', 'hours', 'status', 'is_close']

# used


class DomainSerializer(serializers.ModelSerializer):
    is_delete = serializers.BooleanField(read_only=True)

    class Meta:
        model = Domain
        fields = ["id", "name", "code", 'is_delete']

    # used


class ApproverSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source='approver.user.email')
    username = serializers.CharField(source='approver.user.username')

    class Meta:
        model = Approver
        fields = ['id', 'email', 'username']

# used


class ApproverListSerializer(serializers.ListSerializer):
    def validate(self, data):
        employee = self.context.get('employee')
        existing_approvers = Approver.objects.filter(
            employee__user=employee.user, employee__project=employee.project)
        validation_set = set()
        if not len(data)+existing_approvers.count() <= 3:
            raise serializers.ValidationError({
                'detail': 'user can only have maximum upto 3 approvers'
            })
        for item in data:
            if item["email"] in validation_set:
                raise serializers.ValidationError(
                    f"{item['email']} is repeated in the given list.Please modify again")
            else:
                validation_set.add(item["email"])

        return data


class CreateApproverSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        list_serializer_class = ApproverListSerializer

    def validate_email(self, email):
        employee = self.context.get('employee')
        approver = Employee.objects.filter(
            project=employee.project, user__email=email, status='A').first()

        if employee.user == email:
            raise serializers.ValidationError(
                f'approver email cannot be same as user email')

        if approver is None:
            raise serializers.ValidationError(
                f'{email} does not belongs to your organization')
        return email

    def validate(self, data):
        employee = self.context.get('employee')
        existing_approvers = Approver.objects.filter(
            employee__user=employee.user, employee__project=employee.project)
        if existing_approvers.filter(approver__user__email=data['email']).exists():
            raise serializers.ValidationError(
                f'''{data['email']} already added as approver''')
        return data

    def create(self, validated_data):
        with transaction.atomic():
            print(self.context.get('employee'), validated_data)
            employee = self.context.get('employee')
            new_approver = Approver(
                employee=employee, approver=Employee.objects.get(user__email=validated_data['email'], project=employee.project))
            new_approver.save()
            return new_approver

# used


class AccessListSerializer(serializers.RelatedField):
    def to_representation(self, value):
        if value is None:
            return []
        return value.access.code


class MyInfoSerializer(serializers.ModelSerializer):
    approvers = ApproverSerializer(many=True)
    email = serializers.EmailField(source="user.email")
    username = serializers.CharField(source='user.username')
    domain = DomainSerializer()
    role = RoleSerializer()
    project = ProjectSerializer()
    # access = AccessListSerializer(
    #     source=f'getattr(role, 'role_access', None)', many=True, read_only=True, default=[])

    class Meta:
        model = Employee
        fields = ['id', 'email', 'username', 'role',
                  'domain', 'approvers', 'project'
                  #    'access'
                  ]


class SimpleLeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['request_number', 'status']

# used


class LeaveDatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDate
        fields = ["date"]

# used


class LeaveRequestSerializer(serializers.ModelSerializer):
    leave_dates = serializers.SlugRelatedField(many=True,
                                               read_only=True,
                                               slug_field='date')
    type = SimpleLeaveTypeSerializer()
    duration = SimpleLeaveDurationSerializer()
    status = serializers.CharField(source='get_status_display')
    status_code = serializers.CharField(source='status')
    created_at = serializers.SerializerMethodField(
        method_name='get_created_at_local')
    is_delete = serializers.SerializerMethodField(method_name='get_is_delete')

    class Meta:
        model = LeaveRequest
        fields = ['id', 'request_number', 'status', 'status_code',
                  'duration', 'from_date', 'to_date', 'type', 'leave_dates', 'created_at', 'is_delete']

    def get_created_at_local(self, leave):
        user = self.context.get('user')
        date = leave.created_at
        if user.timezone is not None:
            date = date.astimezone(pytz.timezone(user.timezone))
        return date

    def get_is_delete(self, leave):
        user = self.context.get('user')
        current_date = get_current_date_in_user_timezone(user.timezone)
        if leave.status == 'P' and leave.from_date > current_date and leave.to_date > current_date:
            return True
        return False


# used


class CreateLeaveRequestSerializer(serializers.Serializer):
    type = serializers.CharField()
    duration = serializers.CharField()
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    leave_date_list = serializers.ListSerializer(
        child=serializers.DateField(), allow_empty=True)

    def validate_type(self, value):
        employee = self.context['employee']
        if not LeaveType.objects.filter(code=value, project=employee.project).exists():
            raise serializers.ValidationError(
                f'{value} is not a correct leave type')
        return value

    def validate_duration(self, value):
        employee = self.context['employee']
        if not LeaveDuration.objects.filter(code=value, project=employee.project).exists():
            raise serializers.ValidationError(
                f'{value} is not a correct leave duration')
        return value

    def validate_from_date(self, from_date):
        employee = self.context['employee']
        current_date = get_current_date_in_user_timezone(
            employee.user.timezone)
        if from_date < current_date:
            raise serializers.ValidationError(
                'Should not be less than current calendar date')
        return from_date

    def validate_to_date(self, to_date):
        employee = self.context['employee']
        current_date = get_current_date_in_user_timezone(
            employee.user.timezone)
        if to_date < current_date:
            raise serializers.ValidationError(
                'Should not be less than current calendar date')
        return to_date

    def validate_leave_date_list(self, leave_date_list):
        unique_list = set(leave_date_list)
        if len(unique_list) != len(leave_date_list):
            raise serializers.ValidationError(
                'some dates are repeated more than once.Please remove'
            )
        return leave_date_list

    def validate(self, data):
        employee = self.context['employee']

        if not Approver.objects.filter(employee=employee).exists():
            raise serializers.ValidationError(
                {"error": 'atleast one approver should be present'})

        if data['from_date'] > data["to_date"]:
            raise serializers.ValidationError({'error': 'FROM date should not be greater than TO date'}
                                              )

        if any([date for date in data['leave_date_list'] if date < data['from_date'] or date > data['to_date']]):
            raise serializers.ValidationError(
                {'some dates in the list are greater or lesser than from and to date'})
        leave_dates_queryset = LeaveDate.objects.filter(
            request_number__employee=employee, date__in=data['leave_date_list']).values('date')
        existing_leave_dates = [i['date'] for i in leave_dates_queryset]
        compared_dates = [
            i for i in data['leave_date_list'] if i in existing_leave_dates]
        if len(compared_dates) > 0:
            raise serializers.ValidationError(
                {'error': f'Leave request already raised for  {",".join(map(str,compared_dates))}'}
            )

        if any([date for date in data['leave_date_list'] if date < data['from_date'] or date > data['to_date']]):
            raise serializers.ValidationError(
                {'error': 'some dates in the list are greater or lesser than from and to date'})
        if not Approver.objects.filter(employee=employee).exists():
            raise serializers.ValidationError(
                {'error': 'No approver added.Please add atleast one approver'})

        return data

    def create(self, validated_data):
        with transaction.atomic():
            data = validated_data
            employee = self.context['employee']
            request_number = generate_request_number(employee.project)
# Creating leave request
            new_request = LeaveRequest()
            new_request.request_number = request_number
            new_request.from_date = data['from_date']
            new_request.to_date = data['to_date']
            new_request.type = LeaveType.objects.get(
                code=validated_data['type'], project=employee.project)
            new_request.duration = LeaveDuration.objects.get(
                code=validated_data['duration'], project=employee.project)
            new_request.employee = employee
            new_request.save()
# Creating leave dates
            leave_dates = [LeaveDate(request_number=new_request, date=date)
                           for date in validated_data['leave_date_list']]
            LeaveDate.objects.bulk_create(leave_dates)
# Creating Leave Approval
            approver_list = Approver.objects.filter(employee=employee)
            approval_list = [LeaveApproval(
                request_number=new_request, approver=approver_object.approver) for approver_object in approver_list]
            LeaveApproval.objects.bulk_create(approval_list)
            LatestLeaveRequestNumber.objects.update_or_create(
                project=employee.project, defaults={'request_id': request_number})
            return new_request

# used


class ApprovalSerializer(serializers.ModelSerializer):

    type = SimpleLeaveTypeSerializer(source='request_number.type')
    duration = SimpleLeaveDurationSerializer(source='request_number.duration')
    request_number = serializers.IntegerField(
        source='request_number.request_number')
    request_id = serializers.PrimaryKeyRelatedField(
        source='request_number', read_only=True)
    from_date = serializers.DateField(source='request_number.from_date')
    to_date = serializers.DateField(source='request_number.to_date')
    your_status = serializers.StringRelatedField(
        read_only=True, source="get_approver_status_display")
    your_status_code = serializers.CharField(
        read_only=True, source="approver_status")
    employee = SimpleEmployeeSerializer(source='request_number.employee')
    status = serializers.CharField(
        source='request_number.get_status_display')
    status_code = serializers.CharField(
        source='request_number.status')
    leave_dates = serializers.SlugRelatedField(source='request_number.leave_dates', many=True,
                                               read_only=True,
                                               slug_field='date')

    class Meta:
        model = LeaveApproval
        fields = ['id', 'your_status', 'your_status_code',
                  'request_number', 'request_id', 'employee', 'type',
                  'duration', 'from_date', 'to_date', 'status', 'status_code', 'leave_dates']

# used


class UpdateApprovalSerializer(serializers.ModelSerializer):
    status = serializers.StringRelatedField(
        read_only=True, source="get_approver_status_display")
    request_number = serializers.IntegerField(read_only=True,
                                              source='request_number.request_number')

    def validate(self, data):
        approval_id = self.context.get('approval_id')
        employee_id = self.context.get('employee_id')
        if not LeaveApproval.objects.filter(id=approval_id, approver=employee_id).exists():
            raise serializers.ValidationError(
                {"error: You are not an approver for this leave request"})
        leave = LeaveRequest.objects.filter(
            leave_approval__id=approval_id).first()
        if leave is None:
            raise serializers.ValidationError("leave is not available")
        requestor_current_date = get_current_date_in_user_timezone(
            leave.employee.user.timezone)
        if leave.from_date < requestor_current_date:
            raise serializers.ValidationError(
                {"message": "Cannot approve past dated leave"})
        return data

    def update(self, instance, validated_data):
        approval = LeaveApproval.objects.get(
            pk=instance.pk)
        approval.approver_status = validated_data['approver_status']
        approval.save()
        # updating leave request status
        approval_id = self.context.get('approval_id')
        status_queryset = LeaveApproval.objects.filter(
            request_number__leave_approval=approval_id)
        status_list = [
            approval.approver_status for approval in status_queryset]
        overall_status = calculate_overall_approval_status(status_list)
        leave_request_obj = LeaveRequest.objects.filter(
            leave_approval=approval_id).first()
        leave_request_obj.status = overall_status
        leave_request_obj.save()
        return approval

    class Meta:
        model = LeaveApproval
        fields = ['approver_status', 'request_number', 'status']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class SimpleTeamSerializer1(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'description']


class SimpleTeamSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'member_count']

# used


class SimpleAllTeamSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField()
    subscribed = serializers.BooleanField()
    enable_subscription = serializers.BooleanField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'member_count',
                  'subscribed', 'enable_subscription']


class SimpleTeamMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    is_contact = serializers.CharField(required=False, default="Y")


class ListTeamMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='employee.user.username')
    email = serializers.EmailField(source="employee.user.email")
    role = serializers.CharField(source='get_role_display')

    class Meta:
        model = TeamMember
        fields = ["id", "username", "email", "role", "is_contact"]

# used


class TeamMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source='employee.user.email', read_only=True)

    username = serializers.CharField(
        source='employee.user.username', read_only=True)
    allow_remove = serializers.SerializerMethodField(
        method_name='get_allow_remove')
    allow_make_as_admin = serializers.SerializerMethodField(
        method_name='get_allow_make_as_admin')
    allow_dismiss_as_admin = serializers.SerializerMethodField(
        method_name='get_dismiss_as_admin')

    class Meta:
        model = TeamMember
        fields = ['id', 'username', 'email', 'role',
                  'is_contact', 'allow_remove', 'allow_make_as_admin', 'allow_dismiss_as_admin']

    def get_allow_remove(self, team_member):
        is_user_team_admin = self.context.get('is_current_user_team_admin')
        employee = self.context.get('employee')
        if (is_user_team_admin and employee):
            if team_member.employee != employee:
                return True
        return False

    def get_allow_make_as_admin(self, team_member):
        is_user_team_admin = self.context.get('is_current_user_team_admin')
        employee = self.context.get('employee')
        if (is_user_team_admin and employee):
            if team_member.employee != employee:
                if team_member.role != 'A':
                    return True
        return False

    def get_dismiss_as_admin(self, team_member):
        is_user_team_admin = self.context.get('is_current_user_team_admin')
        employee = self.context.get('employee')
        if (is_user_team_admin and employee):
            if team_member.employee != employee:
                if team_member.role == 'A':
                    return True
        return False

# used


class RetrieveTeamSerializer(serializers.ModelSerializer):
    team_members = TeamMemberSerializer(many=True)
    created_by = serializers.EmailField(source='created_by.user')
    created_at = serializers.SerializerMethodField(
        method_name='created_at_local')
    modified_by = serializers.EmailField(
        source='modified_by.user', allow_null=True)
    modified_at = serializers.SerializerMethodField(
        method_name='modified_at_local')

    class Meta:
        model = Team
        fields = ['name', 'description', 'team_members',
                  'created_at', 'created_by', 'modified_at', 'modified_by']

    def created_at_local(self, team):
        user = self.context.get('user')
        date = team.created_at
        if user.timezone is not None:
            date = date.astimezone(pytz.timezone(user.timezone))
        return date

    def modified_at_local(self, team):
        user = self.context.get('user')
        date = team.modified_at
        if (user.timezone and date) is not None:
            date = date.astimezone(pytz.timezone(user.timezone))
        return date


class CreateTeamSerializer(serializers.ModelSerializer, BaseTeamValidation):
    team_members = serializers.ListSerializer(
        child=SimpleTeamMemberSerializer(), allow_empty=False)

    class Meta:
        model = Team
        fields = ['name', 'description', 'team_members']

    def validate_team_members(self, team_members):
        employee = self.context.get('employee')
        team_members_id = [member["email"] for member in team_members]
        team_members_employee = Employee.objects.filter(
            user__email__in=team_members_id, project=employee.project)
        if employee.user_id in team_members_id:
            raise serializers.ValidationError(
                "you cannot add yourself as a participant.Please remove your id")
        if len(team_members) != team_members_employee.count():
            raise serializers.ValidationError(
                "some employees in the given list doesn't belongs to this organization")

        if len(team_members_id) != len(set(team_members_employee)):
            raise serializers.ValidationError(
                "email id of the employees are repeated more than once")
        return team_members

    def create(self, validated_data):
        with transaction.atomic():
            employee = self.context.get('employee')
            new_team = Team.objects.create(
                name=validated_data['name'], description=validated_data['description'], created_by=employee, project=employee.project)
            new_team_member_list = []
            for member in validated_data["team_members"]:
                team_member = TeamMember()
                team_member.team = new_team
                team_member.employee = Employee.objects.get(
                    user__email=member["email"], project=employee.project)
                team_member.is_contact = member["is_contact"]
                if member["email"] == employee.user:
                    team_member.role = "A"
                else:
                    team_member.role = "P"
                new_team_member_list.append(team_member)
            group_creator = TeamMember(
                team=new_team, employee=employee, is_contact="Y", role="A")
            new_team_member_list.append(group_creator)
            TeamMember.objects.bulk_create(new_team_member_list)
            return new_team


class UpdateTeamSerializer(serializers.ModelSerializer, BaseTeamValidation):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description']

    def validate(self, data):
        is_user_team_admin = self.context.get('is_user_team_admin')
        if not is_user_team_admin:
            raise serializers.ValidationError('you are not an admin')
        return data

    def update(self, instance, validated_data):
        employee = self.context.get('employee')
        Team.objects.filter(
            pk=instance.pk).update(**validated_data, modified_at=datetime.now(pytz.UTC), modified_by=employee)
        updated_team = Team.objects.get(pk=instance.pk)
        return updated_team

# used


class CreateTeamMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role = serializers.CharField(required=False, default="P")
    is_contact = serializers.CharField(required=False, default="Y")

    class Meta:
        model = TeamMember
        fields = ['id', 'email', 'role', 'is_contact']

    def validate_email(self, email):
        team = Team.objects.get(pk=self.context['team_id'])
        employee = Employee.objects.filter(
            user__email=email, project_id=team.project_id).first()
        if employee is None:
            raise serializers.ValidationError(
                f'{email} does not belong to this organization')
        return email

    def validate(self, data):
        # validation team id
        team_id = self.context['team_id']
        employee = self.context.get('employee')
        get_my_teams(employee, team_id)

        if not TeamMember.objects.filter(employee=employee, team=team_id, role='A').exists():
            raise serializers.ValidationError(
                {"you are not an admin"})

        if TeamMember.objects.filter(employee__user__email=data['email'], team=team_id).exists():
            raise serializers.ValidationError(
                {"error": f'{data["email"]} already exists in this team'})
        return data

    def create(self, validated_data):
        team = Team.objects.get(pk=self.context['team_id'])
        new_team_member = Employee.objects.get(
            user__email=validated_data['email'], project_id=team.project_id)
        team = Team.objects.get(pk=self.context['team_id'])
        instance = TeamMember.objects.create(
            employee=new_team_member, role=validated_data['role'], is_contact=validated_data['is_contact'], team=team)
        SubscribeTeam.objects.filter(
            team=self.context['team_id'], employee=new_team_member).delete()
        return instance

# used


class UpdateTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['role', 'is_contact']

    def validate_role(self, role):
        team_member_id = self.context.get('team_member_id')
        team_member = TeamMember.objects.filter(id=team_member_id).first()
        if (team_member.role == 'A' and role == 'A') or (team_member.role == 'P' and role == 'P'):
            raise serializers.ValidationError(
                'requested role is same as team member existing role')
        return role

    def validate(self, data):
        if not data.get('role'):
            raise serializers.ValidationError('role status not found')
        is_current_user_team_admin = self.context.get(
            'is_current_user_team_admin')
        if not is_current_user_team_admin:
            raise serializers.ValidationError(
                "you are not an admin")

        return data
# used


class ListSubscribeTeamSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(source='team.id')
    name = serializers.CharField(source='team.name')
    description = serializers.CharField(source='team.description')

    class Meta:
        model = SubscribeTeam
        fields = ['id', 'team_id', 'name', 'description']

# used


class SubscribeTeamSerializer(serializers.Serializer):
    def validate(self, data):
        team_id = self.context.get("team_id")
        employee = self.context.get('employee')
        if not Team.objects.filter(project=employee.project, id=team_id).exists():
            raise serializers.ValidationError(
                'given team id does not belongs to this organization')
        if Team.objects.filter(project=employee.project, id=team_id, team_members__employee=employee).exists():
            raise serializers.ValidationError(
                'cannot subscribe your own team')
        return data

    def create(self, validated_data):
        team_id = self.context.get("team_id")
        employee = self.context.get('employee')
        subscribe = self.context.get('subscribe')
        team = Team.objects.filter(id=team_id).first()
        if(subscribe == True):
            if not SubscribeTeam.objects.filter(employee=employee, team=team).exists():
                SubscribeTeam.objects.create(employee=employee, team=team)
            return {"subscribed": True}
        else:
            if SubscribeTeam.objects.filter(employee=employee, team=team).exists():
                instance = SubscribeTeam.objects.filter(
                    employee=employee, team=team).first()
                instance.delete()
            return {"subscribed": False}


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscribeTeam
        fields = "__all__"


class AbsenteesTeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='employee.user.username')
    email = serializers.EmailField(source='employee.user.email')
    team = serializers.CharField(source='team.name')

    class Meta:
        model = TeamMember
        fields = ['name', 'email', 'employee', 'team']


class AbsenteesDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='employee.user.username')
    email = serializers.EmailField(source='employee.user.email')
    team = serializers.CharField(source='team.name')

    class Meta:
        model = TeamMember
        fields = ['name', 'email', 'employee', 'team']


class ListSerializer(serializers.Serializer):
    name = serializers.CharField()


class SubscribeEmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamMember
        fields = "__all__"


class GroupsLeaveCountSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='team.name')
    leave_count = serializers.IntegerField()

    class Meta:
        model = SubscribeTeam
        fields = ['name', 'leave_count']


class TeamAnalysisEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['employee']

# used


class TeamAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name']
# used


class TeamAnalysisMembersSerializer(serializers.ModelSerializer):
    leave_count = serializers.IntegerField()
    name = serializers.CharField(source='employee.user.username')
    email = serializers.EmailField(source='employee.user.email')

    class Meta:
        model = Team
        fields = ['name', 'email', 'leave_count']


class ApprovalInfoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='approver.user.username')
    status = serializers.CharField(source='get_approver_status_display')

    class Meta:
        model = LeaveApproval
        fields = ['name', 'status']

# used


class LeaveBalanceSerializer(serializers.ModelSerializer):

    leave_taken = serializers.IntegerField()
    balance = serializers.IntegerField()

    class Meta:
        model = LeaveType
        fields = ['code', 'name', 'leave_taken', 'balance']


class EmployeeList(serializers.ModelSerializer):
    name = serializers.CharField(source='access_code.name')
    code = serializers.CharField(source='access_code.code')

    class Meta:
        model = EmployeeAccess
        fields = ['code', 'name']


class CreateEmployeeList(serializers.Serializer):
    access_code_list = serializers.ListSerializer(
        child=serializers.CharField(), allow_empty=False)

    def validate(self, data):
        employee_id = self.context.get("employee_id")
        user_id = self.context.get("user_id")
        project_id = self.context.get("project_id")
        if not Employee.objects.filter(id=employee_id, project=project_id, user__email=user_id).exists:
            raise serializers.ValidationError(
                "employee not found")
        return data

    def validate_access_code_list(self, access_code_list):
        if EmployeeAccessList.objects.filter(code__in=access_code_list).count() != len(access_code_list):
            raise serializers.ValidationError(
                "some access codes present in the list are not available in DB")
        return access_code_list

    def save(self, **kwargs):
        employee_id = self.context.get("employee_id")
        validated_data = self.validated_data
        employee = Employee.objects.get(id=employee_id)
        existing_access = EmployeeAccess.objects.filter(
            employee_id=employee_id)
        existing_access.delete()
        new_access_list = EmployeeAccessList.objects.filter(
            code__in=validated_data.get("access_code_list"))

        new_admin_access_list = [EmployeeAccess(
            employee=employee, access_code=access_instance) for access_instance in new_access_list]
        self.instance = EmployeeAccess.objects.bulk_create(
            new_admin_access_list)
        return self.instance


class SimpleAnnouncementTeamSerializer(serializers.ModelSerializer):
    team_id = serializers.CharField(source='team.id')
    name = serializers.CharField(source='team.name')
    description = serializers.CharField(source='team.description')

    class Meta:
        model = AnnouncementTeam
        fields = ["name", 'description', 'team_id']


class AnnouncementSerializer(serializers.ModelSerializer):
    teams = SimpleAnnouncementTeamSerializer(
        source='announcement_team', many=True)
    priority = serializers.CharField(source='get_priority_display')

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'message', 'teams', 'priority', 'expiry_date']


class SimpleAnnouncementSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.user.username')
    priority = serializers.CharField(source='get_priority_display')
    viewed_by = serializers.SerializerMethodField(
        method_name='get_viewed_by_employee')

    def get_viewed_by_employee(self, announcement):
        employee = self.context.get("employee")
        print(employee, announcement)
        try:
            AnnouncementViewedEmployee.objects.get(
                employee=employee, announcement=announcement)
            return True
        except:
            return False

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'message',
                  'priority', 'expiry_date', 'created_by', 'viewed_by']


class CreateAnnouncementSerializer(serializers.Serializer):
    title = serializers.CharField()
    message = serializers.CharField()
    expiry_date = serializers.DateField()
    team_list = serializers.ListSerializer(
        child=serializers.CharField(), allow_empty=False)
    priority = serializers.CharField(required=False)

    def validate_title(self, title):
        return title

    def validate_expiry_date(self, expiry_date):
        employee = self.context.get('employee')
        current_date = get_current_date_in_user_timezone(
            employee.user.timezone)
        diff = expiry_date-current_date
        if expiry_date <= current_date:
            raise serializers.ValidationError(
                "expiry date cannot be less than current date")
        if diff.days >= 30:
            raise serializers.ValidationError(
                "expiry date cannot be greater than 30 days from current date")
        return expiry_date

    def validate_team_list(self, team_list):
        employee = self.context.get('employee')
        teams = Team.objects.filter(
            id__in=team_list, project=employee.project, team_members__employee=employee)
        if len(teams) != len(set(team_list)):
            raise serializers.ValidationError(
                "Announcement cannot be triggered for the groups that you not belong")
        return team_list

    def create(self, validated_data):
        employee = self.context.get('employee')
        team_queryset = Team.objects.filter(
            id__in=validated_data.get("team_list"))
        new_announcement = Announcement(title=validated_data.get(
            "title"), message=validated_data.get("message"), expiry_date=validated_data.get("expiry_date"),
            created_by=employee)
        if validated_data.get('priority') is not None:
            new_announcement.priority = validated_data.get('priority')
        new_announcement.save()
        new_announcement_team_list = [AnnouncementTeam(
            announcement=new_announcement, team=team) for team in team_queryset]
        AnnouncementTeam.objects.bulk_create(new_announcement_team_list)
        self.instance = new_announcement
        return self.instance
