from django.core.cache import cache
from django.conf import settings

def check_register_rate_limit(ip):
    key = f"register_ip:{ip}"
    count = cache.get(key)

    if count is None:
        cache.set(key,1,timeout = settings.REGISTER_RATE_WINDOW)
    elif count >= settings.REGISTER_RATE_LIMIT:
        return False
    else:
        cache.incr(key)
    return True
