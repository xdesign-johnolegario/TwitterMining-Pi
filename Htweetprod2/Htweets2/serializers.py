from rest_framework import serializers
from .models import Htweets2

class Htweets2Serializer(serializers.ModelSerializer):

    class Meta:
        model = Htweets2
        fields = ('tweet_id', 'tweet_timestamp', 'tweet_screenname','tweet_favour_count', 'tweet_recount', 'tweet_location', 'tweet_text', 'tweet_media_entities', 'tweet_status', 'tweet_score')