from datetime import timedelta
import spotipy
from django.contrib.auth.models import User
from django.utils import timezone
from spotify_integration.models import SocialCredential


class SpotifyAuthService:

    def authenticate_or_create_user(self, token_info: dict):
        """Authenticate or create a user based on the request."""

        client = spotipy.Spotify(auth=token_info["access_token"])
        spotify_profile = client.current_user()
        spotify_user_id = spotify_profile["id"]

        try:
            user = User.objects.get(username=spotify_user_id)
            created = False
        except User.DoesNotExist:
            user = self.create_user_from_spotify(spotify_profile)
            created = True

        self.create_or_update_user_credentials(user, token_info)
        return user, created

    # todo add pydantic for token info
    @staticmethod
    def create_or_update_user_credentials(user, token_info: dict) -> SocialCredential:
        """
        Save or update user's Spotify credentials.
        """
        expires_at = timezone.now() + timedelta(seconds=token_info.get('expires_in', 3600))

        credentials, created = SocialCredential.objects.update_or_create(
            user=user,
            platform="spotify",
            defaults={
                'expires_at': expires_at,
            }
        )
        return credentials

    @staticmethod
    def create_user_from_spotify(spotify_profile: dict):  # TODO add pydantic schema
        """Create a user from Spotify profile information."""
        spotify_user_id = spotify_profile["id"]
        email = spotify_profile.get("email")
        display_name = spotify_profile.get("display_name", spotify_user_id)

        username = spotify_user_id

        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@spotify.local",
            first_name=display_name,
            last_name="",
        )
        user.set_unusable_password()
        user.save()
        return user
