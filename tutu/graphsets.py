import os
import subprocess

class Metric(object):
    title = ""

    def __init__(self, poll_skip=0):
        self.poll_skip = poll_skip

    def get_internel_name(self):
        name = self.internal_name_from_args()
        return self.__class__.__name__ + (name or "")

    def internal_name_from_args(self):
        return None

    def previous_tick(self):
        pass

    def previous_poll(self):
        pass


class Uptime(Metric):
    title = "System Uptime"

    def poll(self):
        raw = subprocess.check_output('uptime').decode("utf8").replace(',', '')
        days = int(raw.split()[2])
        if 'min' in raw:
            hours = 0
            minutes = int(raw[4])
        else:
            hours, minutes = map(int,raw.split()[4].split(':'))
        return days + hours / 24.0 + minutes / 1440.0

class OptimizedUptime(Metric):
    def poll(self):
        previous_uptime = self.previous_poll.result
        this_uptime = Uptime().poll()

        if this_uptime > previous_uptime:
            previous_poll.delete()

        return this_uptime


class SystemLoad(Metric):
    title = "System Load Average"

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
    def __init__(self, directories, *args, **kwargs):
        self.directories = directories
        super(SystemLoad, self).__init__(*args, **kwargs)

    def poll(self):
        for directory in self.directories:
            raw = subprocess.check_output(['du', '-s', directory]).decode("utf8")

        return results
