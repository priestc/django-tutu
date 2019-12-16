from django.core.management.base import BaseCommand, CommandError
from tutu.models import Tick
from django.conf import settings

class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help="Test all installed graphsets (does not save the results)",
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help="Show output",
        )

    def handle(self, *args, **options):
        Tick.make_tick(
            settings.INSTALLED_GRAPHSETS,
            verbose=options['verbose'],
            test=options['test']
        )
