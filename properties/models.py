from django.contrib.gis.db import models as geomodels
from django.contrib.auth.models import User

class Location(geomodels.Model):
    id = geomodels.CharField(max_length=20, primary_key=True)
    title = geomodels.CharField(max_length=100)
    center = geomodels.PointField()
    parent_id = geomodels.ForeignKey(
        'self', null=True, blank=True, on_delete=geomodels.CASCADE
    )
    location_type = geomodels.CharField(max_length=20)
    country_code = geomodels.CharField(max_length=2)
    state_abbr = geomodels.CharField(max_length=3, blank=True)
    city = geomodels.CharField(max_length=30, blank=True)
    created_at = geomodels.DateTimeField(auto_now_add=True)
    updated_at = geomodels.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Accommodation(geomodels.Model):
    id = geomodels.CharField(max_length=20, primary_key=True)
    feed = geomodels.PositiveSmallIntegerField(default=0)
    title = geomodels.CharField(max_length=100)
    country_code = geomodels.CharField(max_length=2)
    bedroom_count = geomodels.PositiveIntegerField()
    review_score = geomodels.DecimalField(max_digits=3, decimal_places=1, default=0)
    usd_rate = geomodels.DecimalField(max_digits=10, decimal_places=2)
    center = geomodels.PointField()
    images = geomodels.JSONField()
    location = geomodels.ForeignKey(Location, on_delete=geomodels.CASCADE)
    amenities = geomodels.JSONField()
    user = geomodels.ForeignKey(
        User, on_delete=geomodels.CASCADE, related_name='accommodations'
    )
    published = geomodels.BooleanField(default=False)
    created_at = geomodels.DateTimeField(auto_now_add=True)
    updated_at = geomodels.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class LocalizeAccommodation(geomodels.Model):
    id = geomodels.AutoField(primary_key=True)
    property = geomodels.ForeignKey(Accommodation, on_delete=geomodels.CASCADE)
    language = geomodels.CharField(max_length=2)
    description = geomodels.TextField()
    policy = geomodels.JSONField()

    def __str__(self):
        return f"{self.property.title} - {self.language}"
