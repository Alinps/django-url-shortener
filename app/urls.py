from django.contrib import admin
from django.urls import path,include
from app import views
urlpatterns = [
    path('',views.landingpage),
    path('signup/',views.register,name='signup'),
    path("login/",views.login_user,name='login'),
    path("home/",views.home_page,name='home'),
    path('logout/',views.logout_user,name='logout'),
    path('list/',views.list_url,name='list'),
    path('edit/<int:id>',views.update_url,name='update'),
    path("/delete/<int:id>",views.delete_url,name='delete'),
    path("/redirect/<str:short_code>",views.redirect_url,name="redirect"),
    path("togglestatus/<int:id>",views.toggle_url_status,name="toggle")
]