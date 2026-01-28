from datetime import timedelta

from django.db.models.functions import TruncDate
from django.db.utils import DataError
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render,redirect
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from django.utils import timezone

from .forms import SignUp,login_form
from .utils import short_code_generator, is_valid_custom_code
from .models import ShortURL,ClickEvent
from django.db.models import F, Count
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
from django.contrib.auth.models import User
from .utils import generate_otp,send_reset_otp
from .models import PasswordResetOTP
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import never_cache
from django.db import DataError, IntegrityError
import traceback


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
        custom_code = request.POST.get("custom_code", "").strip()

        print("CUSTOM_CODE:", custom_code)

        # Decide short_code
        if custom_code:
            if not is_valid_custom_code(custom_code):
                messages.error(request, "Invalid short URL format")
                return redirect("home")

            if ShortURL.objects.filter(short_code__iexact=custom_code).exists():
                messages.error(request, "Short URL already exists")
                return redirect("home")

            short_code = custom_code
        else:
            while True:
                short_code = short_code_generator()
                if not ShortURL.objects.filter(short_code=short_code).exists():
                    break

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
            return redirect("home")
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
            "created_at"
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
        custom_code=data["custom_code"]
        if custom_code:
            if not is_valid_custom_code(custom_code):

                return JsonResponse({
                    "success":False,
                    "message":"Invalid Custom URL formal"
                })

            if ShortURL.objects.filter(short_code__iexact=custom_code).exists():

                return JsonResponse({
                    "sucess":False,
                    "message":"Custom URL already exists"
                })

            short_code = custom_code
        else:
            while True:
                short_code = short_code_generator()
                if not ShortURL.objects.filter(short_code=short_code).exists():
                    break
        url.short_code=short_code
        url.save()
        return JsonResponse({
            "success":True,
            "title":url.title,
            "original_url":url.original_url,
            "custom_url":url.short_code
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
    #store analytics event (details)
    ClickEvent.objects.create(
        short_url=url,
        user_agent=request.META.get("HTTP_USER_AGENT","")
    )
    return redirect(url.original_url)


@login_required
def toggle_url_status(request,ids):
    url=get_object_or_404(ShortURL,id=ids,user=request.user)
    url.is_active=not url.is_active
    url.save(update_fields=["is_active"])
    return redirect("list")

def toggle_url_ajax(request,id):
    if request.method == 'POST':
        url=get_object_or_404(ShortURL,id=id,user=request.user)
        url.is_active=not url.is_active
        url.save(update_fields=["is_active"])
        return JsonResponse({
        'status':url.is_active,
        'active_url':ShortURL.objects.filter(user=request.user,is_active=True).count(),
        'disabled_url':ShortURL.objects.filter(user=request.user, is_active=False).count()
        })




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


def url_click_stats(request,url_id):
    print(url_id)
    url=ShortURL.objects.get(id=url_id,user=request.user)
    total_clicks=ShortURL.objects.filter(user=request.user).aggregate(total=Sum("click_count"))["total"] or 0
    return JsonResponse({
        "click_count":url.click_count,
        "total_clicks":total_clicks
    })



@login_required
def dashboard_stats(request):
    urls = ShortURL.objects.filter(user=request.user)

    total_clicks = urls.aggregate(
        total=Sum("click_count")
    )["total"] or 0

    url_stats = {
        url.id: url.click_count
        for url in urls
    }

    return JsonResponse({
        "total_clicks": total_clicks,
        "urls": url_stats
    })

@login_required
def analytics_view(request,url_id):
    url=get_object_or_404(ShortURL,id=url_id,user=request.user)
    #Read range from query params
    range_params=request.GET.get("range","7")

    #decide the start date
    now=timezone.now()

    if range_params=="30":
        start_date=now-timedelta(days=30)
    elif range_params=="all":
        start_date=None
    else:
        start_date=now-timedelta(days=7)

    #base queryset
    clicks=ClickEvent.objects.filter(short_url=url)

    #Apply date filer if needed
    if start_date:
        clicks=clicks.filter(timpestamp__gte=start_date)

    total_clicks=url.click_count #total clicks


    last_click=clicks.order_by("-timestamp").first() #last clicked time



    daily_clicks=( #clicks per day
        clicks
        .annotate(day=TruncDate("timestamp")) #this create a temporary column in table which will convert the date time to date only.
        .values("day") #this will group the rows that have the same day value.
        .annotate(count=Count("id"))  #For each group, count how many rows it contains. this produce aggregated results.
        .order_by("day") #the result is sorted chronologically.
    )

    days=[item["day"].strftime("%Y-%m-%d")  for item in daily_clicks]
    counts=[item["count"] for item in daily_clicks]
    return render(request,"analytics.html",{
        "url":url,
        "total_clicks":total_clicks,
        "last_click":last_click.timestamp if last_click else None,
        "daily_clicks":daily_clicks,
        "days":days,
        "counts":counts,
    })
