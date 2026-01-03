from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from .forms import SignUp,login_form
from .utils import short_code_generator
from .models import ShortURL
# Create your views here.
def register(request):
    if request.method=='POST':
        form=SignUp(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration Successfull")
            return redirect('login')
    else:   
        form=SignUp()
    return render(request,'signup.html',{"form":form})

def login_user(request):
    if request.method=='POST':
        form=login_form(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(user)
            login(request,user)
            print(request.POST)
            return render(request,'home.html',{'user':user})
    else:
        form=login_form()
    return render(request,'login.html',{'form':form})


@login_required(login_url='/login/')
def logout_user(request):
    if request.method=='POST':
        logout(request)
        return redirect('login')
    context={
        'user':request.user
    }
    return render(request,'logout.html',{'context':context})



def create_short_url(request):
    if request.method=='POST':
        original_url = request.POST.get("original_url")
        short_code=short_code_generator()
        ShortURL.objects.create(
            original_url=original_url,
            short_code=short_code
        )
        messages.success(request,"Successfully shortened the URL")
        return render(request,"create.html")
    return render(request,"create.html")



def list_url(request):
    urls = ShortURL.objects.all().order_by("-created_at")
    return render(request,"list.html",{"urls":urls})



def update_url(request,id):
    url_obj=get_object_or_404(ShortURL,id=id)
    if request.method=="POST":
        new_url=request.POST.get("original_url")
        url_obj.original_url=new_url
        url_obj.save()
        return redirect("list")
    return render(request,"edit.html",{"url":url_obj})


def delete_url(request,id):
    url_obj=get_object_or_404(ShortURL,id=id)
    if request.method=='POST':
        url_obj.delete()
        return redirect("list")
    return render(request,"delete.html",{'url':url_obj})
        

def redirect_url(request,short_code):
    url=get_object_or_404(ShortURL,short_code=short_code)
    return redirect(url.original_url)