# signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Model
from .models import ModelLog  # Import the log model
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
import json

@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if isinstance(instance, Model):  # Replace 'Model' with the appropriate model you're interested in
        # model_name = sender.__name__
        # action = 'create' if created else 'update'
        # user = getattr(instance, 'user', None)

        # # Create a dictionary of changes with only relevant fields
        # changes = {
        #     field: value for field, value in instance.__dict__.items()
        #     if not field.startswith('_') and isinstance(value, (str, int, float, bool))  # Ensure only basic types
        # }

        # # Remove any datetime fields from changes
        # for key in list(changes.keys()):
        #     if isinstance(changes[key], datetime):
        #         del changes[key]
        # print(action, model_name, changes)
        # Log the action to the database
        # ModelLog.objects.create(
        #     action=action,
        #     model_name=model_name,
        #     instance_id=instance.pk,
        #     user=user if isinstance(user, User) else None,
        #     changes=json.dumps(changes),  # Serialize the changes dictionary
        #     timestamp=timezone.now()  # Use timezone-aware timestamp
        # )
        
        pass


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    # Ensure we're dealing with a model instance
    if isinstance(instance, Model):  
        model_name = sender.__name__
        user = getattr(instance, 'user', None)  # Assume the instance has a user attribute
        
        # Log the action to the database
        # ModelLog.objects.create(
        #     action='delete',
        #     model_name=model_name,
        #     instance_id=instance.pk,
        #     user=user if isinstance(user, User) else None,
        #     changes=instance.__dict__.copy()  # Store the instance state before deletion
        # )
