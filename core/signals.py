"""
The Vault - Signals

Auto-create Profile when a User is created.
Update Couple timezone when Profile timezone changes.
"""

from django.db.models.signals import post_save
from django.db.models import Q
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, Couple

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile automatically when a new User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Profile)
def update_couple_timezone_on_profile_change(sender, instance, **kwargs):
    """
    Update couple timezone when a user's profile timezone changes.
    This ensures couples always use the correct shared timezone.
    """
    # Get all couples where this user is user1 or user2
    couples = Couple.objects.filter(
        Q(user1=instance.user) | Q(user2=instance.user)
    )
    
    for couple in couples:
        # Save the couple, which will recalculate timezone in its save() method
        # Don't use update_fields to ensure the full save() logic runs
        couple.save()

