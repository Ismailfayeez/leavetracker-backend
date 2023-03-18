from cgitb import lookup
from django.urls import path
from . import views
from rest_framework_nested import routers
urls = [

    path('account-preference', views.EmployeeAccountPreference.as_view()),
    path('current-fy/', views.FinancialYear.as_view()),
    path('my-fy-list/', views.FinancialYearList.as_view()),
    path('my-groups-report/', views.MyGroupsReport.as_view()),
    path('all-groups-report/', views.AllGroupsReport.as_view()),
    path('all-groups-report-excel/', views.AllGroupsExcelReport.as_view()),
]
router = routers.DefaultRouter()
router.register('my-accounts', views.MyAccountsViewSet, basename='my-accounts')
router.register('employee', views.EmployeeViewSet, basename='employees')
router.register('role', views.RoleViewSet, basename='role')
router.register('domain', views.DomainViewSet, basename='domain')
router.register('leave-type', views.LeaveTypeViewset,
                basename='leave-type')
router.register('leave-duration', views.LeaveDurationViewset,
                basename='leave-duration')
router.register('approver', views.ApproverViewSet, basename='approvers')
router.register('request', views.LeaveRequestViewSet, basename='requests')
router.register('approval', views.ApprovalViewSet, basename='approvals')
router.register('absentees', views.AbsenteesViewSet, basename='absentees')
router.register('groups-leave-count',
                views.GroupsLeaveCountViewSet, basename='groups-leave-count')
router.register('leave-balance', views.LeaveBalanceViewSet,
                basename='leave-balance')
router.register('team-analysis', views.TeamAnalysisViewSet,
                basename='team-analysis')
router.register('my-team', views.MyTeamViewSet, basename='my-team')
router.register('all-team', views.AllTeamViewSet, basename='all-team')
router.register('subscribed-team', views.SubscribedTeamViewSet,
                basename='subscribed-teams')
router.register('announcement', views.AnnouncementViewSet,
                basename='my-announcement')

# leave request routes
leaverequest_router = routers.NestedSimpleRouter(
    router, 'request', lookup='request'
)
leaverequest_router.register(
    'leave-dates', views.LeaveDatesViewSet, basename='leave-dates'
)
leaverequest_router.register(
    'approval-status', views.ApprovalInfoViewSet, basename='approval-info'
)

# approval routes
approval_router = routers.NestedSimpleRouter(
    router, 'approval', lookup='approval'
)
approval_router.register(
    'approval-status', views.LeaveApprovalInfoViewSet, basename='approval-info'
)


# my team routes
myteam_member_router = routers.NestedSimpleRouter(
    router, 'my-team', lookup='myteam')
myteam_member_router.register(
    'member', views.MyTeamMemberViewSet, basename='team-member')

# all team routes
allteam_member_router = routers.NestedSimpleRouter(
    router, 'all-team', lookup='allteam')
allteam_member_router.register(
    'member', views.AllTeamMemberViewSet, basename='team-member')


# team analysis routes
teamanalysis_router = routers.NestedSimpleRouter(
    router, 'team-analysis', lookup='teamanalysis'
)
teamanalysis_router.register(
    'member', views.TeamAnalysisMembersViewSet, basename='team-analysis-member')


urlpatterns = router.urls+myteam_member_router.urls + allteam_member_router.urls + \
    leaverequest_router.urls+teamanalysis_router.urls+urls+approval_router.urls
