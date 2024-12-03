from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import Location, Accommodation, LocalizeAccommodation
from .forms import AccommodationAdminForm

# Register your models here.

@admin.register(Location)
class LocationAdmin(LeafletGeoAdmin):
    list_display = ('title', 'location_type', 'city', 'country_code')
    search_fields = ('title', 'city', 'country_code')
    list_filter = ('location_type',)

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    form = AccommodationAdminForm
    list_display = ('title', 'feed', 'location', 'review_score', 'usd_rate', 'published')
    search_fields = ('title', 'user__username')
    list_filter = ('published', 'feed')

    def get_form(self, request, obj=None, **kwargs):
        """
        Override the form to dynamically set the user field.
        """
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Only for new objects
            form.base_fields['user'].initial = request.user
            form.base_fields['user'].disabled = True  # Make the field read-only
        return form

    def save_model(self, request, obj, form, change):
        """
        Automatically assign the logged-in user as the owner if creating a new record.
        """
        if not obj.pk:  # If creating a new object
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Property Owners').exists() and not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_delete_permission(request, obj)

    # Optional: Add help text to clarify why the field is read-only

@admin.register(LocalizeAccommodation)
class LocalizeAccommodationAdmin(admin.ModelAdmin):
    list_display = ('property', 'language')
    search_fields = ('property__title', 'language')
    list_filter = ('language',)
