"""
URL configuration for urlshortner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path,include
from django_prometheus import exports
from prometheus_client import generate_latest,CollectorRegistry,multiprocess, CONTENT_TYPE_LATEST

def metrics_view(request):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    path("metrics/", metrics_view,),
    path('admin/', admin.site.urls),
    path('',include('app.urls')),
    path('accounts/',include('allauth.urls')),
    path('account/', include('accounts.urls')),
]
