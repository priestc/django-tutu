from __future__ import division

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
    internal_name = None
    title = None

    def make_title(self):
        return self.title or self.internal_name

    def __init__(self, poll_skip=0, internal_name=None, title=None, alerts=[]):
        self.internal_name = internal_name or self.make_default_internal_name()
        self.title = title or self.make_title()
        self.poll_skip = poll_skip
        [setattr(alert, 'metric', self) for alert in alerts]
        self.alert_modes = alerts

    def perform_alert(self, result, verbose=False):
        result = self.result_to_matrix(result)
        for alert in self.alert_modes:
            alert.perform(result, verbose)


    def make_default_internal_name(self):
        name = self.internal_name_from_args()
        return self.__class__.__name__ + (name or "")

    def internal_name_from_args(self):
        if not self.__dict__:
            return ""
        sorted_d = sorted(self.__dict__.items(), key=lambda x: x[0])
        return "_" + self.make_mini_hash(
            ''.join("%s%s" % (k,v) for k,v in sorted_d)
        )

    def make_mini_hash(self, directory):
        return hashlib.sha256(directory.encode()).hexdigest()[:6]

    def make_special_tick(self, at_time, value):
        t = self.tick.__class__.objects.create(
            machine=self.tick.machine, date=at_time
        )
        self.tick.PollResult.objects.create(
            tick=t, result=json.dumps(value), metric_name=self.internal_name,
            seconds_to_poll=0, success=True
        )

    @cached_property
    def previous_tick(self):
        try:
            return self.tick.__class__.objects.filter(machine=self.tick.machine).order_by("-date")[1]
        except IndexError:
            return None

    @cached_property
    def previous_poll(self):
        try:
            return self.tick.PollResult.objects.filter(metric_name=self.internal_name).latest()
        except self.tick.PollResult.DoesNotExist:
            return None

    def result_to_matrix(self, result):
        return result

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
            if self.previous_poll.result != "0":
                self.previous_poll.delete()
        else:
            # reboot detected
            self.make_power_off()
            self.make_power_on(this_uptime)

        return this_uptime


class SystemLoad(Metric):
    yaxis_title = "Load Average"
    traces = [{"type": "scatter"}]

    def make_title(self):
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
    yaxis_title = "_bytes"

    @property
    def traces(self):
        returned = []
        for directory in self.directories:
            last_dir = self.get_path_title(directory)
            returned.append({"type": "scatter", "name": last_dir})
        return returned

    def get_path_title(self, directory):
        if directory.endswith("/"):
            directory = directory[:-1]
        return directory.split("/")[-1]

    def __init__(self, directories, *args, **kwargs):
        self.directories = directories
        self.mini_hashes = [self.make_mini_hash(d) for d in directories]
        super(DirectorySize, self).__init__(*args, **kwargs)

    def poll(self):
        results = {}
        for i, directory in enumerate(self.directories):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    # skip if it is symbolic link
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)

            results[self.mini_hashes[i]] = total_size

        return results

    def result_to_matrix(self, result):
        column = []
        for minihash in self.mini_hashes:
            column.append(result.get(minihash, None))
        return column


class DiskSpace(Metric):
    yaxis_title = "_bytes"

    def make_title(self):
        if self.dimension.endswith("used"):
            return "Disk Space Used"
        return "Disk Space Free"

    @property
    def traces(self):
        returned = []
        for device in self.devices:
            returned.append({"type": "scatter", "name": device})
        return returned

    def __init__(self, devices, dimension='free', *args, **kwargs):
        self.devices = devices
        self.dimension = dimension
        if dimension.startswith("percentage"):
            self.yaxis_title = "Percent"
        super(DiskSpace, self).__init__(*args, **kwargs)

    def parse_df(self):
        raw = subprocess.check_output(['df', '-k']).decode("utf8").split("\n")
        result = {}
        for line in raw[1:-1]:
            splitted = list(filter(lambda x: x != '', line.split(" ")))
            if len(splitted) > 9:
                continue
            result[splitted[0]] = {
                'free': int(splitted[3]) * 1024,
                'used': int(splitted[2]) * 1024
            }
        return result

    def poll(self):
        df = self.parse_df()
        results = {}
        for device in self.devices:
            if self.dimension in ['free', 'used']:
                results[device] = df[device][self.dimension]
                continue

            all = (df[device]['used'] + df[device]['free'])

            if self.dimension == 'percentage_free':
                results[device] = 100 * df[device]['free'] / all
            elif self.dimension == 'percentage_used':
                results[device] = 100 * df[device]['used'] / all

        return results

    def result_to_matrix(self, result):
        column = []
        for device in self.devices:
            column.append(result.get(device, None))
        return column

class Memory(Metric):
    yaxis_title = "_bytes"

    def make_title(self):
        if self.dimension.endswith("used"):
            return "Memory Used"
        return "Memory Free"

    def __init__(self, dimension='free', *args, **kwargs):
        self.dimension = dimension
        if dimension.startswith("percentage"):
            self.yaxis_title = "Percent"
        super(Memory, self).__init__(*args, **kwargs)

    def poll(self):
        mem = psutil.virtual_memory()
        if self.dimension == 'percentage_used':
            return mem.percent
        if self.dimension == 'percentage_free':
            return 100 - mem.percent
        if self.dimension == 'free':
            return mem.available

        return getattr(mem, self.dimension)

class CPU(Metric):
    yaxis_title = "Percent"

    def make_title(self):
        if self.dimension.endswith("used"):
            return "CPU Percentage Used"
        return "CPU Percentage Free"

    def __init__(self, dimension='percentage_used', *args, **kwargs):
        self.dimension = dimension
        super(CPU, self).__init__(*args, **kwargs)

    def poll(self):
        mem = psutil.virtual_memory()
        if self.dimension == 'percentage_used':
            return psutil.cpu_percent()
        if self.dimension == 'percentage_free':
            return 100 - psutil.cpu_percent()
