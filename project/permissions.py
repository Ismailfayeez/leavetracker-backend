from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from .models import ProjectOwner, ProjectAdmin, ProjectAdminRoleAccess
from .query_methods import get_my_projects
from core.permissions import hasModulePermission
from core.constants import PERMISSION_ACCESS_CODE as MODULE_PERMISSION_CODE
from .constants import PERMISSION_ACCESS_CODE as PROJECT_PERMISSION_CODE


class IsProjectMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return get_my_projects(request.user, view.kwargs.get('project_pk'))


class IsProjectOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        project = get_my_projects(
            request.user, view.kwargs.get('project_pk'))
        if (project is not None and ProjectOwner.objects.filter(project=project, user=request.user).exists()):
            return True
        return False


class IsProjectMemberHasPermission(permissions.BasePermission):
    def __init__(self, access_code):
        self.access_code = access_code

    def has_permission(self, request, view):
        project = get_my_projects(
            request.user, view.kwargs.get('project_pk'))
        if project is None:
            return False
        try:
            project_owner = ProjectOwner.objects.get(
                project=project, user=request.user)
            return project_owner
        except:
            try:
                project_admin = ProjectAdmin.objects.get(
                    project=project, user=request.user)
                if project_admin.role is not None:
                    ProjectAdminRoleAccess.objects.get(
                        role=project_admin.role, access_code__code=self.access_code)
                    return True
            except:
                pass
        return False


def is_authenticated_user():
    return [IsAuthenticated()]


def is_user_has_module_permission(code):
    return [IsAuthenticated(), hasModulePermission(MODULE_PERMISSION_CODE[code])]


def is_user_project_member():
    return [IsAuthenticated(), IsProjectMember()]


def is_user_project_member_has_permission(code):
    return [IsAuthenticated(), IsProjectMemberHasPermission(PROJECT_PERMISSION_CODE[code])]
