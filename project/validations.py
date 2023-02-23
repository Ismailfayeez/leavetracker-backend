from leavetracker.models import Role, Domain
from .models import ProjectAdminRole
from .query_methods import get_my_projects
from rest_framework import serializers


class RoleDomainValidation():
    def validate_role(self, role):
        project_id = self.context.get('project_id')
        if role and not Role.objects.filter(project=project_id, code=role).exists():
            raise serializers.ValidationError('role Not found')
        return role

    def validate_domain(self, domain):
        project_id = self.context.get('project_id')
        if domain and not Domain.objects.filter(project=project_id, code=domain).exists():
            raise serializers.ValidationError('Domain Not found')
        return domain


class AdminRoleValidation():
    def validate_role(self, role):
        print(role)
        if not role:
            return None
        project_id = self.context.get("project_id")
        if not ProjectAdminRole.objects.filter(project=project_id, code=role).exists():
            raise serializers.ValidationError(
                "given role not present in the db")
        return role

    def validate(self, data):
        project_id = self.context.get('project_id')
        user_id = self.context.get('user_id')
        get_my_projects(user_id, project_id)
        return data
