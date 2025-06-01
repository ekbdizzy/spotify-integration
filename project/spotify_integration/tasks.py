from celery import shared_task
from spotify_integration.services import SpotifyDataService


@shared_task
def fetch_spotify_tracks_task(access_token: str):
    service = SpotifyDataService()
    tracks = service.fetch_user_tracks(access_token)
    return len(tracks)
