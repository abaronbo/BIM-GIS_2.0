from django.urls import path
from . import views

urlpatterns = [
    path('', views.cesium_viewer, name='cesium_viewer'),  # Handles both Contractor and Municipality users
]
