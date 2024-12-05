import json
import os
from django.core.management.base import BaseCommand
from properties.models import Location

class Command(BaseCommand):
    help = 'Generate a dynamic sitemap.json file with hierarchical locations'
    OUTPUT_DIR = "Generated"

    def create_location_entry(self, location, base_path=''):
        slug = location.title.lower().replace(' ', '-')
        full_path = f"{base_path}/{slug}" if base_path else slug
        entry = {location.title: full_path}
        child_locations = Location.objects.filter(parent_id=location).order_by('title')

        if child_locations.exists():
            entry['locations'] = []
            for child in child_locations:
                child_entry = self.create_location_entry(child, base_path=full_path)
                entry['locations'].append(child_entry)

        return entry

    def handle(self, *args, **kwargs):
        # Always attempt to create the directory, triggering the mock exception if any
        try:
            os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating sitemap: {e}"))
            return

        sitemap_file = os.path.join(self.OUTPUT_DIR, 'sitemap.json')

        try:
            countries = Location.objects.filter(location_type='country').order_by('title')
            if not countries.exists():
                self.stdout.write(self.style.WARNING("No countries found in the database."))
                return

            sitemap = []
            for country in countries:
                slug = country.title.lower().replace(' ', '-')
                # Ensure 'locations': [] is always present
                country_entry = {country.title: slug, 'locations': []}
                child_locations = Location.objects.filter(parent_id=country).order_by('title')
                for child in child_locations:
                    child_entry = self.create_location_entry(child, base_path=slug)
                    country_entry['locations'].append(child_entry)
                sitemap.append(country_entry)

            with open(sitemap_file, mode="w", encoding='utf-8') as file:
                json.dump(sitemap, file, indent=4, ensure_ascii=False)

            self.stdout.write(self.style.SUCCESS(f"Sitemap successfully saved to {sitemap_file}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating sitemap: {e}"))
