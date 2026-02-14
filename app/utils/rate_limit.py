from django.conf import settings
from django.core.cache import cache

def check_rate_limit(ip):

    key = f"rate_limit:{ip}"

    current = cache.get(key)

    if current is None:
        # First request
        cache.set(key,1,timeout=settings.REDIRECT_RATE_WINDOW)
        return True

    if current >= settings.REDIRECT_RATE_LIMIT:
        return False

    cache.incr(key)
    return True
