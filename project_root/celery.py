import os
from celery import Celery
from django.conf import settings
from kombu import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_root.settings')

app = Celery('project_root')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.task_queues = (
    Queue('celery', routing_key='celery'),
    Queue('generate_pdf', routing_key='generate_pdf'),
)
