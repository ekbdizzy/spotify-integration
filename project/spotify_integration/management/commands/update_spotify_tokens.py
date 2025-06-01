# project/spotify_integration/management/commands/update_spotify_tokens.py
from django.core.management.base import BaseCommand
from spotify_integration.models import SocialCredential
from spotify_integration.services import SpotifyAuthService


class Command(BaseCommand):
    help = "Update Spotify tokens for all users with a refresh token"

    def handle(self, *args, **options):
        auth_service = SpotifyAuthService()
        credentials = SocialCredential.objects.filter(
            platform="spotify",
            refresh_token__isnull=False
        ).exclude(refresh_token=b"")
        updated = 0
        for cred in credentials:
            try:
                token_info = auth_service.spotify_service.refresh_access_token(cred.refresh_token_value)
                auth_service.create_or_update_user_credentials(cred.user, token_info)
                updated += 1
            except Exception as e:
                self.stderr.write(f"Failed to update token for user {cred.user_id}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Updated tokens for {updated} users."))