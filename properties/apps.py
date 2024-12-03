# apps.py

from django.apps import AppConfig
from django.db.models.signals import post_migrate

class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'properties'

    def ready(self):
        import properties.signals  # Ensure signals are imported and connected
