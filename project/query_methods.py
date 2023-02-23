from project.models import Project
from django.db.models import Q
from django.http import Http404


def get_my_projects(user, project_id=None):
    queryset = Project.objects.filter(
        Q(project_admin__user=user)
        |
        Q(project_owner__user=user), status='A'
    ).distinct('id')
    if project_id is not None:
        try:
            detail = queryset.get(id=project_id)
            return detail
        except:
            return None
    return queryset
