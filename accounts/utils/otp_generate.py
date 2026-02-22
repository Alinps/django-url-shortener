from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from accounts.models import  OTPVerification
import secrets

def generate_otp(user):
    code = str(secrets.randbelow(900000) + 100000)

    expiry = timezone.now() + timedelta(
        seconds=settings.OTP_EXPIRY_SECONDS
    )

    # Delete old unused OTPs
    OTPVerification.objects.filter(
        user=user,
        is_used=False
    ).delete()

    OTPVerification.objects.create(
        user=user,
        code=code,
        expires_at=expiry
    )

    return code