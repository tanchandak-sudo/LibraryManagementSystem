from django.db import models
from django.contrib.auth.models import User

class ExchangeRate(models.Model):
    currency_code = models.CharField(max_length=3, unique=True)
    rate_from_inr = models.DecimalField(max_digits=12, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 INR = {self.rate_from_inr} {self.currency_code}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    signature = models.CharField(max_length=255, null=True, blank=True)
    
    base_amount_inr = models.DecimalField(max_digits=10, decimal_places=2)
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2)
    charged_currency = models.CharField(max_length=3, default='INR')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"