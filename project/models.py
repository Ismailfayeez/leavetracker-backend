import uuid
from django.db import models
from django.conf import settings

from core.models import User
# Create your models here.


class Project(models.Model):
    PROJECT_ACTIVE = "A"
    PROJECT_INACTIVE = "I"
    PROJECT_STATUS = [
        (PROJECT_ACTIVE, 'active'), (PROJECT_INACTIVE, 'inactive')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    status = models.CharField(choices=PROJECT_STATUS,
                              default=PROJECT_ACTIVE, max_length=1)

    def __str__(self) -> str:
        return self.name


class ProjectInfo(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_created')
    modified_at = models.DateTimeField(
        auto_now=True, null=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_modified', null=True)


class ProjectOwner(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='project_owner')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='project_owner')

    class Meta:
        unique_together = [['project', 'user']]


class ProjectAdminRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    code = models.CharField(max_length=5)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class ProjectAdmin(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='project_admin')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='project_admin')
    role = models.ForeignKey(
        ProjectAdminRole, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = [['project', 'user', 'role']]


class ProjectAdminAccess(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, unique=True)


class ProjectAdminRoleAccess(models.Model):
    role = models.ForeignKey(
        ProjectAdminRole, on_delete=models.CASCADE, related_name="project_admin_access")
    access_code = models.ForeignKey(
        ProjectAdminAccess, on_delete=models.CASCADE, related_name="project_admin_access_code")

    class Meta:
        unique_together = [['role', 'access_code']]
