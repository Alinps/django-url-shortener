from datetime import timedelta
from django.utils import timezone
from datetime import datetime
from django.db.models.functions import TruncDate
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
from .utils.shortcode_validator import  is_valid_custom_code
from .models import ShortURL,ClickEvent
from django.db.models import F, Count
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
from django.contrib.auth.models import User
from .utils.mail_sender import send_reset_otp
from .utils.detect_device import detect_device_type
from .utils.otp_generate import generate_otp
from .models import PasswordResetOTP
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import never_cache
from django.db import DataError, IntegrityError
import traceback
from .utils.base62 import encode_base62
from django.core.cache import cache


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
    if request.method == "POST":
        original_url=request.POST.get("original_url")
        title=request.POST.get("title")
        custom_code=request.POST.get("custom_code","").strip()

        try:
            #CASE 1 : User wants a custom shortcode
            if custom_code:
                if not is_valid_custom_code(custom_code):
                    messages.error(request, "Invalid short URL format")
                    return redirect("home")

                #Attempt to create directly
                short_url = ShortURL.objects.create(
                    user=request.user,
                    original_url=original_url,
                    short_code=custom_code,
                    title=title
                )

            #CASE 2 : Auto-generate shortcode (production way)
            else:
                # Step 1 : Create row without short_code
                short_url=ShortURL.objects.create(
                    user=request.user,
                    original_url=original_url,
                    title=title
                )
                # Step 2: generate deterministic code
                short_url.short_code = encode_base62(short_url.id)

                # Step 3: update only short_code
                short_url.save(update_fields=["short_code"])

            messages.success(request, "URL shortneed successfully")
            return redirect("list")

        except IntegrityError:
            # Triggered when custom_code already exists
            messages.error(request, "Short URL already exists")
            return redirect("home")

        except DataError:
            messages.error(request,"The URL is too long or Invalid.")
            return redirect("home")

    return render(request, "home.html")




# @never_cache
# @login_required
# @csrf_protect
# def home_page(request):
#     if request.method == 'POST':
#         original_url = request.POST.get("original_url")
#         title = request.POST.get("title")
#         custom_code = request.POST.get("custom_code", "").strip()
#
#         print("CUSTOM_CODE:", custom_code)
#
#         # Decide short_code
#         if custom_code:
#             if not is_valid_custom_code(custom_code):
#                 messages.error(request, "Invalid short URL format")
#                 return redirect("home")
#
#             if ShortURL.objects.filter(short_code__iexact=custom_code).exists():
#                 messages.error(request, "Short URL already exists")
#                 return redirect("home")
#
#             short_code = custom_code
#         else:
#             while True:
#                 short_code = short_code_generator()
#                 if not ShortURL.objects.filter(short_code=short_code).exists():
#                     break
#
#         try:
#             ShortURL.objects.create(
#                 user=request.user,
#                 original_url=original_url,
#                 short_code=short_code,
#                 title=title
#             )
#             messages.success(request, "URL shortened successfully")
#             return redirect("list")
#
#         except DataError:
#             messages.error(
#                 request,
#                 "The URL is too long. Please enter a shorter or valid URL."
#             )
#             return redirect("home")
#     return render(request, "home.html")

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


        custom_code=data["custom_code"]

        try:
            if custom_code:

                if not is_valid_custom_code(custom_code):

                    return JsonResponse({
                        "success":False,
                        "message":"Invalid Custom URL formal"
                    })
                url.short_code=custom_code
                url.title = data["title"]
                url.original_url = data["original_url"]
                url.save(update_fields=["short_code","title","original_url"])
                return JsonResponse({
                        "success":True,
                        "title":url.title,
                        "original_url":url.original_url,
                        "custom_url":url.short_code
                    })
        except IntegrityError:
            return JsonResponse({
                "success":False,
                "message":"URL Shortcode already exists, try new custom short code."
            })
        except DataError:
            return JsonResponse({
                "success":False,
                "message":"Too Long URL or, Invalid URL format."
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


# def redirect_url(request,short_code):
#     url=get_object_or_404(ShortURL.objects.only("original_url"),
#                           short_code=short_code,
#                           is_active=True)
#
#     ShortURL.objects.filter(id=url.id).update( #Atomic increment, increment the value safely at the db level. This prevents race condition while multiple user click at a time
#         click_count=F("click_count") + 1
#     )
#
#
#
#     ua = request.META.get("HTTP_USER_AGENT","")
#     device=detect_device_type(ua)
#
#     #store analytics event (details)
#     ClickEvent.objects.create(
#         short_url=url,
#         user_agent=request.META.get("HTTP_USER_AGENT",""),
#         device_type=device
#     )
#     return redirect(url.original_url)




CACHE_TTL = 60 * 60 # 1 hour
def redirect_url(request,short_code):
    cache_key=f"short_url:{short_code}"

    #STEP 1: Try cache
    cached = cache.get(cache_key)

    if cached:
        if not cached["is_active"]:
            raise Http404("This URL is disables")

        ua = request.META.get("HTTP_USER_AGENT","")
        device = detect_device_type(ua)

        ShortURL.objects.filter(short_code=short_code).update(
            click_count=F("click_count")+1
        )

        ClickEvent.objects.create(
            short_url_id=cached["id"],
            user_agent=ua,
            device_type=device
        )
        print("CACHE HIT")
        return redirect(cached["original_url"])

    #STEP 2: Cache miss -> DB
    url = get_object_or_404(
        ShortURL.objects.only("id","original_url","is_active"),
        short_code=short_code,
        is_active=True
    )

    cache.set(
        cache_key,
        {
            "id":url.id,
            "original_url":url.original_url,
            "is_active":url.is_active,
        },
        CACHE_TTL
    )

    #STEP 4: TEMP analytics
    ua = request.META.get("HTTPS_USER_AGENT","")
    device = detect_device_type(ua)

    ShortURL.objects.filter(id=url.id).update(
        click_count=F("click_count") + 1
    )

    ClickEvent.objects.create(
        short_url=url,
        user_agent=ua,
        device_type=device
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
    # base queryset
    clicks = ClickEvent.objects.filter(short_url=url)
    #Read range from query params
    range_params=request.GET.get("range")
    start_params=request.GET.get("start")
    end_params=request.GET.get("end")




    #decide the start date
    now=timezone.now()
    start_date=None
    end_date=None

    #Preset ranges
    if range_params=="7":
        start_date=now - timedelta(days=7)
    elif range_params=="30":
        start_date=now-timedelta(days=30)
    elif range_params=="all":
        start_date=None

    #Custom range (overrides presets)
    if start_params and end_params:
        try:
            start_date=datetime.strptime(start_params,"%Y-%m-%d")
            end_date=datetime.strptime(end_params,"%Y-%m-%d") + timedelta(days=1)

            start_date=timezone.make_aware(start_date)
            end_date=timezone.make_aware(end_date)
        except ValueError:
            start_date=None
            end_date=None




    #Apply date filer if needed
    if start_date:
        clicks=clicks.filter(timestamp__gte=start_date)
    if end_date:
        clicks=clicks.filter(timestamp__lt=end_date)

    #---Aggregations---
    total_clicks=url.click_count #total clicks

    device_stats = (
        clicks
        .values("device_type")
        .annotate(count=Count("id"))
    )


    last_click_obj=clicks.order_by("-timestamp").first() #last clicked time
    last_click = last_click_obj.timestamp if last_click_obj else None




    daily_clicks=( #clicks per day
        clicks
        .annotate(day=TruncDate("timestamp")) #this creates a temporary column in table which will convert the date time to date only.
        .values("day") #this will group the rows that have the same day value.
        .annotate(count=Count("id"))  #For each group, count how many rows it contains. this produce aggregated results.
        .order_by("day") #the result is sorted chronologically.
    )
    device_labels=[item["device_type"].title() if item["device_type"] else "Unknown"
                   for item in device_stats
                   ]
    device_counts=[item["count"] for item in device_stats]
    days=[item["day"].strftime("%Y-%m-%d")  for item in daily_clicks]
    counts=[item["count"] for item in daily_clicks]
    return render(request,"analytics.html",{
        "url":url,
        "total_clicks":total_clicks,
        "last_click":last_click,
        "daily_clicks":daily_clicks,
        "current_range":range_params,
        "days":days,
        "counts":counts,
        "start":start_params,
        "end":end_params,
        "device_stats":device_stats,
        "device_labels":device_labels,
        "device_counts":device_counts

    })

