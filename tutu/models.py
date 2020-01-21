from __future__ import print_function

from django.db import models
from django.utils import timezone

import socket
import time
import json
from tutu.utils import get_installed_metrics, get_column_number_and_instance

class FakeException(BaseException):
    pass

class Tick(models.Model):
    machine = models.TextField()
    date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.machine, self.date)

    @classmethod
    def make_tick(cls, metrics=[], test=False, verbose=False, catch=True):
        machine = socket.gethostname()

        tick = cls.objects.create(
            machine=machine, date=timezone.now()
        )
        tick.AlertHistory = AlertHistory
        tick.PollResult = PollResult

        if not test:
            if verbose:
                print("Doing tick #%s" % tick.id)

        if catch:
            to_catch = Exception
        else:
            to_catch = FakeException

        for metric in metrics:
            metric.tick = tick

            if not test:
                if tick.id % (metric.poll_skip + 1) != 0:
                    if verbose:
                        print("%s: SKIPPED (took: %.2f)" % (
                            metric.internal_name, seconds
                        ))
                    continue

            t0 = time.time()
            success = True
            try:
                result = metric.poll()
            except to_catch as exc:
                result = "%s: %s" % (exc.__class__.__name__, str(exc))
                success = False

            seconds = time.time() - t0

            if verbose or test:
                if not success:
                    fail = "** FAILURE ** "
                else:
                    fail = ""
                print("%s: %s%s (took: %.2f)" % (
                    metric.internal_name,
                    fail, result, seconds
                ))
            if test:
                continue

            metric.perform_alert(result, verbose=verbose)

            PollResult.objects.create(
                metric_name=metric.internal_name,
                tick=tick,
                result=json.dumps(result) if success else result,
                success=success,
                seconds_to_poll=seconds
            )
        if test:
            tick.delete()

    @classmethod
    def old_make_matrix(cls, machine, to_json=False):
        t0 = timezone.now()
        ticks = cls.objects.filter(machine=machine).exclude(pollresult__isnull=True)
        rows = []
        current_tz = timezone.get_current_timezone()
        for tick in ticks.order_by('date'):
            row = [current_tz.normalize(tick.date).isoformat()]
            for metric in get_installed_metrics():
                pr = tick.pollresult_set.filter(metric_name=metric.internal_name, success=True)
                if pr.exists():
                    row.append(
                        metric.result_to_matrix(json.loads(pr.get().result))
                    )
                else:
                    row.append(None)
            rows.append(row)

        if to_json:
            return json.dumps(rows, indent=4)

        print("matrix took: %s" % (timezone.now() - t0))
        return rows

    @classmethod
    def make_matrix(cls, machine, to_json=False):
        t0 = timezone.now()
        column_numbers = get_column_number_and_instance()

        prs = PollResult.objects.filter(success=True).order_by('tick__date')
        prs = prs.filter(metric_name__in=column_numbers.keys())
        prs = prs.values('tick__date', 'result', 'metric_name')
        initialize_row = lambda: [None] * (len(column_numbers) + 1)
        current_tz = timezone.get_current_timezone()

        rows = []
        row = initialize_row()

        for pr in prs:
            date = current_tz.normalize(pr['tick__date']).isoformat()
            column_number, metric = column_numbers[pr['metric_name']]
            result = metric.result_to_matrix(json.loads(pr['result']))

            if not row[0]:
                row[0] = date

            elif row[0] != date:
                rows.append(row)
                row = initialize_row()
                row[0] = date

            row[column_number] = result

        rows.append(row)
        print("new matrix took: %s" % (timezone.now() - t0))
        return rows

class PollResult(models.Model):
    metric_name = models.TextField()
    tick = models.ForeignKey(Tick, on_delete=models.CASCADE)
    success = models.BooleanField()
    result = models.TextField()
    seconds_to_poll = models.FloatField()

    @classmethod
    def get_graph_data(cls, machine, metric):
        pr = cls.objects.filter(tick__machine=machine, metric_name=metric)
        pr = pr.filter(success=True).values_list('tick__date', 'result')
        current_tz = timezone.get_current_timezone()
        return {
            'x': [current_tz.normalize(item[0]) for item in pr],
            'y': [json.loads(item[1]) for item in pr]
        }

    def __unicode__(self):
        return "%s (%s)" % (self.metric_name, bool(self.success))

    class Meta:
        get_latest_by = 'tick__date'


class AlertHistory(models.Model):
    tick = models.ForeignKey(Tick, on_delete=models.CASCADE)
    alert_on = models.BooleanField()
    did_action = models.BooleanField(default=False)
    alert_name = models.TextField()
    actions_performed = models.TextField()

    class Meta:
        get_latest_by = 'tick__date'
