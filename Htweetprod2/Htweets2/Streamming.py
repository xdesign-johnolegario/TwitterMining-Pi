


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob.classifiers import NaiveBayesClassifier
import json

import sys, os, django

from sense_hat import SenseHat
sense = SenseHat()

r = [255, 0, 0]
o = [255, 127, 0]
y = [255, 255, 0]
g = [0, 255, 0]
w = [150, 150, 150]
b = [0, 0, 255]
i = [75, 0, 130]
v = [159, 0, 255]
e = [0, 0, 0]

detectionstate = [
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y,
y,y,y,y,y,y,y,y
]

sys.path.append("/home/hermes/Documents/Htweetprod2")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Htweetprod2.settings")
django.setup()

from Htweets2.models import Htweets2
from profanity import profanity

# Variables that contains the user credentials to access Twitter API
consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret = "DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"


swear_words =['arse', 'bastard', 'bitch', 'biatch',
              'bollock', 'bollok', 'boner', 'boob', 'bugger','bum', 'butt', 'buttplug',
              'clitoris', 'cock', 'coon', 'crap', 'cunt', 'cunts','damn','dick', 
              'dyke', 'fag', 'feck', 'fellate', 'fellatio', 'felching', 'fuck','f u c k',
        		'fucking','fudgepacker', 'fudge packer', 'flange', 'faggot', 'paki','knob', 'cuntflaps','semen',
				'homo', 'jerk', 'jizz', 'knobend', 'knobend', 'knob end', 'labia',
              'muff', 'nigger', 'nigga', 'penis', 'piss', 'piss', 'poop', 'prick', 'pube', 'pussy',
              'queer', 'scrotum', 'sex', 'shit', 's hit', 'slut', 'smegma', 'spunk', 'tosser',
               'retard', 'retards', 'twat', 'twats', 'vagina', 'wank', 'wanker', 'whore']

#load custom bad words
profanity.load_words(swear_words)

critical_train = [
    ('Cannot upload csv', 'neg'),
    ('Cannot access payment', 'neg'),
    ('Payment is not working', 'neg'),
    ('Tracking is not working', 'neg'),
    ('I cant track my parcel', 'neg'),
    ('your tracking shows delivered but I didnt receive my parcel', 'ing'),
    ('Site issue', 'neg'),
    ('claims process not working', 'neg'),
    ('i cant track my order online', 'neg'),
    ('no tracking', 'neg'),
    ('i cannot log in to myhermes account', 'neg'),
    ('I cannot process my quotes', 'neg'),
]
#passing training data into the constructor
cl = NaiveBayesClassifier(critical_train)

# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self):
        self.tweet_data = []

        # self.counter = 0

    def on_data(self, data):
        # pprint (data)
        # saveFile = io.open('tweet_raw.json', 'a', encoding='utf-8')co
        # thetweets = json.loads(data)
        print(json.loads(data))
        self.tweet_data.append(json.loads(data))

        result = 'neg'
        tweets = Htweets2()
        for x in self.tweet_data:
            tweets.tweet_timestamp = x['timestamp_ms']
            tweets.tweet_id = x['id']
            tweets.tweet_screenname = x['user']['screen_name']
            tweets.tweet_recount = x['retweet_count']
            tweets.tweet_favour_count = x['favorite_count']
            tweets.tweet_text = profanity.censor(x['text'])

            tweets.tweet_location = x['user']['location']
            tweets.tweet_media_entities = x['source']

            tweets.save()

            cl.classify(x['text'])
            if cl.classify(x['text']) == result:
                sense.set_pixels(detectionstate)
            else:
                pass


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
    stream.filter(track=['@myhermes'])
