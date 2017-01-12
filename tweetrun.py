import time
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import os
import io

consumer_key = "dAJxDkO2T5sMzDBtuz5LN9ORw"
consumer_secret = "L5e2TYAI2yZX2JuwmFfXZV23KQ5GGqe3xOkVf7c8HP2lvM7XgC"
access_token = "800388305623785476-Q2ToEqMguIZhbdhtm9P2ODg21e8F1Ep"
access_token_secret="DTilA2WWlSgy9pfI6iXrGFyYB6YHX0UAIzXci0JhAvIPN"
start_time = time.time()
keyword_list = ['hermes', 'parcel']

class listener(StreamListener):

	def __init__(self, start_time, time_limit=60):
 
		self.time = start_time
		self.limit = time_limit
		self.tweet_data = []
 
	def on_data(self, data):
 
		saveFile = io.open('raw_tweets.json', 'a', encoding='utf-8')
 
		while (time.time() - self.time) < self.limit:
 
			try:
 
				self.tweet_data.append(data)
 
				return True
 
 
			except BaseException, e:
				print 'failed ondata,', str(e)
				time.sleep(5)
				pass
 
		saveFile = io.open('raw_tweets.json', 'w', encoding='utf-8')
		saveFile.write(u'[\n')
		saveFile.write(','.join(self.tweet_data))
		saveFile.write(u'\n]')
		saveFile.close()
		exit()
 
	def on_error(self, status):
 
		print statuses

auth = OAuthHandler(consumer_key, consumer_secret) #OAuth object
auth.set_access_token(access_token, access_token_secret)
 
 
twitterStream = Stream(auth, listener(start_time, time_limit=20)) #initialize Stream object with a time out limit
twitterStream.filter(track=keyword_list, languages=['en'])  #call the filter method to run the Stream Object