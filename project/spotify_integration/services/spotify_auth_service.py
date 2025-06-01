from datetime import timedelta
import spotipy
from django.contrib.auth.models import User
from django.utils import timezone
from spotify_integration.models import SocialCredential
from spotify_integration.schemes import TokenInfo, SpotifyProfile
import logging

logger = logging.getLogger(__name__)


class SpotifyAuthService:

    def authenticate_or_create_user(self, token_info: TokenInfo) -> tuple[User, bool]:
        """Authenticate or create a user based on the request."""

        client = spotipy.Spotify(auth=token_info.access_token).current_user()
        spotify_profile: SpotifyProfile = SpotifyProfile.model_validate(client)
        spotify_user_id = spotify_profile.id

        try:
            user = User.objects.get(username=spotify_user_id)
            created = False
        except User.DoesNotExist:
            user = self.create_user_from_spotify(spotify_profile)
            created = True
        return user, created

    @staticmethod
    def create_or_update_user_credentials(user, token_info: TokenInfo) -> SocialCredential:
        """
        Save or update user's Spotify credentials.
        """
        expires_at = timezone.now() + timedelta(seconds=token_info.expires_in)
        credentials, created = SocialCredential.objects.get_or_create(
            user=user,
            platform="spotify",
            defaults={
                'expires_at': expires_at,
                'platform_user_id': user.username,
            }
        )
        credentials.access_token_value = token_info.access_token
        if "refresh_token" in token_info:
            credentials.refresh_token_value = token_info.refresh_token

        credentials.expires_at = expires_at
        credentials.save()
        logger.info(f"{'Created' if created else 'Updated'} Spotify credentials for user: {user.username}")
        return credentials

    @staticmethod
    def create_user_from_spotify(spotify_profile: SpotifyProfile) -> User:
        """Create a user from Spotify profile information."""
        spotify_user_id = spotify_profile.id
        email = spotify_profile.email
        display_name = spotify_profile.display_name or spotify_user_id
        username = spotify_user_id

        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@spotify.local",
            first_name=display_name,
            last_name="",
        )
        user.set_unusable_password()
        user.save()
        logger.info(f"Created new user: {user.username} from Spotify profile.")
        return user

    @staticmethod
    def get_access_token(user: User) -> str:
        """Get the access token for the user."""
        token = SocialCredential.objects.get_access_token(user)
        if token is None:
            raise ValueError("Spotify credentials are missing or expired.")
        return token
