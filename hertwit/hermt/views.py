from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework.response import Response
from rest_framework import status
from .models import Htweets
from .serializers import HtweetSerializer


"""from django.shortcuts import render
from django.http import HttpResponse
from hermt.models import Htweets

def index(request):
    tweets = Htweets.object.all()
    context = {'tweets': tweets}
    return render(request, 'tweets/hermtweet.html', context)"""

#list all tweets or create a new one
class Htweetlist(APIView):

    def get(self):
        tweets = Htweets.object.all()
        serializer = HtweetSerializer(tweets, many=True) #converts data in to json
        return Response(serializer.data)
    def post(self):
        pass