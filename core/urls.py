from django.urls import path
from django.views.generic import TemplateView
urlpatterns = [
    # not-verified
    path('', TemplateView.as_view(template_name='core/index.html'))
]
