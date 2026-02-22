import random
from django.core.cache import cache
from django.conf import settings

from accounts.models import OTPVerification
from django.conf import settings

def generate_otp():
    return str(random.randint(100000,999999))

def store_otp(email,otp):
    otp_key = f"reset_otp:{email}"
    attempt_key = f"reset_otp_attempts:{email}"

    cache.set(otp_key,otp,timeout=settings.OTP_EXPIRY_SECONDS)
    cache.set(attempt_key,0,timeout=settings.OTP_EXPIRY_SECONDS)

# def verify_otp(email,otp_input):
#     otp_key = f"reset_otp:{email}"
#     attempt_key = f"reset_otp_attempts:{email}"
#
#     stored_otp = cache.get(otp_key)
#
#     if not stored_otp:
#         return "expired"
#
#     attempts = cache.get(attempt_key,0)
#     if attempts >= settings.OTP_MAX_ATTEMPTS:
#         cache.delete(otp_key)
#         cache.delete(attempt_key)
#         return "locked"
#
#     if otp_input != stored_otp:
#         cache.incr(attempt_key)
#         return "invalid"
#
#     # Correct OTP
#     cache.delete(otp_key)
#     cache.delete(attempt_key)
#     return "valid"


def verify_otp(user, input_code):
    try:
        otp = OTPVerification.objects.get(
            user=user,
            is_used=False
        )
    except OTPVerification.DoesNotExist:
        return "invalid"

    if otp.is_expired():
        otp.delete()
        return "expired"

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.delete()
        return "locked"

    if otp.code != input_code:
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        return "invalid"

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    return "valid"