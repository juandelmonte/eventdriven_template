import os
import json
from celery import Celery
from pathlib import Path

# Load config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')
with open(CONFIG_FILE) as config_file:
    CONFIG = json.load(config_file)

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoproject.settings')

app = Celery('djangoproject')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
