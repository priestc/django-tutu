from __future__ import print_function

from django.db import models
from django.utils import timezone

import socket
import time
import json
from tutu.utils import validate_graphset

class Tick(models.Model):
    machine = models.TextField()
    date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.machine, self.date)

    @classmethod
    def make_tick(cls, graphsets=[], test=False, verbose=False):
        machine = socket.gethostname()

        tick = cls.objects.create(
            machine=machine, date=timezone.now()
        )

        if not test:
            if verbose:
                print("Doing tick #%s" % tick.id)

        for item in graphsets:
            graphset = validate_graphset(item)
            graphset.tick = tick

            if not test:
                if tick.id % (graphset.poll_skip + 1) != 0:
                    if verbose:
                        print("%s: SKIPPED (took: %.2f)" % (
                            graphset.get_internel_name(), seconds
                        ))
                    continue

            t0 = time.time()
            success = True
            try:
                result = graphset.poll()
            except Exception as exc:
                result = "%s: %s" % (exc.__class__.__name__, str(exc))
                success = False

            seconds = time.time() - t0

            if verbose or test:
                if not success:
                    fail = "** FAILURE ** "
                else:
                    fail = ""
                print("%s: %s%s (took: %.2f)" % (
                    graphset.get_internel_name(),
                    fail, result, seconds
                ))
            if test:
                continue

            PollResult.objects.create(
                graphset_name=graphset.get_internel_name(),
                tick=tick,
                result=json.dumps(result) if success else result,
                success=success,
                seconds_to_poll=seconds
            )
        if test:
            tick.delete()

class PollResult(models.Model):
    graphset_name = models.TextField()
    tick = models.ForeignKey(Tick, on_delete=models.CASCADE)
    success = models.BooleanField()
    result = models.TextField()
    seconds_to_poll = models.FloatField()

    @classmethod
    def get_graph_data(cls, machine, graphset):
        pr = cls.objects.filter(tick__machine=machine, graphset_name=graphset)
        pr = pr.filter(success=True).values_list('tick__date', 'result')
        return {
            'x': [item[0] for item in pr],
            'y': [json.loads(item[1]) for item in pr]
        }

    def __unicode__(self):
        return "%s (%s)" % (self.graphset_name, bool(self.success))
