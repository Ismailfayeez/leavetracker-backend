"""leave_tracker_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import core.views
from rest_framework_nested import routers

router = routers.DefaultRouter()


router.register('auth/all-users',
                core.views.UsersViewSet, basename='all-users')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('leavetracker/', include('leavetracker.urls')),
    path('project/', include('project.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('auth/timezone', core.views.TimeZone.as_view()),
    path('auth/country', core.views.Country.as_view()),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]+router.urls
