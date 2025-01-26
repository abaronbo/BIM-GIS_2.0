"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from cesiumapp.views import cesium_viewer
from queryifcapp.views import get_ifc_attributes
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from login.views import CustomLoginView, logout_view

def redirect_to_login(request):
    return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CustomLoginView.as_view(), name='login'),  # Root URL for login page
    path('logout/', logout_view, name='logout'),
    path('cesium/', include('cesiumapp.urls')),  # Cesium app after login
    path('ifcupload/', include('ifcupload.urls')),
    path('sparql_filter/', include('sparql_filter.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
