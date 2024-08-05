from django.db.models.signals import post_save, post_delete
from .models  import Entry, Tournament
from django.dispatch import receiver

@receiver(post_save, sender=Entry)
def noTeams_increase(sender, instance, created, *args, **kwargs):
    if created:
        tournament = Tournament.objects.get(pk=instance.tournament.id)
        teams = tournament.noTeams + 1
        Tournament.objects.filter(pk=instance.tournament.id).update(noTeams=teams)

@receiver(post_delete, sender=Entry)
def noTeams_decrease(sender, instance, *args, **kwargs):
    tournament = Tournament.objects.get(pk=instance.tournament.id)
    teams = tournament.noTeams - 1
    Tournament.objects.filter(pk=instance.tournament.id).update(noTeams=teams)