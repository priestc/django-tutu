from django.contrib import admin
from django.db.models import Sum
from tutu.models import Tick

class TickAdmin(admin.ModelAdmin):
    list_display = [
        'machine', 'date', 'number_of_successful_polls',
        'number_of_error_polls', 'total_time'
    ]
    ordering = ('-date', )
    readonly_fields = ("poll_result", )

    def total_time(self, tick):
        total = tick.pollresult_set.aggregate(x=Sum('seconds_to_poll'))
        return "%.2f" % total['x']

    def number_of_successful_polls(self, tick):
        return tick.pollresult_set.exclude(success='').count()

    def number_of_error_polls(self, tick):
        count = tick.pollresult_set.filter(success='').count()
        if count > 0:
            return "<span style='color:red'>%d</span>" % count
        return count
    number_of_error_polls.allow_tags = True

    def poll_result(self, tick):
        lines = []
        for result in tick.pollresult_set.all():
            if result.success:
                lines.append(
                    "<b>%s</b>: %s (took: %.2f)" % (result.graphset_name, result.success,
                    result.seconds_to_poll
                ))
            else:
                lines.append(
                    "<span style='color: red'><b>%s</b>: %s (took: %.2f)</span>" % (
                        result.graphset_name, result.error,
                        result.seconds_to_poll
                ))
        return "<br>".join(lines)
    poll_result.allow_tags = True

admin.site.register(Tick, TickAdmin)
