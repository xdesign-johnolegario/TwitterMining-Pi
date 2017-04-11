from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Hermtweets
from .serializers import HermtweetsSerializer
import json

import time



with open('/home/hermes/Documents/hermesprodtweets/Hermtweets/htweetings1.json') as json_data:
    e = json.load(json_data)
    json_data.close()

    tweets = Hermtweets()
    for x in e:
        tweets.tweet_date = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(x['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
        tweets.tweet_id = x['id']
        tweets.tweet_recount = x['retweet_count']
        tweets.tweet_favour_count = x['favorite_count']
        tweets.tweet_text = x['text']

    tweets.save()


# Create your views here.
#list all tweets
class HermtweetsList(APIView):

    def get(self, request):
        tweets = Hermtweets.objects.all()
        serializer = HermtweetsSerializer(tweets, many=True)
        return Response(serializer.data)

    def post(self):
        pass