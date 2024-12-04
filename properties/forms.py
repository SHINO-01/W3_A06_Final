from django import forms
from django.contrib.auth.models import User
from leaflet.forms.widgets import LeafletWidget
from .models import Location, Accommodation
from import_export import resources


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'
        widgets = {
            'center': LeafletWidget(),
        }

class AccommodationAdminForm(forms.ModelForm):
    class Meta:
        model = Accommodation
        fields = '__all__'    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # If editing an existing object
            self.fields['user'].widget.attrs['readonly'] = True
            self.fields['user'].widget.attrs['style'] = 'pointer-events: none; background-color: #e9ecef;'

class LocationResource(resources.ModelResource):
    class Meta:
        model = Location
        fields = ('id', 'title', 'center', 'parent_id', 'location_type', 'country_code', 'state_abbr', 'city')  # Adjust fields as needed
        import_id_fields = ('id',)  # Specify the unique identifier field

    def before_import_row(self, row, **kwargs):
        """
        Ensure parent_id exists or create a placeholder parent.
        """
        parent_id = row.get('parent_id')
        if parent_id:
            parent, created = Location.objects.get_or_create(
                id=parent_id,
                defaults={
                    'title': f"Placeholder for {parent_id}",
                    'center': 'POINT(0 0)',  # Placeholder center, adjust if necessary
                    'location_type': 'unknown',
                    'country_code': 'XX',  # Default values
                },
            )
            row['parent_id'] = parent.id
