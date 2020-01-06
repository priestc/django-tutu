from django.http import JsonResponse, Http404
from django.template.response import TemplateResponse
from tutu.models import Tick, PollResult
from tutu.utils import get_metrics_from_names

def list_machines(request):
    machine_list = list(Tick.objects.values_list("machine", flat=True).distinct())
    return TemplateResponse(request, "list_machines.html", locals())

def show_machine_graphs(request, machine):
    ticks = Tick.objects.filter(machine=machine)
    if not ticks.exists():
        raise Http404("Machine not found")
    metric_list = get_metrics_from_names(
        ticks.values_list('pollresult__metric_name', flat=True).distinct()
    )
    return TemplateResponse(request, "show_graphs.html", locals())

def get_graph_data(request, machine, metric):
    ticks = Tick.objects.filter(machine=machine)
    if not ticks.exists():
        raise Http404("Machine not found")
    results = ticks.filter(pollresult__metric_name=metric)
    if not results.exists():
        raise Http404("Metric not found")

    return JsonResponse(PollResult.get_graph_data(machine, metric))

def get_matrix(request, machine):
    ticks = Tick.objects.filter(machine=machine)
    if not ticks.exists():
        raise Http404("Machine not found")
    return JsonResponse({'matrix': Tick.make_matrix(machine)})
