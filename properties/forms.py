from django import forms
from django.contrib.auth.models import User
from leaflet.forms.widgets import LeafletWidget
from .models import Location, Accommodation

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