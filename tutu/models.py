from django.db import models
import datetime
import socket

class Tick(models.Model):
    machine = models.TextField()
    date = models.DateTimeField()

    @classmethod
    def make_tick(cls, graphsets=[]):
        machine = socket.gethostname()
        tick = cls.objects.create(
            machine=machine, date=datetime.datetime.now()
        )
        for graphset in graphsets:
            t0 = time.time()
            result = graphset.poll()
            seconds = time.time() - t0
            TickData.objects.create(
                tick=tick,
                data=json.dumps(result),
                seconds_to_poll=seconds
            )

class TickData(models.Model):
    tick = models.ForeignKey(Tick)
    data = models.TextField()
    seconds_to_poll = models.FloatField()
