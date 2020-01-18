class Alert(object):
    def perform(self, result, metric, verbose):
        if verbose:
            print("Doing alert", metric)

class EmailAlert(Alert):
    def __init__(self, address):
        self.address = address

class IRCAlert(Alert):
    pass

class DiscordAlert(Alert):
    pass
