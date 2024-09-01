from django.db.models.signals import post_save, post_delete
from .models  import League, LeagueEntry
from django.dispatch import receiver

@receiver(post_save, sender=LeagueEntry, weak=False)
def noTeams_increase(sender, instance, created, *args, **kwargs):
    if created:
        league = League.objects.get(pk=instance.league.id)
        teams = league.noTeams + 1
        League.objects.filter(pk=instance.league.id).update(noTeams=teams)

@receiver(post_delete, sender=LeagueEntry, weak=False)
def noTeams_decrease(sender, instance, *args, **kwargs):
    league = League.objects.get(pk=instance.league.id)
    teams = league.noTeams - 1
    League.objects.filter(pk=instance.league.id).update(noTeams=teams)