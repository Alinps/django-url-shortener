from datetime import timedelta
from django.conf import settings
from datetime import datetime
from django.db.models.functions import TruncDate
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, render,redirect
import json
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .tasks import enqueue_click
from .utils.id_generator import get_next_short_id
from .utils.rate_limit import check_rate_limit, check_create_rate_limit
from .utils.rate_limit_response import rate_limited_response
from .utils.shortcode_validator import  is_valid_custom_code
from .models import ClickEvent,ShortURLCore, ShortURLMeta
from django.db.models import  Count
from django.views.decorators.csrf import csrf_protect
from .utils.detect_device import detect_device_type
from django.db import DataError, IntegrityError, transaction
from .utils.base62 import encode_base62,obfuscate_id
from django.core.cache import cache
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .metrics import (redirect_request_total,
                      cache_hit_total,
                      cache_miss_total,
                      click_enqueued_total, redirect_latency_seconds)
import time
from django.views.decorators.cache import never_cache
from redis.exceptions import RedisError
import logging
logger = logging.getLogger(__name__)
# Create your views here.





def landingpage(request):
    return render(request,'landingpage.html')







#





@never_cache
@login_required
@csrf_protect
def home_page(request):

    if request.method == "POST":

        # --------------------------
        # Get Client IP
        # --------------------------
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip = x_forwarded.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        # --------------------------
        # 1️⃣ Redis Burst Protection (Fail-Open)
        # --------------------------
        try:
            if not check_create_rate_limit(ip, request.user.id):
                logger.error("URL creation rate limit exceeded",extra={"ip":ip,"request_id":request.request_id})
                return rate_limited_response(
                    request,
                    settings.CREATE_RATE_WINDOW
                )
        except RedisError:
            # Redis down → allow request (fail-open)
            pass

        # --------------------------
        # 2️⃣ DB Hard Daily Quota (Authoritative)
        # --------------------------
        today = timezone.now().date()

        daily_count = ShortURLMeta.objects.filter(
            user=request.user,
            created_at__date=today
        ).count()

        if daily_count >= settings.CREATE_DAILY_LIMIT:
            return rate_limited_response(
                request,
                settings.CREATE_RATE_WINDOW
            )

        # --------------------------
        # Extract Inputs
        # --------------------------
        original_url = request.POST.get("original_url")
        title = request.POST.get("title")
        custom_code = request.POST.get("custom_code")

        try:
            with transaction.atomic():

                # --------------------------
                # Shortcode Generation
                # --------------------------
                if custom_code:

                    if not is_valid_custom_code(custom_code):
                        messages.error(request, "Invalid short URL format")
                        return redirect("home")

                    core = ShortURLCore.objects.create(
                        short_code=custom_code,
                        original_url=original_url,
                        is_active=True
                    )

                else:
                    # Recommended: Use DB auto-increment ID
                    core = ShortURLCore.objects.create(
                        short_code="temp",  # placeholder
                        original_url=original_url,
                        is_active=True
                    )

                    # Generate based on DB id
                    obfuscated = obfuscate_id(core.id)
                    short_code = encode_base62(obfuscated)

                    core.short_code = short_code
                    core.save(update_fields=["short_code"])

                # --------------------------
                # Meta Record
                # --------------------------
                ShortURLMeta.objects.create(
                    short_url=core,
                    user=request.user,
                    title=title or "",
                    click_count=0
                )

            messages.success(request, "URL shortened successfully")
            return redirect("list")

        except IntegrityError:
            logger.error("DB Integrity Error",extra={"ip":ip,"request_id":request.request_id})
            messages.error(request, "Short URL already exists")
            return redirect("home")

        except DataError:
            logger.error("DB Data Error", extra={"ip": ip, "request_id": request.request_id})
            messages.error(request, "Invalid URL format or URL is too long")
            return redirect("home")

    return render(request, "home.html")















@never_cache
@login_required
@require_GET
def list_url(request):
    query = request.GET.get("q", "").strip()

    urls = (
        ShortURLMeta.objects
        .filter(user=request.user)
        .select_related("short_url")
        .order_by("-short_url__created_at")
    )

    if query:
        urls = urls.filter(
            Q(title__icontains=query) |
            Q(short_url__original_url__icontains=query) |
            Q(short_url__short_code__icontains=query)
        ).distinct()

    paginator = Paginator(urls, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_clicks = urls.aggregate(total=Sum("click_count"))["total"] or 0
    total_urls = urls.count()
    active_urls = urls.filter(short_url__is_active=True).count()
    disabled_urls = urls.filter(short_url__is_active=False).count()

    # 👇 AJAX detection
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        results = []
        for url in page_obj:
            results.append({
                "id": url.id,
                "title": url.title,
                "original_url": url.short_url.original_url,
                "short_code": url.short_url.short_code,
                "click_count": url.click_count,
                "is_active": url.short_url.is_active,
                "created_at": url.short_url.created_at.strftime("%b %d, %Y"),
            })

        return JsonResponse({
            "results": results,
            "pagination": {
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
            },
            "stats": {
                "total_urls": total_urls,
                "active_urls": active_urls,
                "disabled_urls": disabled_urls,
                "total_clicks": total_clicks,
            }
        })

    # Normal HTML render
    return render(request, "list.html", {
        "urls": page_obj,
        "total_clicks": total_clicks,
        "total_urls": total_urls,
        "active_urls": active_urls,
        "disabled_urls": disabled_urls,
    })











@login_required
def update_url(request,id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})
        print("id",id)

        meta = get_object_or_404(
            ShortURLMeta.objects.select_related("short_url"),
            id=id,
            user=request.user
        )

        core = meta.short_url
        new_title = data.get("title")
        print("new_title",new_title)
        new_original_url = data.get("original_url")
        print("new_original_url",new_original_url)
        custom_code = data.get("custom_code","").strip()
        print("custom_code",custom_code)
        if not new_original_url:
            return JsonResponse({
                "success": False,
                "message": "Original URL cannot be empty"
            })

        try:
            with transaction.atomic():
                old_short_code = core.short_code

                if custom_code and custom_code  != core.short_code:
                    # Rule 1 : Never clicked
                    never_clicked = not ClickEvent.objects.filter(short_url=core).exists()


                    # Rule 2 : Created within 5 minutes
                    within_5_minutes=(
                        timezone.now() - core.created_at
                    ) <= timedelta(minutes=5)

                    if not (never_clicked or within_5_minutes):
                        return JsonResponse({
                            "success":False,
                            "message":"Shortcode cannot be changed after exposure"
                        })
                    # Validate Custom shortcode
                    if not is_valid_custom_code(custom_code):
                        return JsonResponse({
                            "success":False,
                            "message":"Invalid custom URL format."
                        })

                    # Prevent collision (excluding self)
                    if ShortURLCore.objects.exclude(id=core.id).filter(short_code=custom_code).exists():
                        return JsonResponse({
                            "success":False,
                            "message":"Shortcode already exists."
                        })
                    core.short_code = custom_code

                # Always allow updating title and destination
                core.original_url = new_original_url
                meta.title = new_title

                core.save(update_fields=["short_code","original_url"])
                meta.save(update_fields=["title"])

                # Cache invalidation
                cache.delete(f"short_url:{old_short_code}")

                if custom_code and custom_code != old_short_code:
                    cache.delete(f"short_url:{custom_code}")

            return JsonResponse({
                "success":True,
                "title":meta.title,
                "original_url":core.original_url,
                "custom_url":core.short_code
            })

        except DataError:
            return JsonResponse({
                "success":False,
                "message":"Invalid or too long URL"
            })
    else:
        meta = get_object_or_404(
            ShortURLMeta.objects.select_related("short_url"),
            id=id,
            user=request.user
        )
        return JsonResponse({
            "id":meta.id,
            "title":meta.title,
            "original_url":meta.short_url.original_url,
            "custom_url":meta.short_url.short_code
        })










@login_required
def delete_url(request,id):
    if request.method == "DELETE":
        with transaction.atomic():

            # Get meta with related core
            meta = get_object_or_404(
                ShortURLMeta.objects.select_related("short_url"),
                id=id,
                user=request.user
            )

            core = meta.short_url

            # Delete cache first
            cache_key = f"short_url:{core.short_code}"
            cache.delete(cache_key)

            # If Core has on_delete=CASCADE from Meta -> It's already deleted
            core.delete()

        # Recalculate counts from Meta
        urls = ShortURLMeta.objects.filter(user=request.user)

        return JsonResponse({
            "success":True,
            "total_urls":urls.count(),
            "active_urls":urls.filter(short_url__is_active=True).count(),
            "disables_urls":urls.filter(short_url__is_active=False).count()
        })
    return None









CACHE_TTL = 60 * 60 # 1 hour
def redirect_url(request,short_code):
    start_time = time.time()
    try:
        redirect_request_total.inc()

        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip = x_forwarded.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        if not check_rate_limit(ip):
            logger.warning("Redirect URL rate limit exceeded",extra={"ip":ip,"request_id":request.request_id})
            return rate_limited_response(
                request,
                settings.REDIRECT_RATE_WINDOW
            )

        cache_key=f"short_url:{short_code}"

        #STEP 1: Try cache
        try:
            cached = cache.get(cache_key)
        except RedisError:
            logger.error("Redis error! redirect cant connect to redis",extra={"ip":ip,"request_id":request.request_id,"short_code":short_code})
            cached = None

        if cached:
            cache_hit_total.inc()
            if not cached["is_active"]:
                logger.warning("accessed disabled url",extra={"ip":ip,"request_id":request.request_id,"short_code":short_code})
                raise Http404("This URL is disabled")

            # Enqueue analytics (NON-BLOCKING)
            # record_click_event.delay(
            #     cached["id"],
            #     request.META.get("HTTP_USER_AGENT",""),
            #     detect_device_type(request.META.get("HTTP_USER_AGENT",""))
            # )
            click_enqueued_total.inc()
            try:
                logger.info("enqueue_click event cached",extra={"request_id":request.request_id,"short_code":short_code})
                enqueue_click.delay(
                    cached["id"],
                    request.META.get("HTTP_USER_AGENT",""),
                    detect_device_type(request.META.get("HTTP_USER_AGENT",""))
                )
                print("CACHE HIT")
            except Exception:
                logger.error("enqueue_click event can't be cached",extra={"request_id":request.request_id,"short_code":short_code})
                pass

            return redirect(cached["original_url"])

        #STEP 2: Cache miss -> DB
        cache_miss_total.inc()
        url = get_object_or_404(
            ShortURLCore.objects.only("id","original_url","is_active"), # New table
            short_code=short_code,
            # is_active=True
        )

        try:
            cache.set(
                cache_key,
                {
                    "id":url.id,
                    "original_url":url.original_url,
                    "is_active":url.is_active,
                },
                CACHE_TTL
            )
        except RedisError:
            pass
        click_enqueued_total.inc()

        try:
            logger.info("enqueue_click event cached",
                        extra={"request_id": request.request_id, "short_code": short_code})
            enqueue_click.delay(
                url.id,
                request.META.get("HTTP_USER_AGENT", ""),
                detect_device_type(request.META.get("HTTP_USER_AGENT", ""))
            )
        except Exception:
            logger.error("enqueue_click event can't be cached",
                         extra={"request_id": request.request_id, "short_code": short_code})
            pass
        print("from db")
        if not url.is_active:
            raise Http404("This URL is disabled")
        return redirect(url.original_url)
    finally:
        duration = time.time()-start_time
        redirect_latency_seconds.observe(duration)







def toggle_url_ajax(request, id):
    if request.method == "POST":
        with transaction.atomic():
            meta = get_object_or_404(
                ShortURLMeta.objects.select_related("short_url"),
                id=id,
                user=request.user
            )

            core = meta.short_url

            core.is_active = not core.is_active
            core.save(update_fields=["is_active"])

            cache_key = f"short_url:{core.short_code}"
            cache.delete(cache_key)

        active_count = ShortURLMeta.objects.filter(
            user=request.user,
            short_url__is_active=True
        ).count()

        disabled_count = ShortURLMeta.objects.filter(
            user=request.user,
            short_url__is_active=False
        ).count()

        return JsonResponse({
            "success":"True",
            "status":core.is_active,
            "active_count":active_count,
            "disabled_count":disabled_count
        })
    return JsonResponse({
        "success":"False"
    })




def aboutus(request):
    return render(request,'about.html')














@login_required
def dashboard_stats(request):

    urls = (
        ShortURLMeta.objects
        .filter(user=request.user)
        .select_related("short_url")
        .order_by("-short_url__created_at")
    )

    total_clicks = urls.aggregate(
        total=Sum("click_count")
    )["total"] or 0
    print(total_clicks)

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
    url = get_object_or_404(
        ShortURLMeta.objects.select_related("short_url"),
        id=url_id,
        user=request.user
    )
    # base queryset
    clicks = ClickEvent.objects.filter(short_url=url.short_url)
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

