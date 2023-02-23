from rest_framework import permissions
from .models import ModuleAccess


class hasModulePermission(permissions.BasePermission):
    def __init__(self, access_code):
        self.access_code = access_code

    def has_permission(self, request, view):
        try:
            ModuleAccess.objects.get(
                user=request.user, module__code=self.access_code)
            return True
        except:
            return False
