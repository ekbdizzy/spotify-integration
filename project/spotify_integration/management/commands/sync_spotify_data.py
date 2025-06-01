# project/spotify_integration/management/commands/sync_spotify_data.py
from django.core.management.base import BaseCommand
from spotify_integration.models import SocialCredential
from spotify_integration.tasks import (
    fetch_spotify_following_task,
    fetch_spotify_playlists_task,
    fetch_spotify_tracks_task,
)


class Command(BaseCommand):
    help = "Sync Spotify data for all users with valid credentials"

    def handle(self, *args, **options):
        users = SocialCredential.objects.filter(
            platform="spotify",
            refresh_token__isnull=False
        ).exclude(refresh_token=b"").values_list("user_id", flat=True)
        for user_id in users:
            fetch_spotify_tracks_task.delay(user_id)
            fetch_spotify_playlists_task.delay(user_id)
            fetch_spotify_following_task.delay(user_id)
        self.stdout.write(self.style.SUCCESS(f"Triggered sync for {len(users)} users."))