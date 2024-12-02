from django import forms
from django.contrib.auth.models import User
from leaflet.forms.widgets import LeafletWidget
from .models import Location

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
