from django.urls import path
from . import views

urlpatterns = [
    path('get_ifc_attributes/', views.get_ifc_attributes, name='get_ifc_attributes'),
]
