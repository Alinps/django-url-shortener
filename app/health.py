from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django_redis import get_redis_connection
from redis.exceptions import RedisError
from urlshortner.celery_app import app
from celery.exceptions import CeleryError

def health_live(request):
    """
    Liveness probe.
    Only checks if Django process is running.
    """
    return JsonResponse({"status": "alive"}, status=200)


def health_ready(request):
    """
    Readiness probe.
    Checks DB and Redis connectivity.
    """

    status = {
        "database": "unknown",
        "redis": "unknown"
    }

    overall_status = 200

    # -----------------------
    # Check Database
    # -----------------------
    try:
        db_conn = connections["default"]
        db_conn.cursor()  # simple connection check
        status["database"] = "ok"
    except OperationalError:
        status["database"] = "down"
        overall_status = 503

    # -----------------------
    # Check Redis
    # -----------------------
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        status["redis"] = "ok"
    except RedisError:
        status["redis"] = "down"
        overall_status = 503

    # -----------------------
    # Check celery
    # -----------------------

    try:
        inspector = app.control.inspect(timeout=1)
        response = inspector.ping()

        if not response:
            raise Exception("No workers responded")

        status["celery"] = "ok"

    except Exception:
        status["celery"] = "down"
        overall_status = 503


    return JsonResponse(
        {
            "status": "ready" if overall_status == 200 else "not_ready",
            "services": status
        },
        status=overall_status
    )