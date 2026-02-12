from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from app.utils.base62 import encode_base62





class PasswordResetOTP(models.Model):
    email=models.EmailField()
    otp=models.CharField(max_length=6)
    created_at=models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (timezone.now()-self.created_at).seconds>300






#Hot table for redirecting url
class ShortURLCore(models.Model):
    short_code = models.CharField(max_length=10, unique=True)
    original_url = models.URLField()
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["short_code"]),]

    # def save(self, *args, **kwargs):
    #     super().save(*args,**kwargs)
    #
    #     if not self.short_code:
    #         self.short_code = encode_base62(self.id)
    #         super().save(update_fields=["short_code"])

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


# Cold table for user and metadata
class ShortURLMeta(models.Model):
    short_url = models.OneToOneField(ShortURLCore,on_delete=models.CASCADE,related_name="meta",)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True,blank=True)
    title=models.CharField(max_length=255,blank=True)
    click_count= models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Meta for {self.short_url.short_code}"




class ClickEvent(models.Model):
    short_url = models.ForeignKey(ShortURLCore, on_delete=models.CASCADE,related_name="click_events")
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20,blank=True)

    def __str__(self):
        return f"Click on {self.short_url.short_code}at {self.timestamp}"