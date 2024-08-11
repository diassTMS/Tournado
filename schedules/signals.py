from django.db.models.signals import post_save
from .models import Schedule, Timings, Rules
from tournaments.models import Tournament
from django.dispatch import receiver

@receiver(post_save, sender=Tournament)
def create_sched(sender, instance, created, **kwargs):
    if created:
        sched = Schedule.objects.create(tournament=instance)
        sched.save()

@receiver(post_save, sender=Schedule)
def create_sched(sender, instance, created, **kwargs):
    if created:
        rules = [
            "The toss of a coin shall decide which team shall have the first push back or choice of end",
            "Match Ball: 1st named team to provide the match ball",
            "Clash of shirts: 2nd named team to change",
            "Scoring Win = 3 points Draw = 1 point Loss = 0 points",
            "If, at the end of the division matches teams are equal on points, the rankings will be decided by:",
            "1. Goal difference",
            "2. Goals scored",
            "3. Winner of match between tied teams",
            "4. Barrage of three penalty strokes",
            "5. Sudden death penalty strokes",
        ]

        for i in range(len(rules)):
            rule = Rules.objects.create(schedule=instance, rule=rules[i], order=(i+1))
            rule.save()
