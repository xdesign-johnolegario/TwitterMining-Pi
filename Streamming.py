# Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json

# Variables that contains the user credentials to access Twitter API
consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret="DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"


def classificationAnalysis(text):

    # method that takes the text and spits out the argument
    classified_text = len(text)

    return classified_text


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def on_connect(self):
        """Called when the connection is made"""
        print("You're connected to the streaming server.")

    def on_data(self, data):
        # print(data)
 #       with open('tweets.json', 'a') as tf:
  #          json.dumps(tf, indent=1)
        stream_array = []
        tweet_stream = json.loads(data)

        c = {
            'created': tweet_stream['created_at'],
            'id': tweet_stream['id'],
            'text': tweet_stream['text']
        }

        stream_array.append(c)
        print(len(stream_array))
        print(stream_array)
        return True

    def on_error(self, status_code, status):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            print(status)
            return False


if __name__ == '__main__':

    # This handles Twitter authetification and the connection to Twitter Streaming API

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, StdOutListener())

    # This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
    # async parameter on filter so the stream will run on a new thread
    stream.filter(track=['@myhermes'], async=True)


