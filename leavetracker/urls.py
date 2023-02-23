from cgitb import lookup
from django.urls import path
from . import views
from rest_framework_nested import routers
urls = [

    path('account-preference', views.EmployeeAccountPreference.as_view()),
    # verification-done
    path('current-fy/', views.FinancialYear.as_view()),
    # verification-done
    path('my-fy-list/', views.FinancialYearList.as_view()),
]
router = routers.DefaultRouter()
router.register('employee', views.EmployeeViewSet, basename='employees')
router.register('role', views.RoleViewSet, basename='role')
# not-verified
router.register('domain', views.DomainViewSet, basename='domain')
# not-verified
router.register('leave-type', views.LeaveTypeViewset,
                basename='leave-type')
# not-verified
router.register('leave-duration', views.LeaveDurationViewset,
                basename='leave-duration')
# not-verified
router.register('my-accounts', views.MyAccountsViewSet, basename='my-accounts')
# not-verified
router.register('approver', views.ApproverViewSet, basename='approvers')
# not-verified
router.register('request', views.LeaveRequestViewSet, basename='requests')
# not-verified
router.register('approval', views.ApprovalViewSet, basename='approvals')
# not-verified
router.register('graph', views.GraphViewSet, basename='graphs')
# verification-done
router.register('leave-balance', views.LeaveBalanceViewSet,
                basename='leave-balance')
# not-verified
router.register('team-analysis', views.TeamAnalysisViewSet,
                basename='team-analysis')
# not-verified
router.register('my-team', views.MyTeamViewSet, basename='my-team')
# not-verified
router.register('all-team', views.AllTeamViewSet, basename='all-team')
# not-verified
router.register('subscribed-team', views.SubscribedTeamViewSet,
                basename='subscribed-teams')
# not-verified
router.register('absentees', views.AbsenteesViewSet, basename='absentees')

# leave request routes
# not-verified
leaverequest_router = routers.NestedSimpleRouter(
    router, 'request', lookup='request'
)
# not-verified
leaverequest_router.register(
    'leave-dates', views.LeaveDatesViewSet, basename='leave-dates'
)
# not-verified
leaverequest_router.register(
    'approval-status', views.ApprovalInfoViewSet, basename='approval-info'
)

# approval routes
# not-verified
approval_router = routers.NestedSimpleRouter(
    router, 'approval', lookup='approval'
)
# not-verified
approval_router.register(
    'approval-status', views.LeaveApprovalInfoViewSet, basename='approval-info'
)


# my team routes
# not-verified
myteammember_router = routers.NestedSimpleRouter(
    router, 'my-team', lookup='myteam')
# not-verified
myteammember_router.register(
    'member', views.MyTeamMemberViewSet, basename='team-member')

# all team routes
# not-verified
allteammember_router = routers.NestedSimpleRouter(
    router, 'all-team', lookup='allteam')
# not-verified
allteammember_router.register(
    'member', views.AllTeamMemberViewSet, basename='team-member')


# team analysis routes
# not-verified
teamanalysis_router = routers.NestedSimpleRouter(
    router, 'team-analysis', lookup='teamanalysis'
)
# not-verified
teamanalysis_router.register(
    'member', views.TeamAnalysisMembersViewSet, basename='team-analysis-member')


urlpatterns = router.urls+myteammember_router.urls + allteammember_router.urls + \
    leaverequest_router.urls+teamanalysis_router.urls+urls+approval_router.urls
