from rest_framework import permissions
from leavetracker.models import Employee, LTAccountPreference, RoleAccess
from rest_framework.permissions import IsAuthenticated
from .queries import get_employee


class IsEmployee(permissions.BasePermission):
    message = 'employee account/project not found or account preference may not be added.'
    error = 'no-emp-acct-found'

    def has_permission(self, request, view):
        try:
            return get_employee(request.user)
        except:
            return False


class IsEmployeeHasPermission(permissions.BasePermission):
    message = 'Employee does not have suitable permission'
    error = 'emp-perm-not-found'

    def __init__(self, access_code):
        self.access_code = access_code

    def has_permission(self, request, view):
        try:
            employee = get_employee(request.user)
            if (employee and employee.role) is not None:
                try:
                    role_access = RoleAccess.objects.get(
                        role=employee.role, role__project=employee.project, access__code=self.access_code)
                    return role_access
                except:
                    pass
        except:
            pass
        return False
