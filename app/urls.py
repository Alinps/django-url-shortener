from django.contrib import admin
from django.urls import path,include
from app import views
urlpatterns = [
    
    path('',views.register),
    path("login/",views.login_user,name='login')
]