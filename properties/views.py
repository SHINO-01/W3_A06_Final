# properties/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from .forms import SignUpForm
from .models import Accommodation, LocalizeAccommodation

def home(request):
    return render(request, 'properties/home.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            property_owner_group, created = Group.objects.get_or_create(name=_('Property Owners'))
            user.groups.add(property_owner_group)
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'properties/signup.html', {'form': form})

def accommodation_detail(request, accommodation_id):
    accommodation = Accommodation.objects.get(id=accommodation_id)
    language = get_language()
    localized = LocalizeAccommodation.objects.filter(property=accommodation, language=language).first()
    if not localized:
        localized = LocalizeAccommodation.objects.filter(property=accommodation, language='en').first()
    return render(request, 'properties/accommodation_detail.html', {
        'accommodation': accommodation,
        'localized': localized,
    })
