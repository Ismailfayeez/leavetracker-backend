from django.db import models
from django.conf import settings
from project.models import Project
import uuid
# Create your models here.


class LTAccountPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'project']]


class Domain(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=4)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [['code', 'project']]


class Role(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=4)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [['code', 'project']]


class Access(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.code


class RoleAccess(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="role_access")
    access = models.ForeignKey(Access, on_delete=models.CASCADE)


class Employee(models.Model):
    ACTIVE = 'A'
    CLOSED = 'C'
    INACTIVE = 'IN'
    status_choices = [(ACTIVE, 'active'), (CLOSED, 'closed'),
                      (INACTIVE, 'inactive')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee')
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    domain = models.ForeignKey(
        Domain, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=2, choices=status_choices, default=ACTIVE)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

    class Meta:
        unique_together = [['user', 'project']]


class Supervisor(models.Model):
    supervisor = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='supervisor_employees')
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name='supervisor')


class Approver(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='approvers')
    approver = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='approver_employees')

    class Meta:
        unique_together = [['employee', 'approver']]


class LeaveDuration(models.Model):
    ACTIVE = 'A'
    CLOSED = 'C'
    INACTIVE = 'IN'
    status_choices = [(ACTIVE, 'active'), (CLOSED, 'closed'),
                      (INACTIVE, 'inactive')]
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=15)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(
        max_length=2, choices=status_choices, default=ACTIVE)

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = [['code', 'project']]


class LeaveType(models.Model):
    ACTIVE = 'A'
    CLOSED = 'C'
    INACTIVE = 'IN'
    status_choices = [(ACTIVE, 'active'), (CLOSED, 'closed'),
                      (INACTIVE, 'inactive')]
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=20)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    days = models.IntegerField()
    status = models.CharField(
        max_length=2, choices=status_choices, default=ACTIVE)

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = [['project', 'code', ]]


class FiscalYear(models.Model):

    month = models.CharField(max_length=3)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='fiscal_year')

    class Meta:
        unique_together = [['project', 'month']]


class LeaveRequest(models.Model):
    REQUEST_STATUS_PENDING = 'P'
    REQUEST_STATUS_ACCEPTED = 'A'
    REQUEST_STATUS_REJECTED = 'R'
    REQUEST_STATUS_DELETED = 'D'
    REQUEST_STATUS_CANCELLED = 'C'
    REQUEST_STATUS_CHOICES = [
        (REQUEST_STATUS_PENDING, 'Pending'),
        (REQUEST_STATUS_ACCEPTED, 'Accepted'),
        (REQUEST_STATUS_DELETED, 'Deleted'),
        (REQUEST_STATUS_REJECTED, 'Rejected'),
        (REQUEST_STATUS_CANCELLED, "Cancelled")
    ]

    request_number = models.IntegerField()
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="leave_request")
    type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name='leave_request')
    duration = models.ForeignKey(LeaveDuration, on_delete=models.PROTECT)
    from_date = models.DateField()
    to_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(null=True)
    modified_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name="leave_request_modified_by")
    status = models.CharField(
        max_length=1, choices=REQUEST_STATUS_CHOICES, default=REQUEST_STATUS_PENDING)

    class Meta:
        unique_together = [['request_number', 'employee']]


class LeaveDate(models.Model):
    request_number = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE, related_name='leave_dates')
    date = models.DateField()

    class Meta:
        unique_together = [['request_number', 'date']]


class LatestLeaveRequestNumber(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    request_id = models.IntegerField()


class LeaveApproval(models.Model):
    APPROVER_REQUEST_STATUS_PENDING = 'P'
    APPROVER_REQUEST_STATUS_ACCEPTED = 'A'
    APPROVER_REQUEST_STATUS_REJECTED = 'R'
    APPROVER_REQUEST_STATUS_DELETED = 'D'
    APPROVER_REQUEST_STATUS_CANCELLED = 'C'

    APPROVER_REQUEST_STATUS_CHOICES = [
        (APPROVER_REQUEST_STATUS_PENDING, 'Pending'),
        (APPROVER_REQUEST_STATUS_ACCEPTED, 'Accepted'),
        (APPROVER_REQUEST_STATUS_DELETED, 'Deleted'),
        (APPROVER_REQUEST_STATUS_REJECTED, 'Rejected'),
        (APPROVER_REQUEST_STATUS_CANCELLED, 'Cancelled')
    ]
    request_number = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE, related_name='leave_approval')
    approver = models.ForeignKey(Employee, on_delete=models.PROTECT)
    approver_status = models.CharField(
        max_length=1, choices=APPROVER_REQUEST_STATUS_CHOICES, default=APPROVER_REQUEST_STATUS_PENDING)


class Team(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name='team_created_by')
    created_at = models.DateTimeField(
        auto_now_add=True)
    modified_at = models.DateTimeField(null=True)
    modified_by = models.ForeignKey(
        Employee, on_delete=models.PROTECT, null=True, related_name='team_modified_by')
    is_active = models.BooleanField(default=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class TeamMember(models.Model):
    PARTICIPANT = 'P'
    ADMIN = 'A'
    TEAM_ROLE = [
        (PARTICIPANT, 'participant'),
        (ADMIN, 'admin')]
    IS_CONTACT = [
        ('Y', 'yes'),
        ('N', 'no')
    ]

    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="team_members")
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='teams')
    role = models.CharField(
        max_length=1, choices=TEAM_ROLE, default=PARTICIPANT)
    is_contact = models.CharField(
        max_length=1, choices=IS_CONTACT, default='N')

    class Meta:
        unique_together = [['employee', 'team']]


class SubscribeTeam(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='subscribed_team_employee')
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='subscribed_teams')

    class Meta:
        unique_together = [['employee', 'team']]


class EmployeeAccessList(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=255, unique=True)


class EmployeeAccess(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    access_code = models.ForeignKey(
        EmployeeAccessList, on_delete=models.CASCADE)
