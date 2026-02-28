import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path
import urlshortner.tracing
from opentelemetry.instrumentation.celery import CeleryInstrumentor

CeleryInstrumentor().instrument()
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Tell celery where Django settings live
os.environ.setdefault("DJANGO_SETTINGS_MODULE","urlshortner.settings")

# Create the celery app (name should match project)
app  = Celery("urlshortner")

# Load CELERY_* settings from Django setting.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()