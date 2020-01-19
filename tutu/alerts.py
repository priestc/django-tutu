import dis
import sys
from contextlib import contextmanager
from cStringIO import StringIO
from django.core.mail import send_mail

@contextmanager
def captureStdOut(output):
    stdout = sys.stdout
    sys.stdout = output
    try:
        yield
    finally:
        sys.stdout = stdout

def lam_to_str(l):
    out = StringIO()
    with captureStdOut(out):
        dis.dis(l)
    return out.getvalue()

class AlertMode(object):
    def __init__(self, actions, do_alert):
        self.actions = actions
        self.do_alert = do_alert

    @property
    def internal_name(self):
        return "%s%s%s" % (
            self.metric.internal_name,
            self.__class__.__name__,
            lam_to_str(self.do_alert)
        )

    def perform(self, result, metric, verbose):
        if self.do_alert(result) and self.should_alert():
            if verbose: print("Doing alert: %s" % metric)
            for alert_action in self.actions:
                alert_action.action(result, metric, verbose)
        else:
            if verbose: print("Not doing alert: %s" % metric)


class Once(AlertMode):
    def should_alert(self):
        pass

class Every(AlertMode):
    def should_alert(self):
        return True

class Backoff(AlertMode):
    def should_alert(self):
        pass

#########################################################

class AlertAction(object):
    pass

class EmailAlert(AlertAction):
    def __init__(self, addresses):
        self.addresses = addresses

    def action(self, result, metric, verbose):
        send_mail(
            '[Tutu alert] %s' % metric.title,
            'This metric has triggered an alert: %s' % result,
            None,
            self.addresses,
            fail_silently=False,
        )

class IRCAlert(AlertAction):
    pass

class DiscordAlert(AlertAction):
    pass
