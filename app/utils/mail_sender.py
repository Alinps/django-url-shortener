from django.conf import settings
from django.core.mail import send_mail

def send_reset_otp(email,otp):
    send_mail(
        subject="Password Reset OTP",
        message=f"Your OTP for password reset is {otp}. It is valid for 5 minutes",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )