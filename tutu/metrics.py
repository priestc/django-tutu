import os
import subprocess
import psutil
import datetime

class Metric(object):
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

    @property
    def previous_tick(self):
        from tutu.models import Tick
        self.Tick = Tick
        try:
            return Tick.objects.filter(machine=self.tick.machine).order_by("-date")[1]
        except IndexError:
            return None

    @property
    def previous_poll(self):
        from tutu.models import PollResult
        self.PollResult = PollResult
        try:
            return PollResult.objects.filter(metric_name=self.get_internal_name()).latest()
        except PollResult.DoesNotExist:
            return None

class Uptime(Metric):
    title = "System Uptime"
    yaxis_title = "Days"

    def poll(self):
        boot_date = datetime.datetime.fromtimestamp(psutil.boot_time())
        return (
            datetime.datetime.now() - boot_date
        ).total_seconds() / 86400.0

class OptimizedUptime(Metric):
    title = "Uptime (optimized)"

    def poll(self):
        this_uptime = Uptime().poll()
        previous_uptime = self.previous_poll.result

        if this_uptime > previous_uptime:
            self.previous_poll.delete()

        return this_uptime


class SystemLoad(Metric):
    yaxis_title = "Load Average"

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
        super(SystemLoad, self).__init__(*args, **kwargs)

    def poll(self):
        for directory in self.directories:
            raw = subprocess.check_output(['du', '-s', directory]).decode("utf8")

        return results
