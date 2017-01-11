from rango.db import models

class Htweet(models.Model):
	createdAt = models.DateTimeField()
	tText = models.CharField(max_length=250)
	location = models.CharField(max_length=100)
    in_reply_to_status = models.charField(max_length=250)
	urls = models.URLField(max_length=200)
	
	

"""class Htproblems(model.Model):
    busername = models.ForeignKey(Album, on_delete=models.CASCADE)
	datetweet = models.DateTimeField()
	location = models.CharField(max_length=100)
	urls = models.URLField(max_length=200)
	tweets = models.CharField(max_legth=140)"""

#class Courier(model.Model):
     
