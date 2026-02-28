"""
WSGI config for urlshortner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from prometheus_client import multiprocess,CollectorRegistry
import urlshortner.tracing

from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urlshortner.settings')

application = get_wsgi_application()
DjangoInstrumentor().instrument()
RedisInstrumentor().instrument()

if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
