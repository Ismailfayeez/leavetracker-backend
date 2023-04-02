from django.contrib import admin
from core import models
from leavetracker import models as leavetracker_models
from project import models as project_models


@admin.register(models.ModuleAccess)
class ModuleAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', ]


@admin.register(leavetracker_models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'domain',
                    'project', 'status', 'created_on']
    list_editable = ['status']


@admin.register(leavetracker_models.Access)
class AccessAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


@admin.register(project_models.ProjectAdminAccess)
class ProjectAdminAccessAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


admin.site.register(models.User)
admin.site.register(models.Module)
admin.site.register(leavetracker_models.Team)
