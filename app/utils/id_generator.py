from django_redis import get_redis_connection
from app.models import ShortURLCore

COUNTER_KEY = "short_url_counter"

def initialize_counter():
    """
    Initialize Redis counter from DB State.
    Used when Redis is empty or during deployment.
    """

    redis_conn = get_redis_connection("default")

    last = ShortURLCore.objects.all().order_by("-id").first()

    if last:
        redis_conn.set(COUNTER_KEY,last.id)
        return last.id
    else:
        redis_conn.set(COUNTER_KEY,0)
        return 0

def get_next_short_id():
    """
    Safe ID generator.
    Self-heals if Redis restarts.
    """

    redis_conn = get_redis_connection("default")

    # If counter missing (Redis restart), reinitialize
    if not redis_conn.exists(COUNTER_KEY):
        initialize_counter()
    return redis_conn.incr(COUNTER_KEY)