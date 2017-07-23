


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from nose.tools import *
import sys
from pprint import pprint
from textblob.classifiers import PositiveNaiveBayesClassifier
from textblob.classifiers import NaiveBayesClassifier
import json
import sys, os, django

if sys.version_info[0] == 2:
    access = 'r'
    kwargs = {}
else:
    access = 'wt'
    kwargs = {'newline': ''}

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

redalertstate = [
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r,
r,r,r,r,r,r,r,r
]

sys.path.append("C:\Users\hisg316\Desktop\Htweetprod2")
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
    ('Cannot upload csv', 'alert'),
    ('Please help me guys @myhermes having issues with your online chat room.', 'alert'),
    ('Payment not working', 'alert'),
    ('Tracking not working', 'alert'),
    ('claims process not working', 'alert'),
    ('cannot log in to myhermes account', 'alert'),
    ('cannot process my quotes', 'alert'),
    ('website down', 'critical'),
    ('site down', 'critical'),
    ('website offline', 'critical'),
    ('site offline', 'critical'),
    ('website takendown', 'critical'),
    ('website broken', 'critical'),
    ('is your website down', 'critical'),
    ('when your website will be back online', 'critical'),
    ('Is your site still broken? I am just about to move to Collect plus.', 'critical')]

critical_train2 = [
    ('@ASOS should always use @DPD_UK instead as theyre actually reliable', 'neu'),
    ('should always use instead as theyre actually reliable', 'neu'),
    ('@LermanSchmidt: @TheVampsJames @myhermes My #TeenChoice vote for #ChoiceMusicGroup is @TheVampsband.', 'neu'),
    ('Do @myhermes ever deliver at a time before 6pm', 'neu'),
    ('@myhermes @boohoo Hey DM us your order number and we will happily check this out for you.', 'neu'),
    ('can u check ur dms pls', 'neu'),
    ('Have any other bloggers had a terrible experience with @myhermes where they just deliver our blogger mail into thin air! #fbloggers', 'neu'),
    ('either your courier is lying or they can move at the speed at which I blink', 'neu'),
    ('what does days even say ??? No contact number', 'neu'),
    ('can someone let me know at what time my order will be delivered by ??', 'neu'),
    ('tracking is down', 'neg'),
    ('tracking not working', 'neg'),
    ('I cannot process my quotes', 'neg'),
    ('Cannot access payment', 'neg')]


critical_train_neg = [
    'tracking is down',
    'tracking not working',
    'I cannot process my quotes',
    'Cannot access payment',
    'Payment is not working',
    'your login page is down',
    'cannot log in',
    'unable to login']

critical_train_ing =[
    'website is down',
    'website is broken'
    'website offline',
    'website takendown',
    'site offline',
    'is your website down',
    'when your website will be back online'
    'Is your site still broken? I am just about to move to Collect plus.']


neg_neutral = []
with open('C:\\Users\\hisg316\\Desktop\\Htweetprod2\\Htweets2\\neg_neutral.txt', 'r') as inputfile:
    for line in inputfile:
        neg_neutral.append(line.rstrip('\n'))
#pprint (neg_neutral)


ing_neutral = []
with open('C:\\Users\\hisg316\\Desktop\\Htweetprod2\\Htweets2\\ing_neutral.txt', 'r') as inputfile1:
    for line2 in inputfile1:
        ing_neutral.append(line2.rstrip('\n'))
#pprint (ing_neutral)

train = critical_train + critical_train2

#passing training data into the constructor
cl = NaiveBayesClassifier(critical_train)
cl2 = NaiveBayesClassifier(train)

# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self):
        self.tweet_data = []
        self.just_text = []
        # self.counter = 0

    def on_data(self, data):
        # pprint (data)
        # saveFile = io.open('tweet_raw.json', 'a', encoding='utf-8')co
        # thetweets = json.loads(data)
        print(json.loads(data))
        self.tweet_data.append(json.loads(data))

        tweets = Htweets2()
        for x in self.tweet_data:
                    self.just_text.append(x['text'])
                    #cl.classify(x['text'])
                    #result =
                    #result2 = 'ing' #if cl.classify(x['text']) == cl.labels() == 'ing' else 'none'
                    #result3 = 'normal' #if not (cl.classify(x['text']) == cl.labels() != result and cl.classify(x['text']) == cl.labels() != result2) else 'none'
                    tweets.tweet_timestamp = x['timestamp_ms']
                    tweets.tweet_id = x['id']
                    tweets.tweet_screenname = x['user']['screen_name']
                    tweets.tweet_recount = x['retweet_count']
                    tweets.tweet_favour_count = x['favorite_count']
                    tweets.tweet_text = profanity.censor(x['text'])

                    tweets.tweet_location = x['user']['location']
                    tweets.tweet_media_entities = x['source']


                    #critical_train2 = [(x['text']), 'norm']
                    #cl2 = NaiveBayesClassifier(critical_train2)

                    classifier = PositiveNaiveBayesClassifier(positive_set=critical_train_neg,
                                                              unlabeled_set=neg_neutral)
                    classifier1 = PositiveNaiveBayesClassifier(positive_set=critical_train_ing,
                                                               unlabeled_set=ing_neutral)
                    classifier.classify(x['text'])
                    classifier1.classify(x['text'])

                    if classifier.classify(x['text']) is True and cl.classify(x['text']) == 'alert':
                        print 'not normal - alert'
                        tweets.tweet_status = 'not normal'
                        tweets.tweet_score = 'alert'
                    elif classifier.classify(x['text']) is False:
                        print 'normal-no alert'
                        tweets.tweet_status = 'normal'
                        tweets.tweet_score = 'neutral'
                    elif cl2.classify(x['text']) == 'neu':
                        print 'normal-neutral'
                        tweets.tweet_score = 'neutral'
                        tweets.tweet_status = 'normal'
                    elif classifier1.classify(x['text']) is True and cl.classify(x['text']) == 'critical':
                        print 'not normal - critical'
                        tweets.tweet_status = 'not normal'
                        tweets.tweet_score = 'critical'
                    elif classifier1.classify(x['text']) is False:
                        print 'normal-no critical'
                        tweets.tweet_score = 'neutral'
                        tweets.tweet_status = 'normal'

                    tweets.save()

    #def gettext(self):
        #for tweets in self.tweet_data:
            #print(tweets["text"])


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
    #@sentiment_h'
    #testH17'