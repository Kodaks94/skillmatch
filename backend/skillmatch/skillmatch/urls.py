from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('team.urls')),  # This includes all frontend & API views
    path('auth/', include('django.contrib.auth.urls')),  # login/logout
]