import dis
import sys
from contextlib import contextmanager
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
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
    metric = None

    def __init__(self, actions, do_alert):
        self.actions = actions
        self.do_alert = do_alert

    @property
    def internal_name(self):
        return "%s_%s_%s" % (
            self.metric.internal_name,
            self.__class__.__name__,
            self.metric.make_mini_hash(lam_to_str(self.do_alert))
        )

    def alert_status(self):
        try:
            latest = self.metric.tick.AlertHistory.objects.filter(
                tick__machine=self.metric.tick.machine,
                alert_name=self.internal_name
            ).latest()
        except self.metric.tick.AlertHistory.DoesNotExist:
            return "off"
        return "on" if latest.alert_on else "off"

    def set_alert_on(self):
        if self.alert_status() == 'on':
            return
        return self.metric.tick.AlertHistory.objects.create(
            tick=self.metric.tick,
            alert_on=True,
            alert_name=self.internal_name
        )

    def set_alert_off(self):
        if self.alert_status() == 'off':
            return
        return self.metric.tick.AlertHistory.objects.create(
            tick=self.metric.tick,
            alert_on=False,
            alert_name=self.internal_name
        )

    def set_action(self, history, performed):
        if history:
            history.did_action = True
            history.actions_performed = "\n".join(performed)
            history.save()
            return

        self.metric.tick.AlertHistory.objects.create(
            tick=self.metric.tick,
            alert_on=True, did_action=True,
            alert_name=self.internal_name,
            actions_performed="\n".join(performed)
        )


    def perform(self, result, verbose):
        if self.do_alert(result):
            if verbose: print("*** Alert On: %s" % self.internal_name)
            history = self.set_alert_on()
            if self.should_alert():
                performed = []
                for alert_action in self.actions:
                    performed.append(alert_action.action(result, self.metric, verbose))
                self.set_action(history, performed)
        else:
            self.set_alert_off()
            if verbose: print("*** Alert off: %s" % self.internal_name)


class Once(AlertMode):
    def should_alert(self):
        return True

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
        if verbose: print("****** Sending email: %s" % self.addresses)
        send_mail(
            '[Tutu alert] %s' % metric.title,
            'This metric has triggered an alert: %s' % result,
            None,
            self.addresses,
            fail_silently=False,
        )
        return "Send emails to: %s" % self.addresses

class IRCAlert(AlertAction):
    pass

class DiscordAlert(AlertAction):
    pass
