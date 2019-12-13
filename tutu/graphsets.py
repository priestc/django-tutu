import os
import subprocess

class Graphset(object):
    def get_name(self):
        return self.__class__.__name__

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
    def poll(self, tick_time):
        return os.getloadavg()[0]
