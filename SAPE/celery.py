import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "SAPE.settings.prod"))

app = Celery("SAPE")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "atualizar-noticias-a-cada-1h": {
        "task": "aplicativo.tasks.atualizar_noticias_task",
        "schedule": crontab(minute=0),  # todo início de hora
    }
}