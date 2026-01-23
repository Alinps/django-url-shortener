import string
import random
from django.core.mail import send_mail
from django.conf import settings

def short_code_generator(length=6):
    short_list=[]
    chars=string.ascii_letters+string.digits
    for _ in range(length):
        short_list.append(random.choice(chars))
    return ''.join(short_list)


def generate_otp():
    return str(random.randint(100000,999999))


def send_reset_otp(email,otp):
    send_mail(
        subject="Password Reset OTP",
        message=f"Your OTP for password reset is {otp}. It is valid for 5 minutes",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )