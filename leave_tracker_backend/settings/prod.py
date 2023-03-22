from .common import *
import os
import dj_database_url
SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = False

ALLOWED_HOSTS = ['leave-tracker-backend.onrender.com']

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'https://leavetracker-frontend.vercel.app/',
)

DATABASES = {
    'default': dj_database_url.config()
}
