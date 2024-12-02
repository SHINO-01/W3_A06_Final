from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from properties.models import Accommodation

class Command(BaseCommand):
    help = 'Create Property Owners group with specific permissions'

    def handle(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(name='Property Owners')
        content_type = ContentType.objects.get_for_model(Accommodation)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_accommodation', 'change_accommodation', 'delete_accommodation', 'view_accommodation']
        )
        group.permissions.set(permissions)
        group.save()
        self.stdout.write(self.style.SUCCESS('Property Owners group created with permissions.'))
