from django.urls import path
from spotify_integration import views

app_name = "spotify"

urlpatterns = [
    path("auth/", views.SpotifyAuthView.as_view(), name="spotify_auth"),
    path("callback/", views.SpotifyCallbackView.as_view(), name="spotify_callback"),
    path("refresh/", views.SpotifyRefreshView.as_view(), name="spotify_refresh"),
    path("disconnect/", views.SpotifyDisconnectView.as_view(), name="spotify_disconnect"),

    path("sync/tracks/", views.SpotifyTracksSyncView.as_view(), name="spotify_track_list"),
    path("sync/playlists/", views.SpotifyPlaylistsSyncView.as_view(), name="spotify_track_list"),
    # path("sync/follows/", views.SpotifyTrackListView.as_view(), name="spotify_track_list"),
]
