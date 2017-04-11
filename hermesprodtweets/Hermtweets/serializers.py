from rest_framework import serializers
from .models import Hermtweets

class HermtweetsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hermtweets
        fields = ('tweet_id', 'tweet_date', 'tweet_favour_count', 'tweet_recount', 'tweet_text', 'tweet_timestamp', 'tweet_media_entities')