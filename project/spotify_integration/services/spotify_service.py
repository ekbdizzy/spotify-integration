import secrets

import spotipy
from django.conf import settings
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


class SpotifyApiError(Exception):
    """Custom exception for Spotify API errors."""

    pass


class SpotifyService:
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

    def get_auth_url(self, state: str) -> tuple[str, str]:
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

    def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchange the authorization code for tokens.
        """
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )
        token_info = sp_oauth.get_access_token(code)
        if not token_info:
            raise SpotifyApiError("Failed to obtain access token.")
        return token_info

