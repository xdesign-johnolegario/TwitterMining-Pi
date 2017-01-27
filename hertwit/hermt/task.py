
import time

import tweepy

from twitter import *
from celery import*
#from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from django.db import IntegrityError

import django
from django.conf import settings


from hermt.models import Htweets
import os
import io

consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret="DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"


auth = OAuthHandler(consumer_key, consumer_secret) #OAuth object
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify=True)

@shared_task(name='get_tweets')
def get_tweets():
    """Get some tweets from the twitter api and store them to the db."""

    # Subtasks
    """chain = cleanup.s()
    chain()"""

    # Check for the minimum tweet_id and set it as max_id.
    # This ensures the API call doesn't keep getting the same tweets.
    max_id = min([tweet.tweet_id for tweet in Htweets.objects.all()])

    # Make the call to the Twitter Search API.
    tweets = api.search(
        q='@myhermes',
        max_id=max_id,
        count=100
    )

    # Store the collected data into lists.
    tweets_date = [tweet.created_at for tweet in tweets]
    tweets_id = [tweet.id for tweet in tweets]
    tweets_source = [tweet.source for tweet in tweets]
    tweets_favorite_cnt = [tweet.favorite_count for tweet in tweets]
    tweets_retweet_cnt = [tweet.retweet_count for tweet in tweets]
    tweets_text = [tweet.text for tweet in tweets]

    # Iterate over these lists and save the items as fields for new records in the database.
    for i, j, k, l, m, n in zip(
            tweets_id,
            tweets_date,
            tweets_source,
            tweets_favorite_cnt,
            tweets_retweet_cnt,
            tweets_text
    ):
        try:
            Htweets.objects.create(
                tweet_id=i,
                tweet_date=j,
                tweet_source=k,
                tweet_favorite_cnt=l,
                tweet_retweet_cnt=m,
                tweet_text=n,
            )
        except IntegrityError:
            pass