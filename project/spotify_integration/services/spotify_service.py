from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
from spotify_integration.schemes import TokenInfo
import logging

logger = logging.getLogger(__name__)


class SpotifyApiError(Exception):
    """Custom exception for Spotify API errors."""
    pass


class SpotifyService:
    """Service for interacting with the Spotify API, including authentication and token management."""

    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        self.scope = " ".join(
            [
                "user-library-read",
                "playlist-read-private",
                "playlist-read-collaborative",
                "user-follow-read",
                "user-read-email",
                "user-read-private",
                "user-read-recently-played",
                "user-top-read",
            ]
        )

    def get_auth_url(self, state: str) -> str:
        """
        Get url for Spotify authentication.
        """
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            state=state,
            show_dialog=True,
        )
        auth_url = sp_oauth.get_authorize_url()
        return auth_url

    def exchange_code_for_tokens(self, code: str) -> TokenInfo:
        """
        Exchange the authorization code for tokens.
        """
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )
        token_data = sp_oauth.get_access_token(code)
        if not token_data:
            logger.warning("No token returned from Spotify")
            raise SpotifyApiError("Failed to obtain access token.")
        token_info = TokenInfo.model_validate(token_data)
        return token_info

    def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """
        Refresh the access token using the refresh token.
        """
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )
        token_data = sp_oauth.refresh_access_token(refresh_token)
        if not token_data:
            logger.warning("No token returned from Spotify during refresh")
            raise SpotifyApiError("Failed to refresh access token.")
        token_info = TokenInfo.model_validate(token_data)
        return token_info
