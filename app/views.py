from django.shortcuts import render
from django.contrib import messages
from .forms import SignUp
# Create your views here.
def register(request):
    if request.method=='POST':
        form=SignUp(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration Successfull")
            return render(request,'login.html')
    else:
        form=SignUp()
    return render(request,'signup.html',{"forms":form})