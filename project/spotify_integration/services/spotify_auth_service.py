import spotipy
from django.contrib.auth.models import User
from spotify_integration.models import SocialCredential
from spotify_integration.services.spotify_service import SpotifyService


class SpotifyAuthService:
    def __init__(self):
        self.spotify_service = SpotifyService()

    def authenticate_or_create_user(self, token_info: dict):
        """Authenticate or create a user based on the request."""

        client = spotipy.Spotify(auth=token_info["access_token"])
        spotify_profile = client.current_user()
        spotify_user_id = spotify_profile["id"]

        try:
            credentials = SocialCredential.objects.get(
                platform_user_id=spotify_user_id, platform="spotify"
            )
            user = credentials.user
            created = False

        except SocialCredential.DoesNotExist:
            user = self._create_user_from_spotify(spotify_profile)
            created = True

        self.spotify_service.save_user_credentials(user, token_info)
        return user, created

    def _create_user_from_spotify(self, spotify_profile: dict):
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
