from tutu.metrics import Metric
import datetime
from django.conf import settings

def validate_metric(metric):
    if isinstance(metric, Metric):
        return metric
    elif isinstance(metric, type) and issubclass(metric, Metric):
        return metric()
    else:
        raise ValueError("Must be a Metric class or instance")

def get_installed_metrics():
    metrics = []
    for item in settings.INSTALLED_TUTU_METRICS:
        metrics.append(validate_metric(item))
    return metrics

def get_metric_from_name(name):
    for metric in get_installed_metrics():
        if name == metric.internal_name:
            return metric

def get_metrics_from_names(metric_names):
    metric_list = []
    for metric in get_installed_metrics():
        if metric.internal_name in metric_names:
            metric_list.append(metric)
    return metric_list

def get_column_number_and_instance():
    column_numbers = {}
    for i, metric in enumerate(get_installed_metrics()):
        column_numbers[metric.internal_name] = [i+1, metric]
    return column_numbers

######################################################
######################################################

def make_test_ticks(start_ago=datetime.timedelta(days=30)):
    from tutu.models import Tick
    now = datetime.datetime.now()
    target = now - start_ago
    while(target < now):
        Tick.objects.create(date=target, machine="TestMachine")
        target += datetime.timedelta(minutes=5)

def make_poll_results(metrics):
    import random
    from tutu.models import Tick, PollResult
    for tick in Tick.objects.all():
        for item in metrics:
            metric = validate_metric(item)
            result = random.random()
            PollResult.objects.create(
                tick=tick,
                metric_name=metric.internal_name,
                result=result,
                success=True,
                seconds_to_poll=1
            )
