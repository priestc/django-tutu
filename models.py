from django.db import model

class Tick(models.Model):
    date = models.DateTimeField()

class TickData(models.Model):
    tick = models.ForeignKey(Tick)
    data = models.TextField()
    seconds_to_poll = models.FloatField()
