from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models  import User
from tournaments.models import Entry
from django.dispatch import receiver
from .models import Profile
from django.contrib.auth.models import Group
from orders.models import Order
from decimal import Decimal
from django.db.models import Sum

@receiver(post_save, sender=User, weak=False)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User, weak=False)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Entry, weak=False)
def entry_costs_update(sender, instance, created, *args, **kwargs):
    prof = Profile.objects.get(user=instance.user)
    qs = Entry.objects.filter(user=instance.user)

    cost = 0
    for entry in qs:
        cost += entry.tournament.entryPrice

    prof.due = cost
    prof.save()

@receiver(post_delete, sender=Entry, weak=False)
def entry_costs_update(sender, instance, *args, **kwargs):
    prof = Profile.objects.get(user=instance.user)
    qs = Entry.objects.filter(user=instance.user)
    
    cost = 0
    for entry in qs:
        cost += entry.tournament.entryPrice
    
    prof.due = cost
    prof.save()
