from django.urls import path
from .views import CustomLoginView, logout_view

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),  # URL pattern for login page
    path('logout/', logout_view, name='logout'),
]
