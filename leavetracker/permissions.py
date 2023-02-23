from rest_framework import permissions
from leavetracker.models import Employee, LTAccountPreference, RoleAccess
from rest_framework.permissions import IsAuthenticated


class IsEmployee(permissions.BasePermission):
    message = 'employee account/project not found or account preference may not be added.'
    error = 'no-emp-acct-found'

    def get_employee(self, user):
        try:
            preference = LTAccountPreference.objects.get(user=user)
            project = preference.project
            employee = Employee.objects.get(user=user,
                                            project=project,
                                            status="A", project__status='A')

            return employee
        except:
            return None

    def has_permission(self, request, view):
        return self.get_employee(request.user)


class IsEmployeeHasPermission(IsEmployee):
    def __init__(self, access_code):
        self.access_code = access_code

    def has_permission(self, request, view):
        employee = self.get_employee(request.user)
        if (employee and employee.role) is not None:
            try:
                role_access = RoleAccess.objects.get(
                    role=employee.role, role__project=employee.project, access__code=self.access_code)
                return role_access
            except:
                pass
        return None
