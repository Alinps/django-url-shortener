from django.conf import settings
from django_redis import get_redis_connection
from redis.exceptions import RedisError
from app.utils.rate_limit_response import rate_limited_response
from app.metrics import rate_limit_trigger_total


class GlobalRateLimitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = settings.GLOBAL_RATE_LIMIT
        self.window = settings.GLOBAL_RATE_WINDOW
        self.redis = get_redis_connection("default")

    def __call__(self, request):

        ip = self.get_client_ip(request)
        key = f"global_rl:ip:{ip}"

        try:
            current = self.redis.incr(key)

            if current == 1:
                self.redis.expire(key, self.window)

            if current > self.limit:
                rate_limit_trigger_total.inc()
                return rate_limited_response(request, self.window)

        except RedisError:
            # Redis is down → fail open
            # Log if needed, but do NOT block request
            pass

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded:
            return x_forwarded.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")