from Htweets2.models import Htweets2
from django_cron import CronJobBase, Schedule

class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 5 # every 2 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "Htweetprod2.cron.MyCronJob",    # a unique code

    def do(self):
        oldtweets = Htweets2.objects.all()  # do your thing here
        oldtweets.delete()