from django.utils import timezone
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

    print("Rate limit triggered for IP:",ip)
    print("REDIS KEY:", key)

    current= cache.incr(key)
    print("current count: ",current)
    return True


def check_create_rate_limit(ip,user_id):

    ip_key = f"create_rate_ip:{ip}"
    ip_count = cache.get(ip_key)

    if ip_count is None:
        cache.set(ip_key,1,timeout=settings.CREATE_RATE_WINDOW)
    elif ip_count >= settings.CREATE_RATE_LIMIT:
        return False
    else:
        cache.incr(ip_key)

    #------Per-user daily limit-----

    today = timezone.now().date()
    user_key = f"create_rate_user:{user_id}:{today}"
    user_count = cache.get(user_key)

    if user_count is None:

        now = timezone.now()

        tomorrow = now.date() + timezone.timedelta(days=1) # To mark time upto 24 hours

        midnight = timezone.make_aware(
            timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
        )

        seconds_until_midnight = int((midnight - now).total_seconds())

        cache.set(user_key,1,timeout=seconds_until_midnight)

    elif user_count >= settings.CREATE_DAILY_LIMIT:
        return False
    else:
        count=cache.incr(user_key)
        print("current count:",count)

    return True
