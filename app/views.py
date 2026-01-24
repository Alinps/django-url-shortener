from django.db.utils import DataError
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render,redirect
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from .forms import SignUp,login_form
from .utils import short_code_generator
from .models import ShortURL
from django.db.models import F
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
from django.contrib.auth.models import User
from .utils import generate_otp,send_reset_otp
from .models import PasswordResetOTP
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import never_cache

# Create your views here.


def auth_choice(request):
    return render(request,'auth_choice.html')


def landingpage(request):
    return render(request,'landingpage.html')


def register(request):
    if request.method=='POST':
        form=SignUp(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:   
        form=SignUp()
    return render(request,'signup.html',{'form':form})

def login_user(request):
    if request.method=='POST':
        form=login_form(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(user)
            login(request,user)
            print(request.POST)
            return redirect('home')
    else:
        form=login_form()
    return render(request,'login.html',{'form':form})

# @login_required
# def home_page(request):
#     return render(request,'home.html')


@never_cache
@login_required(login_url='/login/')
@csrf_protect
def logout_user(request):
    if request.method=='POST':
        logout(request)
        return redirect('login')
    return render(request,'logout.html')

@never_cache
@login_required
@csrf_protect
def home_page(request):
    if request.method == 'POST':
        original_url = request.POST.get("original_url")
        title = request.POST.get("title")
        short_code = short_code_generator()

        try:
            ShortURL.objects.create(
                user=request.user,
                original_url=original_url,
                short_code=short_code,
                title=title
            )
            messages.success(request, "URL shortened successfully")
            return redirect("list")

        except DataError:
            messages.error(
                request,
                "The URL is too long. Please enter a shorter or valid URL."
            )
            return redirect("home")   # ✅ FIX HERE

    return render(request, "home.html")

@never_cache
@login_required
def list_url(request):
    query=request.GET.get("q","")
    urls = ShortURL.objects.filter(user=request.user).order_by("-created_at")
    if query:
        urls=urls.filter(title__icontains=query)
    paginator = Paginator(urls, 10)  # 10 urls per page
    page_number = request.GET.get("page")
    url_qs = paginator.get_page(page_number)

    total_clicks=urls.aggregate(
        total=Sum("click_count")
    )["total"] or 0    #if no url Sum returns none, "or 0" prevents template crashes
    total_urls=urls.count()
    active_urls=urls.filter(is_active=True).count()
    disabled_urls=urls.filter(is_active=False).count()
    return render(request,"list.html",{
        "urls":url_qs,
        "total_clicks":total_clicks,
        "total_urls":total_urls,
        "active_urls":active_urls,
        "disabled_urls":disabled_urls
        })



#ajax search
# app/views.py
@login_required
def search_urls(request):
    query = request.GET.get("q", "").strip()

    urls = (
        ShortURL.objects
        .filter(user=request.user, title__icontains=query)
        .values(
            "id",
            "title",
            "original_url",
            "short_code",
            "click_count",
            "is_active",
        )
    )

    return JsonResponse({"results": list(urls)})




@login_required
def update_url(request,id):
    if request.method=="POST":
        data=json.loads(request.body)
        url=get_object_or_404(ShortURL,id=id,user=request.user)

        url.title=data["title"]
        url.original_url=data["original_url"]
        url.save()

        return JsonResponse({
            "success":True,
            "title":url.title,
            "original_url":url.original_url,
        })
    return None


# @never_cache
# @login_required
# def update_url(request,ids):
#     url_obj=get_object_or_404(ShortURL,id=ids,user=request.user)
#     if request.method=="POST":
#         new_url=request.POST.get("original_url")
#         new_status=request.POST.get("status")
#         new_title=request.POST.get("title")
#         url_obj.original_url=new_url
#         url_obj.is_active=new_status
#         url_obj.title=new_title
#         url_obj.save()
#         return redirect("list")
#     return render(request,"edit.html",{"url":url_obj})

# @never_cache
# @login_required
# def delete_url(request,ids):
#     url_obj=get_object_or_404(ShortURL,id=ids,user=request.user)
#     if request.method=='POST':
#         url_obj.delete()
#         return redirect("list")
#     return render(request,"delete.html",{'url':url_obj})

@login_required
def delete_url(request,id):
    if request.method=='POST':
        url=ShortURL.objects.filter(user=request.user)
        ShortURL.objects.filter(id=id).delete()
        return JsonResponse({
            "success":True,
            "total_urls":url.count(),
            "active_urls":url.filter(is_active=True).count(),
            "disabled_urls":url.filter(is_active=False).count()
        })
    return None


def redirect_url(request,short_code):
    url=get_object_or_404(ShortURL,short_code=short_code)
    if not url.is_active:
        raise Http404("This URL is disabled")
    url.click_count=F("click_count")+1   #Atomic increment, increment the value safely at the db level. This prevents race condition while multiple user click at a time
    url.save(update_fields=["click_count"])
    return redirect(url.original_url)


@login_required
def toggle_url_status(request,ids):
    url=get_object_or_404(ShortURL,id=ids,user=request.user)
    url.is_active=not url.is_active
    url.save(update_fields=["is_active"])
    return redirect("list")



def aboutus(request):
    return render(request,'about.html')


def forgot_password(request):
    if request.method=="POST":
        email=request.POST.get("email")
        if not User.objects.filter(email=email).exists():
            return render(request,"forgot_password.html",{
                "error":"No account found with this email"
            })
        otp=generate_otp()
        PasswordResetOTP.objects.create(
            email=email,
            otp=otp
        )
        send_reset_otp(email,otp)
        request.session["reset_email"]=email
        return redirect("verify_reset_otp")
    return render(request,"forgot_password.html")





#verify reset otp
def verify_reset_otp(request):
    if request.method=="POST":
        otp_input=request.POST.get("otp")
        new_password=request.POST.get("password")
        email=request.session.get("reset_email")

        otp_obj=get_object_or_404(
            PasswordResetOTP,
            email=email,
            otp=otp_input
        )
        if otp_obj.is_expired():
            otp_obj.delete()
            return render(request,"reset_password.html",{
                "error":"OTP expired"
            })
        user=User.objects.get(email=email)
        user.password=make_password(new_password)
        user.save()

        otp_obj.delete()
        del request.session["reset_email"]
        return redirect("login")
    return render(request,"reset_password.html")