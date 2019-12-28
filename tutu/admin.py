from django.contrib import admin
from django.utils.html import format_html

from django.db.models import Sum
from tutu.models import Tick

class TickAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'machine', 'date', 'number_of_successful_polls',
        'number_of_error_polls', 'total_time'
    ]
    ordering = ('-date', )
    readonly_fields = ("poll_result", )

    def total_time(self, tick):
        total = tick.pollresult_set.aggregate(x=Sum('seconds_to_poll'))['x']
        return "0" if not total else "%.2f" % total

    def number_of_successful_polls(self, tick):
        return tick.pollresult_set.exclude(success=False).count()

    def number_of_error_polls(self, tick):
        count = tick.pollresult_set.filter(success=False).count()
        if count > 0:
            return format_html("<span style='color:red'>%d</span>" % count)
        return count

    def poll_result(self, tick):
        lines = []
        for result in tick.pollresult_set.all():
            line = "<b>%s</b>: %s (took: %.2f)" % (
                result.metric_name, result.result, result.seconds_to_poll
            )
            if not result.success:
                line = "<span style='color: red'>%s</span>" % line
            lines.append(line)

        return format_html("<br>".join(lines))

admin.site.register(Tick, TickAdmin)
