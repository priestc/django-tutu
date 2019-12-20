from django.http import HttpResponse
from tutu.models import Tick

def list_machines(request):
    machines = list(Tick.objects.values_list("machine", flat=True).distinct())
    return HttpResponse("list machines: " + str(machines))

def show_machine_graphs(request, machine):
    graphsets = [validate_graphset(x) for x in settings.INSTALLED_GRAPHSETS}]
    return HttpResponse("show machine graphs")

def get_graph_data(request, machine, graphset):
    return HttpResponse("get graph data for " + machine + " " + graphset)
