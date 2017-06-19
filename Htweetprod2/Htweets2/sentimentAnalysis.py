


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
import time
import tweepy
from tweepy import Stream
from textblob import TextBlob
import re
import json
from pprint import pprint
import matplotlib.pyplot as plt
import plotly
import plotly.plotly as py
from plotly.graph_objs import Data, Scatter, Stream
import plotly.tools as tls
import plotly.graph_objs as go
import datetime
import time


plotly.tools.set_credentials_file(username='johnobc', api_key='plhGjX9i1CNNeAQVhwNo', stream_ids=['cupc57a4go'])
stream_ids = tls.get_credentials_file()['stream_ids']

# Variables that contains the user credentials to access Twitter API
consumer_key = "2BOthmLtaHuGnVo7ughCVzXiC"
consumer_secret = "AbQHy55BGwjkQw3LMI9SWxuLVwDSugh44LG3KWMUlgZjpO0fs9"
access_token = "867693535256080384-ikcO1SX6U4P7VR2icMVBwJpT9bBtEQz"
access_token_secret = "GxfhL28aq0U0OHTBR7lDKaESBYT7dD1d6jZhpnuI6nM9A"

def calctime(a):
    return time.time() - a

positive = 0
negative = 0
compound = 0

count= 0
initime = time.time()
#plt.ion()


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self):
        self.tweet_data = []
        self.justtext = []


    def on_data(self, data):
        pprint (json.loads(data))
        global initime
        t = int(calctime(initime))

        all_data = json.loads(data)
        sentitweets = all_data['text'].encode("utf-8")
        sentitweets = " ".join(re.findall("[a-zA-Z]+", sentitweets))
        blob = TextBlob(sentitweets.strip())

        global positive
        global negative
        global compound
        global count

        count = count + 1
        senti = 0
        for sen in blob.sentences:
            senti = senti + sen.sentiment.polarity
            if sen.sentiment.polarity >= 0:
                positive = positive + sen.sentiment.polarity
            else:
                negative = negative + sen.sentiment.polarity
        compound = compound + senti
        print count
        print sentitweets.strip()
        print senti
        print t
        print str(positive) + '' + str(negative) + '' + str(compound)

        #data plot
        #x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        #y0 = positive
        y1 = compound
        y2 = negative

        stream_id = stream_ids[0]
        py.plot(Data([Scatter(x=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), y=positive,
                      stream = Stream(token=stream_id, maxpoints=100))]))

        stream = py.Stream(stream_id)
        stream.open()
        stream.write(dict(x=1, y=1))
        stream.close()

        tls.embed('streaming-demo', '12')
    def on_error(self, status):
        print status

if __name__ == '__main__':

    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = tweepy.Stream(auth, l)

    # This line filter Twitter Streams to capture data by the keywords: '@myhermes
    stream.filter(track=['@realDonaldTrump'])




