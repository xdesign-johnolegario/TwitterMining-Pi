from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Htweets2
from .serializers import Htweets2Serializer
from .Streamming import StdOutListener
import json

"""
def load_tweets():

        e = load_tweets()
        for e in
        e = json.load(json_data)
        json_data.close()

        tweets = Htweets2()
        for x in e:
            tweets.tweet_timestamp = x['timestamp_ms']
            tweets.tweet_id = x['id']
            tweets.tweet_screename = x['user']['screen_name']
            tweets.tweet_recount = x['retweet_count']
            tweets.tweet_favour_count = x['favorite_count']
            tweets.tweet_text = x['text']
            tweets.tweet_location = x['user']['location']
            tweets.tweet_media_entities = x['source']

            tweets.save()

load_tweets()"""



# Create your views here.
#list all tweets
class Htweets2List(APIView):

    def get(self, request):
        tweets = Htweets2.objects.all()
        serializer = Htweets2Serializer(tweets, many=True)
        return Response(serializer.data)

    def post(self):
        pass




