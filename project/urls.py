from . import views
from rest_framework_nested import routers
from django.urls import path
from rest_framework_nested import routers

urls = [
    path('myprojects/<project_pk>/fy-month/',
         views.FYMonth.as_view()),

]
router = routers.DefaultRouter()
router.register('myprojects', views.ProjectViewSet, basename='project')
router.register('lt-access', views.LeaveTrackerAccessViewSet,
                basename='lt-access')
router.register('pt-access', views.ProjectAccessViewSet,
                basename='pt-access')

# nested routes
myprojects_router = routers.NestedSimpleRouter(
    router, 'myprojects', lookup='project')
myprojects_router.register(
    'employee', views.EmployeeViewSet, basename='employee')
myprojects_router.register(
    'role', views.RoleViewSet, basename='role')
myprojects_router.register(
    'domain', views.DomainViewSet, basename='domain')
myprojects_router.register(
    'leavetype', views.LeaveTypeViewSet, basename='leave-type')
myprojects_router.register(
    'leaveduration', views.LeaveDurationViewSet, basename='leave-duration')
myprojects_router.register(
    'admin', views.AdminViewSet, basename='admin')
myprojects_router.register(
    'admin-role', views.AdminRoleViewSet, basename='admin-role')

urlpatterns = router.urls+myprojects_router.urls+urls
