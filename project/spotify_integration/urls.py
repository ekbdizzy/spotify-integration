from django.urls import path
from spotify_integration import views

app_name = "spotify"

urlpatterns = [
        path("auth/", views.SpotifyAuthView.as_view(), name="spotify_auth"),
        path("callback/", views.SpotifyCallbackView.as_view(), name="spotify_callback"),
        path("disconnect/", views.SpotifyDisconnectView.as_view(), name="spotify_disconnect"),
]
