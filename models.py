from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Htweets(models.Model):
    tweet_id = models.TextField()
    tweet_date = models.DateTimeField()
    tweet_favour_count = models.CharField(max_length=200)
    tweet_recount = models.CharField(max_length=200)
    tweet_text = models.TextField()

    def __str__(self):
        return self.tweet_id + '|' + str(self.tweet_date)