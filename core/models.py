from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=12)
    country = models.CharField(max_length=2)
    timezone = models.CharField(max_length=100)
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'country', 'timezone']


class Module(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)


class ModuleAccess(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='module_access')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['user', 'module', ]]
