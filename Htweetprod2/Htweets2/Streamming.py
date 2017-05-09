


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json

import sys, os, django


sys.path.append("C:/Users/hisg316/Desktop/Htweetprod2")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Htweetprod2.settings")
django.setup()


from Htweets2.models import Htweets2
from profanity import profanity

# Variables that contains the user credentials to access Twitter API
consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret = "DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"


swear_words =['anal', 'anus', 'arse', 'ballshack', 'balls', 'bastard', 'bitch', 'biatch',
              'bloody', 'blowjob', 'blow job', 'bollock', 'bollok', 'boner', 'boob', 'bugger',
              'bum', 'butt', 'buttplug', 'clitoris', 'cock', 'coon', 'crap', 'cunt', 'cunts','damn',
              'dick', 'dildo', 'dyke', 'fag', 'feck', 'fellate', 'fellatio', 'felching', 'fuck',
              'f u c k', 'fudgepacker', 'fudge packer', 'flange', 'Goddamn', 'God damn', 'hell',
              'homo', 'jerk', 'jizz', 'knobend', 'knobend', 'knob end', 'labia', 'lmao', 'lmfao',
              'muff', 'nigger', 'nigga', 'penis', 'piss', 'piss', 'poop', 'prick', 'pube', 'pussy',
              'queer', 'scrotum', 'sex', 'shit', 's hit', 'slut', 'smegma', 'spunk', 'tit', 'tosser',
               'retard', 'retards', 'twat', 'twats', 'vagina', 'wank', 'whore', 'wtf']

critical_words_train = [('website is down', 'neg'),
                        ('website down', 'neg'),
                        ('the site is down' , 'neg'),
                        ('your site is down', 'neg'),
                        ('the website is down,' 'neg')]
#load custom bad words
profanity.load_words(swear_words)

def classificationAnalysis(text):
    # method that takes the text and spits out the argument
    classified_text = len(text)

    return classified_text



# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self):
        self.tweet_data = []

        # self.counter = 0

    def on_data(self, data):
        # pprint (data)
        # saveFile = io.open('tweet_raw.json', 'a', encoding='utf-8')
        # thetweets = json.loads(data)
        print(json.loads(data))
        self.tweet_data.append(json.loads(data))

        tweets = Htweets2()
        for x in self.tweet_data:
            tweets.tweet_timestamp = x['timestamp_ms']
            tweets.tweet_id = x['id']
            tweets.tweet_screenname = x['user']['screen_name']
            tweets.tweet_recount = x['retweet_count']
            tweets.tweet_favour_count = x['favorite_count']
            tweets.tweet_text = profanity.censor(x['text'])
            tweets.tweet_location = x['user']['location']

            if 'media' in self.tweet_data:
                tweets.tweet_media_entities = x['entities']['media'][0]['media_url']

            tweets.save()

    def gettext(self):
        for tweets in self.tweet_data:
            print(tweets["text"])


    def on_error(self, status):
        print(status)




if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)

    # This line filter Twitter Streams to capture data by the keywords: '@myhermes
    stream.filter(track=['@testH17'])
