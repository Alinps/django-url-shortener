from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str, DjangoUnicodeDecodeError
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
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

            send_verification_email(request, user)

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
                messages.warning(request,
                                 "Your account is not activated. Please verify your email.")
                return redirect("resend_activation")
            login(request,user)
            return redirect('home')
    else:
        form=login_form()
    return render(request,'login.html',{'form':form})





def activate_account(request, uidb64, token):
    User = get_user_model()
    user = None

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
def resend_activation(request):

    if request.method == "POST":
        email = request.POST.get("email")

        user = User.objects.filter(email=email).first()

        # Always respond same way (security)

        if user and not user.is_active:

            cache_key = f"resend_activation:{email}"

            if cache.get(cache_key):
                messages.info(request,"Activation email already sent recently.")
                return redirect("login")

            send_verification_email(request,user)

            cache.set(cache_key,True,timeout=300)

        messages.success(request,
                         "If an inactive account exists, a new activation link has been sent.")
        return redirect("login")

    return render(request,"resend_activation.html")







def forgot_password(request):
    if request.method=="POST":
        email=request.POST.get("email")

        # Always respond same (prevent enumeration)
        user = User.objects.filter(email=email).first()

        if user:
            cooldown_key = f"reset_cooldown:{email}"

            if cache.get(cooldown_key):
                messages.info(request,"OTP already sent recently.")
                return redirect("forgot_password")

            otp = generate_otp()
            store_otp(email,otp)

            send_reset_otp(email,otp)

            cache.set(cooldown_key,True,timeout=settings.OTP_RESEND_COOLDOWN)

            request.session["reset_email"]=email

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

        result = verify_otp(email,otp_input)

        if result == "expired":
            return render(request,"reset_password.html",{"error":"OTP expired"})
        if result == "locked":
            return render(request,"reset_password.html",{"error":"Too many attempts. Try again later."})
        if result == "invalid":
            return render(request,"reset_password.html",{"error":"Invalid OTP"})

        user = User.objects.get(email=email)
        user.password=make_password(new_password)
        user.save(update_fields=["password"])

        del request.session["reset_email"]

        return redirect("login")

    return render(request,"reset_password.html")








@never_cache
@login_required
@csrf_protect
def logout_user(request):
    if request.method=='POST':
        logout(request)
        return redirect('login')
    return render(request,'logout.html')