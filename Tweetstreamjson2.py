# Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from pprint import pprint
import io

import json

# Variables that contains the user credentials to access Twitter API
consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret = "DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self):
        self.tweet_data = []
        self.counter = 0

    def on_data(self, data):
        # pprint (data)
        # saveFile = io.open('tweet_raw.json', 'a', encoding='utf-8')
        print(data)
        self.tweet_data.append(data)
        with open('htweetings.json', 'w', encoding='utf-8') as out:
            json.dump(self.tweet_data, out)
        


def on_error(self, status):
    print(status)


if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)

    # This line filter Twitter Streams to capture data by the keywords: '@myhermes
    stream.filter(track=['@myhermes'])
