import os
import subprocess

class Graphset(object):

    def __init__(self, poll_skip=0):
        self.poll_skip = poll_skip

    def get_name(self):
        name = self.name_from_args()
        return self.__class__.__name__ + (name or "")

    def name_from_args(self):
        return None

class Uptime(Graphset):
    def poll(self, tick_time):
        raw = subprocess.check_output('uptime').decode("utf8").replace(',', '')
        days = int(raw.split()[2])
        if 'min' in raw:
            hours = 0
            minutes = int(raw[4])
        else:
            hours, minutes = map(int,raw.split()[4].split(':'))
        return days + hours / 24.0 + minutes / 1440.0

class SystemLoad(Graphset):

    def __init__(self, position=0, *args, **kwargs):
        if position > 2:
            raise ValueError("Position must not be greater than 2")
        self.position = position
        super(SystemLoad, self).__init__(*args, **kwargs)

    def name_from_args(self):
        if self.position:
            return "P%d" % self.position

    def poll(self, tick_time):
        return os.getloadavg()[self.position]
