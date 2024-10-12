# analytics/models.py
from django.db import models
from django.contrib.auth.models import User
import json

class TradeAlert(models.Model):

    STRATEGY_CHOICES = [
        ('long', 'Long'),
        ('short', 'Short'),
    ]

    id = models.AutoField(primary_key=True)
    date_time = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=18, decimal_places=8)
    time_frame = models.CharField(max_length=20)
    strategy = models.CharField(max_length=5, choices=STRATEGY_CHOICES)
    entry = models.BooleanField(default=False)
    exit = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.symbol} - {self.strategy} - {self.price}'



class StrategyData(models.Model):
    strategy = models.CharField(max_length=255, blank =True, null = True)
    market = models.CharField(max_length=255,  blank =True, null = True)
    broker = models.CharField(max_length=255, blank =True, null = True)
    symbol = models.CharField(max_length=250, blank =True, null = True)
    entry_price = models.DecimalField(max_digits=10, decimal_places=5)
    exit_price = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    pl = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)  # Profit/Loss
    time_frame = models.CharField(max_length=15,  blank =True, null = True)
    entry_type = models.CharField(max_length=90,  blank =True, null = True)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=5)
    order_no = models.CharField(max_length=55)
    api_name = models.CharField(max_length=55, blank = True, null = True)
    currency = models.CharField(max_length=10, blank = True, null = True)
    percentage = models.PositiveIntegerField(default=0)
    order_1 = models.CharField(max_length=255, blank = True, null = True)
    order_2 = models.CharField(max_length=255, blank = True, null = True)
    order_3 = models.CharField(max_length=255, blank = True, null = True)
    order_4 = models.CharField(max_length=255, blank = True, null = True)
    order_5 = models.CharField(max_length=255, blank = True, null = True)
    order_6 = models.CharField(max_length=255, blank = True, null = True)
    order_7 = models.CharField(max_length=255, blank = True, null = True)
    order_8 = models.CharField(max_length=255, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Trade {self.order_no} - {self.symbol} ({self.strategy})"


class ApiIntegration(models.Model):
    API_TYPES = [
        ('forex', 'Forex API'),
        ('crypto', 'Crypto API'),
        ('stock', 'Stock API'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming you're using Django's built-in User model
    api_name = models.CharField(max_length=255)
    broker = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    api_type = models.CharField(max_length=50, choices=API_TYPES)
    status = models.CharField(max_length=255, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.api_name} - {self.user.username}"


class Orders(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming you're using Django's built-in User model
    api = models.ForeignKey(ApiIntegration, on_delete=models.CASCADE, blank = True, null = True)  # Assuming you're using Django's built-in User model
    market = models.CharField(max_length=255)
    broker = models.CharField(max_length=255, blank = True, null = True)
    symbol = models.CharField(max_length=255)
    strategy = models.CharField(max_length=255, blank = True, null = True)
    time_frame = models.CharField(max_length=50)
    long_or_short = models.CharField(max_length=255)
    stop_loss = models.CharField(max_length=255)
    risk_value = models.CharField(max_length=255)
    order_type = models.CharField(max_length=255, blank = True, null = True)
    option_strategies = models.CharField(max_length=255, blank = True, null = True)
    status = models.CharField(max_length=255, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)






class OpenOrders(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank = True, null = True)  # Assuming you're using Django's built-in User model
    ord_id = models.CharField(max_length = 255, blank = True, null = True)
    market = models.CharField(max_length=255)
    broker = models.CharField(max_length=255, blank = True , null = True)
    symbol = models.CharField(max_length=255)
    strategy = models.CharField(max_length=255, blank = True, null = True)
    order_id = models.CharField(max_length=50)
    local_currency = models.CharField(max_length=255)
    time_frame = models.CharField(max_length=50, blank = True, null = True)
    long_or_short = models.CharField(max_length=255, blank = True, null = True)
    price = models.CharField(max_length=255, blank = True, null = True)
    stop_loss = models.CharField(max_length=255, blank = True, null = True)
    risk_value = models.CharField(max_length=255, blank = True, null = True)
    order_type = models.CharField(max_length=255, blank = True, null = True)
    option_strategies = models.CharField(max_length=255, blank = True, null = True)
    automation = models.CharField(max_length=255, blank = True, null = True)
    status = models.CharField(max_length=255, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

