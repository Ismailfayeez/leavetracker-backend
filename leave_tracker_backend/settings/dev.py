from .common import *

SECRET_KEY = 'django-insecure-%@2oaf&e9&o^)ik$05pla7-p215y%spkci3xj=v)995nk%v@!s'

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'leave_tracker',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': '1234'
    }
}
