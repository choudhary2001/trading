# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module for 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hedge.settings')

app = Celery('hedge')

# Using a string here means the worker does not have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Optional: Define a `ready` function to ensure Celery app is loaded
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Add periodic tasks here if needed
    pass