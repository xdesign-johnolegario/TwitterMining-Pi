from django.db import models


class Htweets(models.Model):
    tweet_id = models.CharField(
        max_length=200,
        unique=True,
        primary_key=True
    )
    tweet_date = models.DateTimeField()
    tweet_source = models.TextField()
    tweet_favour_count = models.CharField(max_length=200)
    tweet_retweet_cnt = models.CharField(max_length=200)
    tweet_text = models.TextField()

    def __str__(self):
        return self.tweet_id + '|' + str(self.tweet_date)
