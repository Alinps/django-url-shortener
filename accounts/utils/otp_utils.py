import random
from django.core.cache import cache
from django.conf import settings
from accounts.models import OTPVerification


def generate_otp():
    return str(random.randint(100000,999999))

def store_otp(email,otp):
    otp_key = f"reset_otp:{email}"
    attempt_key = f"reset_otp_attempts:{email}"

    cache.set(otp_key,otp,timeout=settings.OTP_EXPIRY_SECONDS)
    cache.set(attempt_key,0,timeout=settings.OTP_EXPIRY_SECONDS)



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