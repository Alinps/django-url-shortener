from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.
class ShortURL(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True)
    original_url=models.URLField()
    short_code=models.CharField(max_length=10,unique=True,blank=True)
    title=models.CharField(max_length=20,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    click_count=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class PasswordResetOTP(models.Model):
    email=models.EmailField()
    otp=models.CharField(max_length=6)
    created_at=models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (timezone.now()-self.created_at).seconds>300


class ClickEvent(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE,related_name="click_events")
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20,blank=True)

    def __str__(self):
        return f"Click on {self.short_url.short_code}at {self.timestamp}"
