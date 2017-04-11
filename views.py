
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Htweets
from .serializers import HtweetsSerializer

# Create your views here.
#list all tweets
class HtweetsList(APIView):

    def get(self, request):
        tweets = Htweets.objects.all()
        serializer = HtweetsSerializer(tweets, many=True)
        return Response(serializer.data)
