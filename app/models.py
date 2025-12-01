from django.db import models

# Create your models here.
class urls(models.Model):
    shorturl = models.URLField(max_length=10,unique=True)
    originalurl = models.URLField(max_length=100,unique=True)
    addedUrl = models.IntegerField()