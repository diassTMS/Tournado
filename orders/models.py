from django.db import models
from tournaments.models import Tournament
from django.db.models import Sum
from django.conf import settings
from django.urls import reverse
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.utils.timezone import now
from django.contrib.auth.models import User, Group
import datetime
from decimal import Decimal
CURRENCY = settings.CURRENCY
TOURN_PRICE = settings.TOURN_PRICE

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=now)
    title = models.CharField(blank=True, max_length=150)
    timestamp = models.DateField(auto_now_add=True)
    value = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    discount = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    final_value = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return self.title if self.title else 'New Order'
    
    def get_edit_url(self):
        return reverse('update-order', kwargs={'pk': self.id})

    def get_delete_url(self):
        return reverse('delete-order', kwargs={'pk': self.id})

    def tag_final_value(self):
        return f'{CURRENCY}{self.final_value}'

    def tag_discount(self):
        return f'{CURRENCY}{self.discount}'

    def tag_value(self):
        return f'{CURRENCY}{self.value}'
    
class OrderItem(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    total_price = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    invoiced = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.tournament.name}'

    def save(self,  *args, **kwargs):
        if self.order.user.groups.filter(name="Admin").exists():
            self.price = TOURN_PRICE
        else: 
            self.price = self.tournament.entryPrice

        self.total_price = Decimal(self.price) * Decimal(self.qty)

        super().save(*args, **kwargs)
        self.order.save()

    def tag_price(self):
        return f'{CURRENCY}{self.price}'
    
    def tag_total_price(self):
        return f'{CURRENCY}{self.total_price}'
    
    def tag_teams(self):
        return f'{self.qty}'

