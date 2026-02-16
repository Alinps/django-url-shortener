from django.core.cache import cache
from django.conf import settings


def check_login_rate_limit(ip,email):

    ip_key = f"login_ip:{ip}"
    email_key = f"login_email:{email}"

    ip_count = cache.get(ip_key)
    email_count =cache.get(email_key)

    #IP check
    if ip_count  is None:
        cache.set(ip_key,1,timeout=settings.LOGIN_RATE_WINDOW)
    elif ip_count >= settings.LOGIN_RATE_LIMIT:
        return False
    else:
        cache.incr(ip_key)

    # Email check

    if email_count is None:
        cache.set(email_key,1, timeout = settings.LOGIN_RATE_WINDOW)
    elif email_count >= settings.LOGIN_RATE_LIMIT:
        return False
    else:
        cache.incr(email_key)

    return True