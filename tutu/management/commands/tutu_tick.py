from django.core.management.base import BaseCommand, CommandError
from tutu.models import Tick
from django.conf import settings

class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        Tick.make_tick(settings.INSTALLED_GRAPHSETS)
