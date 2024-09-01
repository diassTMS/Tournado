from django.db.models.signals import post_save
from tournaments.models import Entry
from .models  import OrderItem
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal


@receiver(post_save, sender=OrderItem, weak=False)
def order_price_update(sender, instance, created, *args, **kwargs):
    order = instance.order
    order_items = order.order_items.all()
    order.value = order_items.aggregate(Sum('total_price'))['total_price__sum'] if order_items.exists() else 0.00
    order.final_value = Decimal(order.value) - Decimal(order.discount)
    order.save()