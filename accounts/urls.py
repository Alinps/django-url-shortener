from django.urls import path
from accounts import views


urlpatterns = [
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
    path("resend-activation/", views.resend_activation, name="resend_activation"),

]