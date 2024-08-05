from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User, Group
import datetime
from decimal import Decimal
CURRENCY = settings.CURRENCY

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    phone_number = models.CharField(max_length=16, blank=True, null=True)
    invoice_email = models.EmailField(blank=True, null=True)
    due = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    paid = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)
    balance = models.DecimalField(default=0.00, decimal_places=2, max_digits=20)

    def __str__(self):
        return f'{self.user.username}'
    
    def tag_due(self):
        return f'{CURRENCY}{self.due}'

    def tag_paid(self):
        return f'{CURRENCY}{self.paid}'

    def tag_balance(self):
        if self.balance < 0:
            return f'-{CURRENCY}{self.balance * -1}'
        else:
            return f'{CURRENCY}{self.balance}'

    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)