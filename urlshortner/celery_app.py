import os
from celery import Celery

# Tell celery where Django settings live
os.environ.setdefault("DJANGO_SETTINGS_MODULE","urlshortner.settings")

# Create the celery app (name should match project)
app  = Celery("urlshortner")

# Load CELERY_* settings from Django setting.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()