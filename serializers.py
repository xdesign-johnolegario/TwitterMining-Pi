from rest_framework import serializers
from .models import Htweets

class HtweetsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Htweets
        fields = ('tweet_id', 'tweet_date', 'tweet_favour_count', 'tweet_favour_count', 'tweet_recount', 'tweet_text')
