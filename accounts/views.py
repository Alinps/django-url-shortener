from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str, DjangoUnicodeDecodeError
from django.shortcuts import redirect, render
from .tokens import email_verification_token
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .utils.verification_email import send_verification_email


def activate_account(request,uidb64,token):
    User = get_user_model()
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, ObjectDoesNotExist, DjangoUnicodeDecodeError):
        user = None

    if user and email_verification_token.check_token(user,token):
        user.is_active = True
        user.save()
        return redirect('login')
    return render(request,"activation_invalid.html")


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