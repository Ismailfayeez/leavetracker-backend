from .common import *
import os
import dj_database_url
SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = False

ALLOWED_HOSTS = ['leave-tracker-backend.onrender.com']


DATABASES = {
    'default': dj_database_url.config()
}
