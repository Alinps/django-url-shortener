from django.conf import settings
from django_redis import get_redis_connection
from app.utils.rate_limit_response import rate_limited_response


class GlobalRateLimitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = settings.GLOBAL_RATE_LIMIT
        self.window = settings.GLOBAL_RATE_WINDOW
        self.redis = get_redis_connection("default")  # Uses DB 1

    def __call__(self, request):

        ip = self.get_client_ip(request)

        key = f"global_rl:ip:{ip}"

        current = self.redis.incr(key)
        print("global rate count:",current)

        # Always refresh expiry to avoid orphan keys
        if current == 1:
            self.redis.expire(key, 60)

        if current > self.limit:
            return rate_limited_response(
                request,
                self.window
            )

        return self.get_response(request)

    def get_client_ip(self, request):
        """
        Trust X-Forwarded-For only if behind a trusted proxy.
        """
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded:
            return x_forwarded.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")