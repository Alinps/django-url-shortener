from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from .forms import SignUp,login_form
from .utils import short_code_generator
from .models import ShortURL
from django.db.models import F
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
# Create your views here.
def landingpage(request):
    return render(request,'landingpage.html')


def register(request):
    if request.method=='POST':
        form=SignUp(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration Successfull")
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


@login_required(login_url='/login/')
@csrf_protect
def logout_user(request):
    if request.method=='POST':
        logout(request)
        return redirect('login')
    return render(request,'logout.html')


@login_required
@csrf_protect
def home_page(request):
    if request.method=='POST':
        original_url = request.POST.get("original_url")
        title=request.POST.get("title")
        print(title)
        short_code=short_code_generator()
        print(short_code)
        ShortURL.objects.create(
            user=request.user,
            original_url=original_url,
            short_code=short_code,
            title=title
        )
        return redirect("list")
    return render(request,"home.html")


@login_required
def list_url(request):
    query=request.GET.get("q","")
    urls = ShortURL.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(urls, 10)  # 10 urls per page
    page_number = request.GET.get("page")
    url_qs = paginator.get_page(page_number)
    if query:
        urls=urls.filter(title__icontains=query)
    total_clicks=urls.aggregate(
        total=Sum("click_count")
    )["total"] or 0
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


@login_required
def update_url(request,id):
    url_obj=get_object_or_404(ShortURL,id=id,user=request.user)
    if request.method=="POST":
        new_url=request.POST.get("original_url")
        new_status=request.POST.get("status")
        url_obj.original_url=new_url
        url_obj.is_active=new_status
        url_obj.save()
        return redirect("list")
    return render(request,"edit.html",{"url":url_obj})

@login_required
def delete_url(request,id):
    url_obj=get_object_or_404(ShortURL,id=id,user=request.user)
    if request.method=='POST':
        url_obj.delete()
        return redirect("list")
    return render(request,"delete.html",{'url':url_obj})

def redirect_url(request,short_code):
    url=get_object_or_404(ShortURL,short_code=short_code)
    if not url.is_active:
        raise Http404("This URL is disabled")
    url.click_count=F("click_count")+1
    url.save(update_fields=["click_count"])
    return redirect(url.original_url)

@login_required
def toggle_url_status(request,id):
    url=get_object_or_404(ShortURL,id=id,user=request.user)
    url.is_active=not url.is_active
    url.save(update_fields=["is_active"])
    return redirect("list")

@login_required
def aboutus(request):
    return render(request,'about.html')