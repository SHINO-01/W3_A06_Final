import json
from django.core.management.base import BaseCommand
from properties.models import Location

class Command(BaseCommand):
    help = 'Generate a sitemap.json file for all country locations.'

    def handle(self, *args, **options):
        countries = Location.objects.filter(location_type='country').order_by('title')
        sitemap = []

        for country in countries:
            country_slug = country.country_code.lower()
            country_data = {
                country.title: country_slug,
                "locations": []
            }
            states = Location.objects.filter(parent_id=country.id).order_by('title')
            for state in states:
                state_slug = f"{country_slug}/{state.state_abbr.lower()}"
                state_data = {state.title: state_slug}
                country_data["locations"].append(state_data)
            sitemap.append(country_data)

        with open('sitemap.json', 'w') as f:
            json.dump(sitemap, f, indent=4)

        self.stdout.write(self.style.SUCCESS('Successfully generated sitemap.json'))
