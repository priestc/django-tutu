import os
import subprocess
import psutil
import datetime
import json
import hashlib

from django.utils import timezone
from django.utils.functional import cached_property

class Metric(object):
    tick = None
    traces = [{"type": "scatter"}]

    @property
    def title(self):
        return self.get_internal_name()

    def __init__(self, poll_skip=0):
        self.poll_skip = poll_skip

    def get_internal_name(self):
        name = self.internal_name_from_args()
        return self.__class__.__name__ + (name or "")

    def internal_name_from_args(self):
        return None

    def make_special_tick(self, at_time, value):
        from tutu.models import Tick, PollResult
        t = Tick.objects.create(
            machine=self.tick.machine, date=at_time
        )
        PollResult.objects.create(
            tick=t, result=json.dumps(value), metric_name=self.get_internal_name(),
            seconds_to_poll=0, success=True
        )

    @cached_property
    def previous_tick(self):
        from tutu.models import Tick
        try:
            return Tick.objects.filter(machine=self.tick.machine).order_by("-date")[1]
        except IndexError:
            return None

    @cached_property
    def previous_poll(self):
        print("getting previous poll")
        from tutu.models import PollResult
        try:
            return PollResult.objects.filter(metric_name=self.get_internal_name()).latest()
        except PollResult.DoesNotExist:
            return None

class Uptime(Metric):
    title = "System Uptime"
    yaxis_title = "Days"
    traces = [{"type": "scatter"}]

    def poll(self):
        now = timezone.make_naive(self.tick.date) if self.tick else datetime.datetime.now()
        boot_date = datetime.datetime.fromtimestamp(psutil.boot_time())
        return (now - boot_date).total_seconds() / 86400.0

class OptimizedUptime(Metric):
    title = "System Uptime"
    yaxis_title = "Days"
    traces = [{"type": "scatter", "fill": 'tozeroy'}]

    def make_power_on(self, this_uptime):
        d = self.tick.date - datetime.timedelta(days=this_uptime)
        self.make_special_tick(d, 0)

    def make_power_off(self):
        d = self.previous_poll.tick.date + datetime.timedelta(seconds=1)
        self.make_special_tick(d, 0)

    def poll(self):
        uptime = Uptime()
        uptime.tick = self.tick
        this_uptime = uptime.poll()

        if not self.previous_poll:
            # first poll
            self.make_power_on(this_uptime)
        elif this_uptime > float(self.previous_poll.result):
            # extending uptime
            self.previous_poll.delete()
        else:
            # reboot detected
            self.make_power_off()
            self.make_power_on(this_uptime)

        return this_uptime


class SystemLoad(Metric):
    yaxis_title = "Load Average"
    traces = [{"type": "scatter"}]

    @property
    def title(self):
        minute = 1
        if self.position == 1:
            minute = 5
        if self.position == 2:
            minute = 15
        return "System Load Average (%s minute interval)" % minute

    def __init__(self, position=0, *args, **kwargs):
        if position > 2:
            raise ValueError("Position must not be greater than 2")
        self.position = position
        super(SystemLoad, self).__init__(*args, **kwargs)

    def internal_name_from_args(self):
        if self.position:
            return "P%d" % self.position

    def poll(self):
        return os.getloadavg()[self.position]

class DirectorySize(Metric):
    yaxis_title = "Kilobytes"

    def __init__(self, directories, *args, **kwargs):
        self.directories = directories
        super(DirectorySize, self).__init__(*args, **kwargs)

    def mini_hash(self, directory):
        return hashlib.sha256(directory.encode()).hexdigest()[:6]

    def poll(self):
        results = {}
        for directory in self.directories:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    # skip if it is symbolic link
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)

            results[self.mini_hash(directory)] = total_size

        return results
