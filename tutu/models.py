from django.db import models
from django.utils import timezone

import socket
import time
import json

class Tick(models.Model):
    machine = models.TextField()
    date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.machine, self.date)

    @classmethod
    def make_tick(cls, graphsets=[]):
        machine = socket.gethostname()
        tick_time = timezone.now()
        tick = cls.objects.create(
            machine=machine, date=tick_time
        )
        for graphset in graphsets:
            graphset_instance = graphset()
            t0 = time.time()
            result = graphset_instance.poll(tick_time)
            seconds = time.time() - t0
            PollResult.objects.create(
                graphset_name=graphset_instance.get_name(),
                tick=tick,
                data=json.dumps(result),
                seconds_to_poll=seconds
            )

class PollResult(models.Model):
    graphset_name = models.TextField()
    tick = models.ForeignKey(Tick)
    data = models.TextField()
    seconds_to_poll = models.FloatField()
