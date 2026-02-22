from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str, DjangoUnicodeDecodeError
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from redis import RedisError

from accounts.forms import SignUp, login_form
from accounts.utils.mail_sender import send_reset_otp
from accounts.utils.otp_generate import generate_otp
from app.utils.rate_limit_response import rate_limited_response
from .tokens import email_verification_token
from django.contrib.auth import get_user_model, login,logout
from django.core.cache import cache
from .utils.check_login_rate_limit import check_login_rate_limit
from .utils.check_register_rate_limit import check_register_rate_limit
from .utils.otp_utils import store_otp,verify_otp
from .utils.verification_email import send_verification_email

from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from redis.exceptions import RedisError
import logging
logger = logging.getLogger(__name__)



def auth_choice(request):
    return render(request,'auth_choice.html')




def register(request):
    if request.method == 'POST':

        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip = x_forwarded.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        if not check_register_rate_limit(ip):
            return rate_limited_response(
                request,
                settings.REGISTER_RATE_WINDOW
            )
        form = SignUp(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            logger.info("user_registration_attempt", extra={
                "request_id": request.request_id,
            })

            send_verification_email(request, user)
            logger.info("user_activation_email_send_successfully", extra={
                "request_id": request.request_id,
            })

            return render(request, "verify_email_sent.html")
    else:
        form = SignUp()
    return render(request, 'signup.html', {'form': form})






def login_user(request):
    if request.method=='POST':

        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip = x_forwarded.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        email = request.POST.get("username") # using email login

        if not check_login_rate_limit(ip,email):
            return rate_limited_response(
                request,
                settings.LOGIN_RATE_WINDOW
            )


        form=login_form(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                logger.warning("user_account_is_inactive", extra={
                    "request_id": request.request_id,
                    "user_email": email
                })
                messages.warning(request,
                                 "Your account is not activated. Please verify your email.")
                return redirect("resend_activation")
            login(request,user)
            logger.info("user_login_attempt", extra={
                "request_id": request.request_id,
                "user_email": email
            })
            return redirect('home')
    else:
        form=login_form()
    return render(request,'login.html',{'form':form})





def activate_account(request, uidb64, token):
    User = get_user_model()
    user = None
    logger.info("user_initiated_activate_account", extra={
        "request_id": request.request_id,
    })

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError,DjangoUnicodeDecodeError, User.DoesNotExist):
        user = None

    if user is not None:

        # If already activated
        if user.is_active:
            return redirect("login")

        if email_verification_token.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return render(request, "activation_success.html")

    return render(request, "activation_invalid.html")



User = get_user_model()


COOLDOWN_SECONDS = 300  # or use settings value


def resend_activation(request):
    logger.info("user_requested_resend_activation_link", extra={
        "request_id": request.request_id,
    })

    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        # Always respond same way (prevent enumeration)
        if user and not user.is_active:

            cache_key = f"resend_activation:{email}"
            now = timezone.now()
            cooldown_active = False

            # -----------------------
            # 1️⃣ Try Redis cooldown
            # -----------------------
            try:
                cooldown_active = cache.get(cache_key)
            except RedisError:
                # Redis down → ignore and fallback to DB
                cooldown_active = False

            # -----------------------
            # 2️⃣ DB fallback cooldown
            # -----------------------
            if not cooldown_active and user.last_activation_sent_at:
                if now - user.last_activation_sent_at < timedelta(seconds=COOLDOWN_SECONDS):
                    cooldown_active = True

            if cooldown_active:
                messages.info(
                    request,
                    "Activation email already sent recently."
                )
                return redirect("login")

            # -----------------------
            # Send activation email
            # -----------------------
            send_verification_email(request, user)

            # -----------------------
            # Update Redis cooldown
            # -----------------------
            try:
                cache.set(cache_key, True, timeout=COOLDOWN_SECONDS)
            except RedisError:
                # Redis down → skip silently
                pass

            # -----------------------
            # Update DB fallback
            # -----------------------
            user.last_activation_sent_at = now
            user.save(update_fields=["last_activation_sent_at"])

        messages.success(
            request,
            "If an inactive account exists, a new activation link has been sent."
        )
        return redirect("login")

    return render(request, "resend_activation.html")






def forgot_password(request):
    if request.method=="POST":
        email=request.POST.get("email")
        logger.info("user_forgot_password_attempt", extra={
            "request_id": request.request_id,
            "user_email": email
        })

        # Always respond same (prevent enumeration)
        user = User.objects.filter(email=email).first()

        if user:
            cooldown_key = f"reset_cooldown:{email}"

            try:
                if cache.get(cooldown_key):
                    messages.info(request, "OTP already sent recently.")
                    return redirect("forgot_password")
            except RedisError:
                # Redis down → ignore cooldown
                pass

            otp = generate_otp(user)  # <-- pass user

            send_reset_otp(email, otp)

            try:
                cache.set(
                    cooldown_key,
                    True,
                    timeout=settings.OTP_RESEND_COOLDOWN
                )
            except RedisError:
                pass

            request.session["reset_email"] = email

        messages.success(request,
                         "If an account exists, an OTP has been sent.")
        return redirect("verify_reset_otp")
    return render(request,"forgot_password.html")








#verify reset otp
def verify_reset_otp(request):
    email = request.session.get("reset_email")
    if not email:
        return redirect("forgot_password")
    if request.method=="POST":
        otp_input = request.POST.get("otp")
        new_password = request.POST.get("password")

        user = User.objects.get(email=email)

        result = verify_otp(user, otp_input)

        if result == "expired":
            logger.warning("forgot_password_otp_expired", extra={
                "request_id": request.request_id,
                "user_email": email
            })
            return render(request,"reset_password.html",{"error":"OTP expired"})
        if result == "locked":
            logger.warning("reached_max_otp_validation", extra={
                "request_id": request.request_id,
                "user_email": email
            })
            return render(request,"reset_password.html",{"error":"Too many attempts. Try again later."})
        if result == "invalid":
            logger.info("forgot_password_otp_invalid_attempt", extra={
                "request_id": request.request_id,
                "user_email": email
            })
            return render(request,"reset_password.html",{"error":"Invalid OTP"})

        # user = User.objects.get(email=email)
        # user.password=make_password(new_password)
        # user.save(update_fields=["password"])
        #
        # del request.session["reset_email"]
        #
        # return redirect("login")

        if result == "valid":

            user.password = make_password(new_password)
            user.save(update_fields=["password"])
            del request.session["reset_email"]
            logger.info("forgot_password_attempt_success", extra={
                "request_id": request.request_id,
                "user_email": email
            })
            return redirect("login")

    return render(request,"reset_password.html")








@never_cache
@login_required
@csrf_protect
def logout_user(request):
    if request.method=='POST':
        logout(request)
        logger.info("user_attempt_logout", extra={
            "request_id": request.request_id,
        })
        return redirect('login')
    return render(request,'logout.html')