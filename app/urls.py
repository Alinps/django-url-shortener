from django.contrib import admin
from django.urls import path,include
from app import views
urlpatterns = [
    
    path('',views.register),
    path("login/",views.login_user,name='login'),
    path('logout/',views.logout_user,name='logout'),
    path('create/',views.create_short_url,name='create'),
    path('list/',views.list_url,name='list')
]