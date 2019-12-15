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
    def make_tick(cls, graphsets=[], test=False, verbose=False):
        machine = socket.gethostname()
        tick_time = timezone.now()

        if not test:
            tick = cls.objects.create(
                machine=machine, date=tick_time
            )
        
        for graphset in graphsets:
            graphset_instance = graphset()
            t0 = time.time()
            success = True
            try:
                result = graphset_instance.poll(tick_time)
            except Exception as exc:
                result = "%s: %s" % (exc.__class__.__name__, str(exc))
                success = False

            seconds = time.time() - t0

            if verbose or test:
                if not success:
                    fail = "** FAILURE ** "
                else:
                    fail = ""
                print "%s: %s%s (took: %.2f)" % (
                    graphset_instance.get_name(),
                    fail, result, seconds
                )
            if test:
                continue

            PollResult.objects.create(
                graphset_name=graphset_instance.get_name(),
                tick=tick,
                result=json.dumps(result) if success else result,
                success=success,
                seconds_to_poll=seconds
            )

class PollResult(models.Model):
    graphset_name = models.TextField()
    tick = models.ForeignKey(Tick)
    success = models.BooleanField()
    result = models.TextField()
    seconds_to_poll = models.FloatField()

    def __unicode__(self):
        return "%s (%s)" % (self.graphset_name, bool(self.success))
