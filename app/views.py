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
def logout_user(request):
    if request.method=='POST':
        logout(request)
        return redirect('login')
    context={
        'user':request.user
    }
    return render(request,'logout.html',{'context':context})


@login_required
@csrf_protect
def home_page(request):
    if request.method=='POST':
        original_url = request.POST.get("original_url")
        short_code=short_code_generator()
        print(short_code)
        ShortURL.objects.create(
            user=request.user,
            original_url=original_url,
            short_code=short_code
        )
        return redirect("list")
    return render(request,"home.html")


@login_required
def list_url(request):
    urls = ShortURL.objects.filter(user=request.user).order_by("-created_at")
    total_clicks=urls.aggregate(
        total=Sum("click_count")
    )["total"] or 0
    total_urls=urls.count()
    print(total_clicks)
    return render(request,"list.html",{
        "urls":urls,
        "total_clicks":total_clicks,
        "total_urls":total_urls
        })


@login_required
def update_url(request,id):
    url_obj=get_object_or_404(ShortURL,id=id,user=request.user)
    if request.method=="POST":
        new_url=request.POST.get("original_url")
        url_obj.original_url=new_url
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
    url.click_count=F("click_count")+1
    url.save(update_fields=["click_count"])
    return redirect(url.original_url)