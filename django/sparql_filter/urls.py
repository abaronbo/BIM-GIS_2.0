from django.urls import path
from . import views

urlpatterns = [
    path('sparql/', views.sparql_query, name='sparql_query'),  # Existing Contractor query
    path('sparql_municipality/', views.sparql_query_municipality, name='sparql_query_municipality'),
]
