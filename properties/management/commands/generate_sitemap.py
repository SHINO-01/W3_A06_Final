import json
import os
from django.core.management.base import BaseCommand
from properties.models import Location
from django.db.models import Q

class Command(BaseCommand):
    help = 'Generate a dynamic sitemap.json file with hierarchical locations'

    # Fixed output path
    OUTPUT_DIR = "Generated"

    def create_location_entry(self, location, base_path=''):
        """
        Create a dynamic location entry with a hierarchical slug
        
        Args:
            location (Location): The location model instance
            base_path (str): Base path for the location slug
        
        Returns:
            dict: A dictionary representing the location entry
        """
        # Generate slug based on location title
        slug = location.title.lower().replace(' ', '-')
        
        # Construct full path
        full_path = f"{base_path}/{slug}" if base_path else slug
        
        # Create entry
        entry = {location.title: full_path}
        
        # Check if location has child locations
        child_locations = Location.objects.filter(
            parent_id=location
        ).order_by('title')
        
        # If child locations exist, add them
        if child_locations.exists():
            entry['locations'] = []
            for child in child_locations:
                child_entry = self.create_location_entry(
                    child, 
                    base_path=full_path
                )
                entry['locations'].append(child_entry)
        
        return entry

    def handle(self, *args, **kwargs):
        # Ensure the output directory exists
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)

        sitemap_file = os.path.join(self.OUTPUT_DIR, 'sitemap.json')

        try:
            # Find all top-level countries
            countries = Location.objects.filter(
                location_type='country'
            ).order_by('title')

            if not countries.exists():
                self.stdout.write(self.style.WARNING("No countries found in the database."))
                return

            # Generate sitemap
            sitemap = []
            for country in countries:
                # Create country entry
                country_entry = self.create_location_entry(country)
                sitemap.append(country_entry)

            # Write the final JSON to the file
            with open(sitemap_file, mode="w", encoding='utf-8') as file:
                json.dump(sitemap, file, indent=4, ensure_ascii=False)

            self.stdout.write(self.style.SUCCESS(f"Sitemap successfully saved to {sitemap_file}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating sitemap: {e}"))