from rest_framework import serializers
from .models import Htweets

#serializer class simply converts data from models.py and turns this into json format
class HtweetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Htweets
        # fields =("tweet_id", "tweet_date", "tweet_source", "tweet_favour_count", "tweet_retweet_count", "tweet_text")
        fields = '__all__'



