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

    def __init__(self, actions, do_alert, mute_after=False):
        self.actions = actions
        self.do_alert = do_alert
        self.mute_after = mute_after

    @property
    def internal_name(self):
        return "%s_%s_%s" % (
            self.metric.internal_name,
            self.__class__.__name__,
            self.metric.make_mini_hash(lam_to_str(self.do_alert))
        )

    def get_history(self):
        return self.metric.tick.AlertHistory.objects.filter(
            tick__machine=self.metric.tick.machine,
            alert_name=self.internal_name
        )

    def alert_status(self):
        try:
            latest = self.get_history().latest()
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

    def count_actions(self):
        actions = 0
        for h in self.get_history().order_by('-tick__date').values('alert_on').iterator():
            if not h['alert_on']:
                break
            actions += 1
        return actions

    def perform(self, result, verbose):
        if self.do_alert(result):
            if verbose: print("*** Alert On: %s" % self.internal_name)

            if self.mute_after:
                if self.count_actions() > self.mute_after:
                    if verbose: print("****** Muting alert")
                    return

            first_on = self.set_alert_on()

            if first_on or self.should_do_action():
                performed = []
                for alert_action in self.actions:
                    performed.append(alert_action.action(result, self.metric, verbose))
                self.set_action(first_on, performed)
        else:
            self.set_alert_off()
            if verbose: print("*** Alert off: %s" % self.internal_name)


class Once(AlertMode):
    def should_do_action(self):
        return False

class Every(AlertMode):
    def should_do_action(self):
        return True

class Backoff(AlertMode):
    def should_do_action(self):
        already_done = self.count_actions()
        offset = 2 ** (already_done - 1)
        previous = self.get_history().latest()
        msi_of_next_action = previous.tick.msi + offset
        return msi_of_next_action == self.metric.tick.machine_seq_id

#########################################################

class AlertAction(object):
    pass

class EmailAlert(AlertAction):
    def __init__(self, addresses):
        self.addresses = addresses

    def action(self, result, metric, verbose):
        if verbose: print("****** Sending email: %s" % self.addresses)
        return "Send emails to: %s" % self.addresses
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
