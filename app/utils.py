import string
import random
from django.core.mail import send_mail
from django.conf import settings
import re

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

#custum shortcode validator


SHORT_CODE_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
RESERVED_CODES = {"admin", "login", "signup", "dashboard", "api"}

def is_valid_custom_code(code: str) -> bool:
    if not SHORT_CODE_REGEX.match(code):
        return False
    if code.lower() in RESERVED_CODES:
        return False
    return True



def detect_device_type(user_agent:str) -> str:
    if not user_agent:
        return "Unknown"
    ua=user_agent.lower()
    if "ipad" in  ua or "tablet" in ua:
        return "tablet"

    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    if "windows" in ua or "macintosh" in ua or "linux" in ua:
        return "desktop"
    return "unknown"

