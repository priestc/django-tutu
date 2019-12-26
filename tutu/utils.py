from tutu.graphsets import Graphset
import datetime
from django.conf import settings

def validate_graphset(graphset):
    if isinstance(graphset, Graphset):
        return graphset
    elif isinstance(graphset, type) and issubclass(graphset, Graphset):
        return graphset()
    else:
        raise ValueError("Must be a Graphset class or instance")


def get_graphset_from_name(name):
    for item in settings.INSTALLED_GRAPHSETS:
        graphset = validate_graphset(item)
        if name == graphset.get_name():
            return graphset


def make_test_ticks(start_ago=datetime.timedelta(days=30)):
    from tutu.models import Tick
    now = datetime.datetime.now()
    target = now - start_ago
    while(target < now):
        Tick.objects.create(date=target, machine="TestMachine")
        target += datetime.timedelta(minutes=5)

def make_poll_results(graphsets):
    import random
    from tutu.models import Tick, PollResult
    for tick in Tick.objects.all():
        for item in graphsets:
            graphset = validate_graphset(item)
            result = random.random()
            PollResult.objects.create(
                tick=tick,
                graphset_name=graphset.get_name(),
                result=result,
                success=True,
                seconds_to_poll=1
            )
