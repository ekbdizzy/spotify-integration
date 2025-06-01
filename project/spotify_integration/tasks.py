from celery import shared_task
from spotify_integration.services import SpotifyDataService


@shared_task
def fetch_spotify_tracks_task(user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)

    service = SpotifyDataService()
    tracks = service.fetch_user_tracks(user)
    print(f"Fetched {len(tracks)} tracks for user {user.username}")
    return len(tracks)
