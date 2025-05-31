from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include


def index(request):
    return HttpResponse("Welcome to the Spotify Integration API!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("spotify/", include("spotify_integration.urls", namespace="spotify")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path('', index, name='index'),
]
