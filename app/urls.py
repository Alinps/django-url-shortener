
from django.urls import path
from app import views
urlpatterns = [
    path('',views.landingpage),
    path('authchoice/',views.auth_choice,name='auth_choice'),
    path('signup/',views.register,name='signup'),
    path("login/",views.login_user,name='login'),
    path("home/",views.home_page,name='home'),
    path('logout/',views.logout_user,name='logout'),
    path('list/',views.list_url,name='list'),
    path('update/<int:id>/',views.update_url,name='update'),
    path("delete/<int:id>/",views.delete_url,name='delete'),
    path("redirect/<str:short_code>",views.redirect_url,name="redirect"),
    path("togglestatus/<int:ids>",views.toggle_url_status,name="toggle"),
    path("aboutus/",views.aboutus,name="aboutus"),
    path("forgotpassword/",views.forgot_password,name="forgotpassword"),
    path("verifyresetotp/",views.verify_reset_otp,name="verify_reset_otp")
]