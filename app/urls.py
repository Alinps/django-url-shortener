
from django.urls import path
from app import views
from app import health
urlpatterns = [
    path('',views.landingpage),
    path("home/",views.home_page,name='home'),
    path('list/',views.list_url,name='list'),
    path('update/<int:id>/',views.update_url,name='update'),
    path("delete/<int:id>/",views.delete_url,name='delete'),
    path("<str:short_code>",views.redirect_url,name="redirect"),
    path("togglestatusajax/<int:id>",views.toggle_url_ajax,name="toggle_ajax"),
    path("aboutus/",views.aboutus,name="aboutus"),
    path("dashboard/stats/",views.dashboard_stats,name="dashboard_stats"),
    path("analytics/<int:url_id>/", views.analytics_view, name="analytics"),
    path("health/live/", health.health_live),
    path("health/ready/", health.health_ready),

]