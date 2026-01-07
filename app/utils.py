import string
import random
from django.core.mail import send_mail
from django.conf import settings

def short_code_generator(length=6):
    short_code=""
    chars=string.ascii_letters+string.digits
    i=0
    while(i<length):
        short_code+=random.choice(chars)
        i+=1
    return short_code

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