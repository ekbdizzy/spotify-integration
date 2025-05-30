from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path("spotify/", include("spotify_integration.urls", namespace="spotify") ),
]
