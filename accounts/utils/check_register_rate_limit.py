from django.core.cache import cache
from django.conf import settings
from app.metrics import rate_limit_trigger_total


def check_register_rate_limit(ip):
    key = f"register_ip:{ip}"
    count = cache.get(key)

    if count is None:
        cache.set(key,1,timeout = settings.REGISTER_RATE_WINDOW)
    elif count >= settings.REGISTER_RATE_LIMIT:
        rate_limit_trigger_total.inc()
        return False
    else:
        counter = cache.incr(key)
        print("register counter: ",counter)
    return True
