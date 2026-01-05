from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = ["*"]

STATIC_ROOT = os.path.join(BASE_DIR, '/app/static')

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_TIMEZONE = "America/Maceio"
CELERY_ENABLE_UTC = False
