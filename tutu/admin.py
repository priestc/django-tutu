from django.contrib import admin
from tutu.models import Tick

class TickAdmin(admin.ModelAdmin):
    list_display = ['machine', 'date', 'number_of_polls']
    ordering = ('-date', )
    readonly_fields = ("poll_result", )

    def number_of_polls(self, tick):
        return tick.pollresult_set.count()

    def poll_result(self, tick):
        lines = []
        #import ipdb; ipdb.set_trace()
        for result in tick.pollresult_set.all():
            if result.success:
                lines.append(
                    "<b>%s</b>: %s" % (result.graphset_name, result.success)
                )
            else:
                lines.append(
                    "<span style='color: red'><b>%s</b>: %s</span>" % (
                        result.graphset_name, result.error
                ))
        return "<br>".join(lines)
    poll_result.allow_tags = True

admin.site.register(Tick, TickAdmin)
