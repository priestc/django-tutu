from django.contrib import admin
from tutu.models import Tick

class TickAdmin(admin.ModelAdmin):
    list_display = ['machine', 'date', 'number_of_polls']
    ordering = ('-date', )

    def number_of_polls(self, tick):
        return tick.pollresult_set.count()

admin.site.register(Tick, TickAdmin)
