from django.urls import path
from spotify_integration import views

app_name = "spotify"

urlpatterns = [
        path("auth/", views.SpotifyAuthView.as_view(), name="spotify_auth"),
]
