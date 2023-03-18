from . import views
from rest_framework_nested import routers
from django.urls import path
from rest_framework_nested import routers

urls = [
    path('myprojects/<project_pk>/fy-month/',
         views.FYMonth.as_view()),

]
router = routers.DefaultRouter()
# not-verified
router.register('myprojects', views.ProjectViewSet, basename='project')
# not-verified
router.register('lt-access', views.LeaveTrackerAccessViewSet,
                basename='lt-access')
# not-verified
router.register('pt-access', views.ProjectAccessViewSet,
                basename='pt-access')

# nested routes
myprojects_router = routers.NestedSimpleRouter(
    router, 'myprojects', lookup='project')
# not-verified
myprojects_router.register(
    'employee', views.EmployeeViewSet, basename='employee')
# not-verified
myprojects_router.register(
    'role', views.RoleViewSet, basename='role')
# not-verified
myprojects_router.register(
    'domain', views.DomainViewSet, basename='domain')
# not-verified
myprojects_router.register(
    'leavetype', views.LeaveTypeViewSet, basename='leave-type')
# not-verified
myprojects_router.register(
    'leaveduration', views.LeaveDurationViewSet, basename='leave-duration')
# not-verified
myprojects_router.register(
    'admin', views.AdminViewSet, basename='admin')
# not-verified
myprojects_router.register(
    'admin-role', views.AdminRoleViewSet, basename='admin-role')

urlpatterns = router.urls+myprojects_router.urls+urls
