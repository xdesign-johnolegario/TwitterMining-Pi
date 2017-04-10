from __future__ import unicode_literals
from django.utils import timezone
from django.db import models


# Create your models here.
class Hermtweets(models.Model):
    tweet_id = models.BigIntegerField(default=None)
    tweet_date = models.DateTimeField(default=timezone.now())
    tweet_favour_count = models.CharField(default=None, max_length=200)
    tweet_recount = models.BigIntegerField(default=None)
    tweet_text = models.TextField(default=None)
