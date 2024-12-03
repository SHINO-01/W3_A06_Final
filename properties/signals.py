# signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Accommodation

@receiver(post_migrate)
def assign_property_owner_permissions(sender, **kwargs):
    """
    Automatically create the 'Property Owners' group and assign permissions to it.
    """
    group, created = Group.objects.get_or_create(name='Property Owners')
    # Get the Accommodation model content type
    accommodation_content_type = ContentType.objects.get_for_model(Accommodation)

    # Assign CRUD permissions for the Accommodation model to the group
    permissions = Permission.objects.filter(content_type=accommodation_content_type)
    for permission in permissions:
        group.permissions.add(permission)
