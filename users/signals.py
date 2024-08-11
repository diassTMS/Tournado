from django.db.models.signals import post_save, pre_delete
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

@receiver(post_save, sender=Order)
def order_price_update(sender, instance, created, *args, **kwargs):
    prof = Profile.objects.get(user=instance.user)
    orders_user = Order.objects.filter(user=instance.user)
    prof.due = orders_user.aggregate(Sum('final_value'))['final_value__sum'] if orders_user.exists() else 0.00
    orders_paid = Order.objects.filter(user=instance.user, paid=True)
    prof.paid = orders_paid.aggregate(Sum('final_value'))['final_value__sum'] if orders_paid.exists() else 0.00
    prof.balance = Decimal(prof.paid) - Decimal(prof.due)
    prof.save()

@receiver(pre_delete, sender=Order)
def order_price_update(sender, instance, *args, **kwargs):
    prof = Profile.objects.get(user=instance.user)
    orders_user = Order.objects.filter(user=instance.user)
    order = instance
    prof.due = orders_user.aggregate(Sum('final_value'))['final_value__sum'] if orders_user.exists() else 0.00
    prof.due -= order.final_value
    orders_paid = Order.objects.filter(user=instance.user, paid=True)
    prof.paid = orders_paid.aggregate(Sum('final_value'))['final_value__sum'] if orders_paid.exists() else 0.00
    if order.paid == True:
        prof.paid -= order.final_value
    prof.balance = Decimal(prof.paid) - Decimal(prof.due)
    prof.save()
