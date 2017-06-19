from celery import Celery
from Htweets2.models import Htweets2
from celery.schedules import crontab
import sys, os, django


sys.path.append("/home/hermes/Documents/Htweetprod2")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Htweetprod2.settings")
django.setup()

app = Celery('Htweetprod2')


@app.task
def delete_tweets():
    oldtweets = Htweets2.objects.all()
    oldtweets.delete()


CELERYBEAT_SCHEDULE = {
    "delete_tweeets_eachday": {
        'task': "tasks.delete_tweets",
        # Every 1 hour
        'schedule': 30.0,
        'args': (16, 16),
    },
}

app.conf.timezone = 'Europe/London'