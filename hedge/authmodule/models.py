# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from analytics.models import *

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile_no = models.CharField(max_length = 15, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Check if OTP is not older than 5 minutes
        return (timezone.now() - self.created_at).seconds < 300



class ModelLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=255)
    instance_id = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField()  # Store the changes as a JSON object

    def __str__(self):
        return f"{self.model_name} {self.action} by {self.user.username if self.user else 'System'} at {self.timestamp}"



class Plan(models.Model):
    PLAN_CHOICES = [
        ('Trial', 'Trial'),
        ('Basic', 'Basic'),
        ('Intermediate', 'Intermediate'),
        ('Advance', 'Advance'),
        ('Custom', 'Custom Plan'),
    ]
    
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES, default='Basic')
    paypal_plan_id = models.CharField(max_length = 50, blank = True, null = True)
    billings = models.BooleanField(default=False)
    unlimited_strategy_data = models.BooleanField(default=False)
    unlimited_orders = models.BooleanField(default=False)
    api_keys = models.IntegerField(default=0)
    ai_assistant = models.BooleanField(default=False)
    unlimited_devices = models.BooleanField(default=False)
    supports_long = models.BooleanField(default=False)
    supports_short = models.BooleanField(default=False)
    all_markets = models.BooleanField(default=False)
    all_brokers = models.BooleanField(default=False)
    custom_strategy = models.BooleanField(default=False)
    dedicated_support_manager = models.BooleanField(default=False)
    price = models.CharField(max_length = 20, blank = True, null = True)
    def __str__(self):
        return self.plan_name

class UserActivePlanManager(models.Manager):
    def update_expired_plans_for_user(self, user):
        current_time = timezone.now()
        if not user.is_superuser:
            # Filter the plans for the specific user whose end_date is less than current_time and status is not "Expired"

            self.filter(user=user, end_date__lt=current_time).exclude(status="Expired").update(status="Expired")

            # Check if the user has any active plans
            active_plans_exist = self.filter(user=user, status="Active", end_date__gt=current_time).exists()

            # If no active plans exist, update ApiIntegration status to "InActive"
            if not active_plans_exist:
                ApiIntegration.objects.filter(user=user).update(status="InActive")


class Coupon(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, blank = True, null = True)
    code = models.CharField(max_length=50 , unique=True)
    status = models.CharField(max_length = 15, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

class UserTransections(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    transactions_id = models.CharField(max_length = 50, blank = True, null = True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank = True, null = True)
    status = models.CharField(max_length = 20)
    price = models.CharField(max_length = 20)
    start_date = models.DateTimeField(auto_now_add = True)
    end_date = models.DateTimeField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserActivePlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank = True, null = True)
    transactions_id = models.CharField(max_length = 50, blank = True, null = True)
    status = models.CharField(max_length = 20)
    start_date = models.DateTimeField(blank = True, null = True)
    end_date = models.DateTimeField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserActivePlanManager()


class SubscriptionButtonClicked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)


