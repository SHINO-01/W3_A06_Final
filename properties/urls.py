# properties/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('accommodation/<str:accommodation_id>/', views.accommodation_detail, name='accommodation_detail'),
]
