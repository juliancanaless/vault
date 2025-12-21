"""
The Vault - Signals

Auto-create Profile when a User is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile automatically when a new User is created."""
    if created:
        Profile.objects.create(user=instance)

