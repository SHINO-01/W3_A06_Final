from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis import admin as geoadmin
from leaflet.admin import LeafletGeoAdmin
from .models import Location, Accommodation, LocalizeAccommodation

# Register your models here.

@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin):
    list_display = ('title', 'location_type', 'city', 'country_code')
    search_fields = ('title', 'city', 'country_code')
    list_filter = ('location_type',)

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('title', 'feed', 'location', 'review_score', 'usd_rate', 'published')
    search_fields = ('title', 'user__username')
    list_filter = ('published', 'feed')
    raw_id_fields = ('user',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Property Owners').exists() and not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_delete_permission(request, obj)

@admin.register(LocalizeAccommodation)
class LocalizeAccommodationAdmin(admin.ModelAdmin):
    list_display = ('property', 'language')
    search_fields = ('property__title', 'language')
    list_filter = ('language',)
