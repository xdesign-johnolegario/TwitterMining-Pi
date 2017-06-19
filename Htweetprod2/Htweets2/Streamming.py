


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from nose.tools import *
from textblob.classifiers import PositiveNaiveBayesClassifier
from textblob.classifiers import NaiveBayesClassifier
import json

import sys, os, django



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
    ('when your website will be back online', 'critical')]

critical_train_neg = [
    'tracking is down',
    'tracking not working',
    'I cannot process my quotes',
    'Cannot access payment',
    'Payment is not working',
    'your login page is down',
    'cannot log in',
    'unable to login',
    'when your website will be back online']

neg_neutral = [
    'unable to upload csv today',
    'tracking says it supposed to be delievered but it isnt',
    'Not delivered and no info on tracking.',
    'My tracking details say my courier should deliver today',
    'can i get an update on tracking number',
    'No progress on the online tracker',
    'your login page is down.Please sort this ASAP',
    'cant login to my account to book parcels in, Whats happening',
    'is there a problem with your site again today not able to login',
    'your couriers left a blank card AGAIN so no unfortunately I dont have any tracking number etc but sure would like my blender pls',
    'urgent enquiry about my delivery. Have sent DM please can you update me Asap',
    'imagine ordering a parcel, having it lost and then not being able to contact someone to resolve the issue appalling',
    '@myhermes @ASOS_HeretoHelp @MotelRocks @KurtGeiger @HollisterCo @HollisterCoHelp @KurtGeigerHelp',
    '@TeaPartyBeauty @boohoo_cshelp @myhermes For me it depends what time I order as to who delivers! Most of the time',
    '@AlohaKirstie @boohoo_cshelp @myhermes I stopped paying for asos premier when they started using Hermes so switched,',
    '@aliceedmonds99 I understand why ....']

critical_train_ing =[
    'website is down',
    'website is broken']

ing_neutral = [
    'the website is having issues  I cant get quotes out ',
    'is your system down cant get pass login screen or book manually as a new user',
    'can you tell me if your website is down at the minute, ive not been able to get on it since last night',
    'Is your website down again',
    'package has gone missing',
    'Spoke to a lovely agent who was very helpful though',
    'Absolutely disgusting service. Damaged my plastic item',
    'why did your courier leave my parcel with a random house',
    'Hi, a courier should have collected my parcel yesterday but did not turn up',
    'Thanks for declaring our package lost! That is one #ruinedwedding day! #lostpackage #badcustomerservice',
    'parcel been out for delivery for 3 days and no correspondence from them at all.',
    'Thank you',
    'Ive sent it via DM. Please let me know',
    'how am I meant to contact you or your driver when he doesnt leave a contact number? Even when asked to! Terrible service',
    'They r so bad',
    'Ughhh! And never reply. Shall we protest!',
    'they are so bad',
    'your courier is a liar, no delivery attempt was made, I was home all day, wheres my parcel',
    'Still no response since yesterday DMd multiple times ??? This is not helpful',
    'inadministrationsoonhopefully',
    'in administration soon hope fully',
    'Hi can you confirm where my parcel is please? It didnt arrive yesterday despite being home. Order No is ',
    'have the most useless live chat system. All they ever do is tell you to wait another 24 hours &amp; cant tell you a single detail',
    'the last 2 deliveries have been left in a secure porch,I dont have 1. please ensure',
    'Why is your customer service set up so that nothing gets resolved. Is it because youre so incompetent',
    'I dont want you FAQ page, I an actual person to talk to me and get my parcel delivered.',
    'AND I wrecked a nail by shredding the tube from the top down to the dent so I could get the goods out wit',
    'Come on I want to play my new  vinyl its not quite the same in Spotify',
    'Thoroughly detailed delivery slip from. Have no idea who this is for (its a shared house) or how to arrange redelivery. Help pls!',
    'MY PARCEL got delivered to somebody else? Called different myhermes offices and no one can help! You must know who you gave it'
    'post Card though your door saying theyve left a parcel in your porch but you dont have a porch... or the parcel!',
    'Another parcel of mine has now been lost - tracking says stuck in the hub since 7th June? Chat service cut me off and phone service faulty',
    'Yay! My @boohoo stuff has arrived but Im not happy that the packaging absolutely stinks of cigarette smoke  Im not impressed!!!',
    'Hi, we are responding to messages in chronological order so we should be in touch soon',
    'we love your service and would like to establish a partnership with our members club. Who can we contact',
    'posted through letterbox',
    'Disgusted myhermes ordered shoes 4 Nans funeral Mon &amp paid 4 next day delivery. Stayed in 2day 4 delivery',
    'Live chat just ended the chat as they washed hands off delivery its their INCOMPETENT courier WHERE IS MY PARCEL',
    'Retailers shouldnt use as they are USELESS! @DPD_UK are brilliant, never had a problem. Give hour time slot &amp; always turns up!',
    'hi put the wrong postcode for an order that should be delivered by you guys today. Put home postcode not work but work address',
    'Yes there is but Ill send it again',
    'I believe @myhermes are secretly stock piling goods that they say get delivered but dont #oneforyouoneforme',
    'why are our packages just being left outside for someone to take? We are in the house! Knocking doesnt take 2 seconds!',
    'WORST company Ive ever dealt with',
    'What is their argument?',
    'should not be "makes delivery easy" but "causes headaches easy',
    'trying to locate 2 parcels and tracking number is invalid - urgently need someone to get back to me ASAP',
    '@ASOS_HeretoHelp',
    'What we all see when you open your mouth... https://t.co/2wsVOH0Aau',
    'can you respond to my DM please -order said it was delivered yesterday and it wasnt.',
    'delivery note  Behind Bin - not any more on this busy street, thanks Caroline. Appalling delivery standards',
    'Shocking service from these amateurs agn! @asos pls stop using them. Delivery driver blatantly lied &amp; didnt even attmpt delivery!',
    'Have you contacted your post office? They normally leave mine there, if Im not in x',
    'HAD REPLY WHAT IS NOT COVERED BY YOU CUSTOMERS RISK ONLY WHEN YOUR STAFF DELIBERALTY KICKED NOT JUST 1 BUT 2 BOXES 2 DAYS APART',
    'can you DM me your order details',
    'TAKE HOURS, DAYS, OVER A WEEK TO DEAL WITH ANY ISSUES. SEE HOW LONG IT TAKES TO ANSWER MY TWEETS #WORSTCOMPANYEVER',
    'Ugh...Post office then',
    'are just the worse! -- Ill have to just shop at another retailer that doesnt use them. (60 order canceled)',
    '@AlohaKirstie @boohoo_cshelp @myhermes Its beyond a joke now. The fact that I now cant shop places that use Hermes',
    '@TeaPartyBeauty @boohoo_cshelp @myhermes (For ASOS)',
    '@TeaPartyBeauty @boohoo_cshelp @myhermes For me it depends what time I order as to who delivers! Most of the time',
    '@AlohaKirstie @boohoo_cshelp @myhermes I stopped paying for asos premier when they started using Hermes so switched,',
    '@aliceedmonds99 I understand why ....',
    '@myhermes @ASOS_HeretoHelp @MotelRocks @KurtGeiger @HollisterCo @HollisterCoHelp @KurtGeigerHelp']


#passing training data into the constructor
cl = NaiveBayesClassifier(critical_train)

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

                    """
                    cl.classify(x['text'])
                    if cl.classify(x['text']) == 'neg':
                        print 'alert'
                        tweets.tweet_score = 'alert'
                    else:
                        print 'critical'
                        tweets.tweet_score = 'critical' """

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
                    elif classifier1.classify(x['text']) is True and cl.classify(x['text']) == 'critical':
                        print 'not normal - critical'
                        tweets.tweet_status = 'not normal'
                        tweets.tweet_score = 'critical'
                    elif classifier1.classify(x['text']) is False:
                        print 'normal-no critical'
                        tweets.tweet_score = 'neutral'
                        tweets.tweet_status = 'normal'

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
    stream.filter(track=['@myhermes'])
    #@sentiment_h'
    #testH17'