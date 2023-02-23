from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from .models import ModuleAccess
import pytz
from .validations import UserInfoValidation


class ModuleAccessSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='module.code')
    name = serializers.CharField(source='module.name')

    class Meta:
        model = ModuleAccess
        fields = ['code', 'name']


class UserSerializer(BaseUserSerializer, serializers.ModelSerializer, UserInfoValidation):
    access = ModuleAccessSerializer(
        source='module_access', many=True, read_only=True)
    username = serializers.CharField()

    class Meta(BaseUserSerializer.Meta):
        fields = ['username', 'email', 'access', 'country', 'timezone']


class UserCreateSerializer(BaseUserCreateSerializer, UserInfoValidation):
    pass
