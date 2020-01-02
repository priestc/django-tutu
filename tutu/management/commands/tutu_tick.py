from django.core.management.base import BaseCommand, CommandError
from tutu.models import Tick
from tutu.utils import get_installed_metrics

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
        parser.add_argument(
            '--no-catch',
            action='store_true',
            help="Show output",
        )

    def handle(self, *args, **options):
        Tick.make_tick(
            get_installed_metrics(),
            verbose=options['verbose'],
            test=options['test'],
            catch=not options['no_catch']
        )
