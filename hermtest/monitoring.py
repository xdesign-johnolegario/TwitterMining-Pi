from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from .models import Htweet
from django.http import HttpResponse
import tweepy



conn = sqlite3.connect('/home/hermes/Documents/hermtest/rango.db'); # this is the connection to database
x = cursor()
consumer_key = " HenPKqsmggLlAApXJa31ml3Qq"
consumer_secret = "3HqTzdyHSjUCYkgmtPdYrnlWG159qaswexQKsd4x5Ttv6RcshV"
access_token = " 800388305623785476-VJF52W5A2hDRWJTg5apK7En1yRig8xk"
access_token_secret="VeSeMynKbSuvIEOqHKC5hoDcuEjrvZDcPaRpszbdyjFOU"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access,token, access_token_secret)
api = tweepy.API(auth)

class CustomStreamListener(tweepy.StreamListener):

    def on_status(self, status):
    
        try:
            print ("%s\t%s\t%s\t%s" % (status.createdAt, 
                                      status.tText,
                                      status.location 
                                      status.created_at
                                      status.in_reply_to_status 
                                      status.urls))
        cur.executemany("INSERT INTO Htweet(?, ?, ?)", (status.createdAt,
                                                        status.tText,
                                                        status.location,
                                                        status.in_reply_to_status
                                                        status.urls)
        except, Exception e
        print >> sys.derr, 'Encountered error with status code:', status_code
        return True

    def _init_(self, api):
        self.api = api
        super(tweepy.StreamListener, self)._init_()

   

    def on_timeout(self):
        print >> sts.derr, 'Timoeout...'
        return True


streaming_api = tweepy.streaming.Stream(auth, CustomStreamListener(), timeout=60)
print >> sys.derr, 'Filtering the public timeliine for "%s"' % (''.join(sys.argv[1:),)

streaming_api.filter(follow=None, track=Q)



"""
sapi = tweepy.streaming Stream(auth, CustomStreamListener(api))
sapi.filter(track=['hermes'])
"""
conn.close()
