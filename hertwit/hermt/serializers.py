from rest_framework import serializers
from .models import Htweets

class HtweetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Htweets
        # fields =("tweet_id", "tweet_date", "tweet_source", "tweet_favour_count", "tweet_retweet_count", "tweet_text")
        fields = '_all_'



