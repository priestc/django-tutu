from __future__ import print_function

import dis
import sys
import subprocess

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

class Log(object):
    log_prefix = ""
    verbose = False

    def log(self, *a, **k):
        if self.verbose: print(self.log_prefix, *a, **k)

class AlertMode(Log):
    metric = None
    log_prefix = "***"

    def __init__(self, actions, do_alert, mute_after=False, notify_when_off=False):
        self.actions = actions
        self.do_alert = do_alert
        self.mute_after = mute_after
        self.notify_when_off = notify_when_off

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

    def set_alert_status(self, status="on"):
        if self.alert_status() == status:
            return
        return self.metric.tick.AlertHistory.objects.create(
            tick=self.metric.tick,
            alert_on=status == "on",
            alert_name=self.internal_name
        )

    def set_action(self, status, history, performed):
        if history:
            history.did_action = True
            history.actions_performed = "\n".join(performed)
            history.save()
            return

        self.metric.tick.AlertHistory.objects.create(
            tick=self.metric.tick,
            alert_on=status == "on", did_action=True,
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

    def do_actions(self, status, history, result):
        performed = []
        for alert_action in self.actions:
            alert_action.verbose = self.verbose
            performed.append(alert_action.action(
                result, self.metric, status, self
            ))
        self.set_action(status, history, performed)

    def perform(self, result):
        if self.do_alert(result):
            self.log("Alert On: %s" % self.internal_name)

            if self.mute_after:
                if self.count_actions() > self.mute_after:
                    self.log("Muting alert")
                    return

            first_on = self.set_alert_status("on")
            if first_on or self.should_do_action():
                self.do_actions("on", first_on, result)
        else:
            self.log("Alert off: %s" % self.internal_name)

            first_off = self.set_alert_status("off")
            if first_off and self.notify_when_off:
                self.do_actions("off", first_off, result)



class Once(AlertMode):
    def should_do_action(self):
        return False

class Every(AlertMode):
    def should_do_action(self):
        return True

class Backoff(AlertMode):

    def __init__(self, *args, **kwargs):
        if 'offset' in kwargs:
            self.offset = kwargs.pop("offset")
        else:
            self.offset = lambda x: 2**(x-1)

        super(Backoff, self).__init__(*args, **kwargs)

    def should_do_action(self):
        already_done = self.count_actions()
        offset = self.offset(already_done)
        previous = self.get_history().latest()
        msi_of_next_action = previous.tick.machine_seq_id + offset
        ticks_until = msi_of_next_action - self.metric.tick.machine_seq_id
        if ticks_until == 0:
            ticks_until = self.offset(already_done + 1)
        self.log("Ticks until next action:", ticks_until)
        return msi_of_next_action <= self.metric.tick.machine_seq_id

#########################################################

class AlertAction(Log):
    log_prefix = "******"

class EmailAlert(AlertAction):
    def __init__(self, addresses):
        self.addresses = addresses

    def action(self, result, metric, status, alert):
        self.log("Sending %s email: %s" % (
            status, self.addresses
        ))

        title = '[Tutu alert %s] %s on %s' % (
            status, metric.title, metric.tick.machine
        )
        body = 'This metric has triggered an alert %s: %s' % (status, result)

        send_mail(
            title, body, None, self.addresses, fail_silently=False,
        )
        return "Send emails to: %s" % self.addresses

class RunCommand(AlertAction):
    def __init__(self, command):
        self.command = command

    def action(self, result, metric, status, alert):
        filled_in_command = self.command.format(
            result=result, alert=alert, metric=metric, status=status,
            action=self
        )
        self.log("Command:", filled_in_command)
        output = subprocess.check_output(filled_in_command.split(" ")).decode("utf8")
        self.log("Output:", output)
        return filled_in_command + "\n" + output

class DiscordAlert(AlertAction):
    pass
