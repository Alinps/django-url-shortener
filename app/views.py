from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from .forms import SignUp,login_form
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
            login(request,user)
            return render(request,'home.html',{'user':user})
    else:
        form=login_form()
    return render(request,'login.html',{'form':form})

