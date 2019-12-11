import os
import subprocess

class Graphset(object):
    pass


class Uptime(Graphset):
    def poll(self, tick_time):
        raw = subprocess.check_output('uptime').decode("utf8").replace(',', '')
        days = int(raw.split()[2])
        if 'min' in raw:
            hours = 0
            minutes = int(raw[4])
        else:
            hours, minutes = map(int,raw.split()[4].split(':'))
        #totalsecs = ((days * 24 + hours) * 60 + minutes) * 60
        return days + hours / 24.0 + minutes / 3600.0

class SystemLoad(Graphset):
    def poll(self, tick_time):
        return os.getloadavg()[0]
