from django.http import JsonResponse, Http404
from django.template.response import TemplateResponse
from tutu.models import Tick, PollResult

def list_machines(request):
    machine_list = list(Tick.objects.values_list("machine", flat=True).distinct())
    return TemplateResponse(request, "list_machines.html", locals())

def show_machine_graphs(request, machine):
    ticks = Tick.objects.filter(machine=machine)
    if not ticks.exists():
        raise Http404("Machine not found")
    graphset_list = ticks.values_list('pollresult__graphset_name', flat=True).distinct()
    return TemplateResponse(request, "show_graphs.html", locals())

def get_graph_data(request, machine, graphset):
    ticks = Tick.objects.filter(machine=machine)
    if not ticks.exists():
        raise Http404("Machine not found")
    results = ticks.filter(pollresult__graphset_name=graphset)
    if not results.exists():
        raise Http404("Graphset not found")

    return JsonResponse(PollResult.get_graph_data(machine, graphset))
