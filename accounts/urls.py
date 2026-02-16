from django.urls import path
from accounts import views


urlpatterns = [
    path('authchoice/',views.auth_choice,name='auth_choice'),
    path('signup/',views.register,name='signup'),
    path("login/",views.login_user,name='login'),
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
    path("resend-activation/", views.resend_activation, name="resend_activation"),
    path("forgotpassword/", views.forgot_password, name="forgotpassword"),
    path("verifyresetotp/", views.verify_reset_otp, name="verify_reset_otp"),
    path('logout/',views.logout_user,name='logout'),
]