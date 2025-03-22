from django.db import models
from tournaments.models import Tournament

class Schedule(models.Model):

    TIMED = [
            ('Centrally Timed', 'Centrally Timed'),
            ('Umpire Timed', 'Umpire Timed'),
        ]

    tournament = models.OneToOneField(Tournament, on_delete=models.CASCADE)
    timed = models.CharField(max_length=15, choices=TIMED, default="Centrally Timed")
    published = models.BooleanField(default=False)
    umpire_published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.tournament.name} Schedule'

class Rules(models.Model):
    rule = models.CharField(max_length=500)
    order = models.IntegerField()
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.rule}'

class Timings(models.Model):
    timing = models.CharField(max_length=500)
    order = models.IntegerField()
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.timing}'
    
class PitchNames(models.Model):
    name = models.CharField(max_length=500)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'


