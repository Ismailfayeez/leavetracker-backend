from .models import User
from leavetracker.serializers import SimpleUserSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
import pytz
# Create your views here.


class UsersViewSet(ListModelMixin, GenericViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']
    serializer_class = SimpleUserSerializer

    def get_queryset(self):
        return User.objects.filter(
            is_active=True)


class Country(APIView):
    http_method_names = ['get']
    permission_classes = [AllowAny]

    def get(self, request):
        query_params = request.query_params
        param = query_params.get('search')
        countries = pytz.country_names
        countries_list = map(
            lambda x: {"value": x[0], "name": x[1]}, countries.items())
        result_list = list(countries_list)
        if param is not None:
            filtered_list = filter(
                lambda x: (param.lower() in x['name'].lower() or param.lower() in x['value'].lower()), result_list)
            result_list = filtered_list
        return Response(result_list)


class TimeZone(APIView):
    http_method_names = ['get']
    permission_classes = [AllowAny]

    def get(self, request):
        query_params = request.query_params
        country_code = query_params.get('country_code')
        response_data = pytz.country_timezones
        if country_code is not None:
            try:
                country_timezone = pytz.country_timezones[country_code.lower()]
                response_data = country_timezone
            except:
                raise Http404

        return Response(response_data)
