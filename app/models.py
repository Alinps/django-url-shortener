from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class ShortURL(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True)
    original_url=models.URLField()
    short_code=models.CharField(max_length=10,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    click_count=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"