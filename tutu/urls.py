from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

from tutu.views import list_machines, show_machine_graphs, get_graph_data, get_matrix

urlpatterns = [
    url(r'^$', list_machines, name="list_machines"),
    url(r'^(?P<machine>[\w\.-]+)$', show_machine_graphs, name="show_machine_graphs"),
    url(r'^(?P<machine>[\w\.-]+)/matrix$', get_matrix, name='get_matrix'),
    url(r'^(?P<machine>[\w\.-]+)/(?P<metric>\w+)', get_graph_data, name='get_graph_data'),
]
