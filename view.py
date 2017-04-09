from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Htweets
from .serializers import HtweetsSerializer
import json

with open('/home/hermes/Documents/hermestweets/htweets/htweetings1.json') as json_data:
    e = json.load(json_data)
    json_data.close()

    tweets = Htweets()
    for x in e:
        #tweets.tweet_date = x['created_at']
        tweets.tweet_id = x['id']
        tweets.tweet_recount = x['retweet_count']
        tweets.tweet_favour_count = x['favorite_count']
        tweets.tweet_text = x['text']

    tweets.save()


# Create your views here.
#list all tweets
class HtweetsList(APIView):

    def get(self, request):
        tweets = Htweets.objects.all()
        serializer = HtweetsSerializer(tweets, many=True)
        return Response(serializer.data)

    def post(self):
        pass




