from django.contrib.auth import login as django_login, logout
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from response_handlers import success_response, error_response
from spotify_integration.models import SocialCredential
from spotify_integration.serializers import SpotifyAuthSerializer, SpotifyCallbackSerializer
from spotify_integration.services import SpotifyAuthService, SpotifyService, StateStorageService, SpotifyDataService
from spotify_integration.schemes import TokenInfo
import logging

from spotify_integration.tasks import fetch_spotify_tracks_task

logger = logging.getLogger("spotify_integration")


class SpotifyAuthView(APIView):
    """View to handle Spotify authentication."""

    serializer_class = SpotifyAuthSerializer
    storage_service = StateStorageService()
    spotify_service = SpotifyService()

    def get(self, request, *args, **kwargs):
        """Get URL for Spotify authentication."""

        state = self.storage_service.generate_oauth_state()
        auth_url = self.spotify_service.get_auth_url(state)
        serializer = self.serializer_class({"auth_url": auth_url, "state": state})

        return success_response(data=serializer.data)


class SpotifyCallbackView(APIView):
    """
    View to handle Spotify callback after authentication.
    """
    serializer_class = SpotifyCallbackSerializer
    storage_service = StateStorageService()
    spotify_service = SpotifyService()
    auth_service = SpotifyAuthService()

    def get(self, request, *args, **kwargs):
        """Handle Spotify callback."""

        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if error := serializer.validated_data.get("error"):
            return error_response(message=f"Spotify authentication error: {error}")

        if not (code := serializer.validated_data.get("code")):
            return error_response(message=f"Spotify authentication error: {code}")

        state = serializer.validated_data.get("state")
        if not self.storage_service.is_valid_oauth_state(state):
            return error_response(message=f"Invalid state parameter {state}. Possible CSRF attack.")

        try:
            token_info: TokenInfo = self.spotify_service.exchange_code_for_tokens(code)
            user, created = self.auth_service.authenticate_or_create_user(token_info)
            self.auth_service.create_or_update_user_credentials(user, token_info)
            django_login(request, user)

            # TODO start a background task to sync the user's Spotify data

        except Exception as e:
            return error_response(
                message=f"Spotify authentication error: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(message="Spotify authentication successful.")


class SpotifyDisconnectView(APIView):
    """View to disconnect Spotify account."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Disconnect Spotify account."""
        try:
            credential = request.user.social_credentials.filter(platform="spotify").first()
            if credential:
                credential.delete()
                logger.info(f"Spotify disconnected for user: {request.user.username}")
                logout(request)
                return success_response(message="Spotify disconnected.")

            else:
                return error_response(message="No Spotify account connected.")
        except Exception as e:
            return error_response(message=f"Spotify disconnect error: {e}",
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SpotifyRefreshView(APIView):
    """View to refresh Spotify access token."""

    permission_classes = [IsAuthenticated]
    spotify_service = SpotifyService()
    auth_service = SpotifyAuthService()

    def post(self, request, *args, **kwargs):
        """Refresh Spotify access token."""
        try:
            credentials = SocialCredential.objects.filter(user_id=request.user.id, platform="spotify").first()
            if credentials is None:
                return error_response(message="No Spotify account connected.")

            if credentials.refresh_token is None:
                return error_response(message="No Spotify refresh token available.")

            token_info: TokenInfo = self.spotify_service.refresh_access_token(credentials.refresh_token_value)
            self.auth_service.create_or_update_user_credentials(request.user, token_info)

        except Exception as e:
            return error_response(message=f"Spotify refresh token error: {e}",
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                                  )

        return success_response(message="Spotify refresh access token successful.")


class SpotifyTracksSyncView(APIView):
    """Trigger background fetch of Spotify tracks."""
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     fetch_spotify_tracks_task.delay(request.user.id)
    #     return Response(
    #         {"message": "Spotify track fetch task started."},
    #         status=status.HTTP_202_ACCEPTED
    #     )

    def post(self, request, *args, **kwargs):
        """Fetch Spotify tracks."""

        data_service = SpotifyDataService()
        auth_service = SpotifyAuthService()

        try:
            access_token = auth_service.get_access_token(request.user)
            tracks_spotify_data = data_service.fetch_user_tracks(access_token)
            social_posts = data_service.map_tracks_to_social_posts(request.user, tracks_spotify_data)
            data_service.bulk_update_social_posts(
                user=request.user,
                platform="spotify",
                post_type="tracks",
                social_posts=social_posts)

        except Exception as e:
            return error_response(
                message=f"Error fetching Spotify tracks: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response()


class SpotifyPlaylistsSyncView(APIView):
    """Trigger background fetch of Spotify tracks."""
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     fetch_spotify_tracks_task.delay(request.user.id)
    #     return Response(
    #         {"message": "Spotify track fetch task started."},
    #         status=status.HTTP_202_ACCEPTED
    #     )

    def post(self, request, *args, **kwargs):
        """Fetch Spotify playlists."""

        data_service = SpotifyDataService()
        auth_service = SpotifyAuthService()

        try:
            access_token = auth_service.get_access_token(request.user)
            playlists_spotify_data = data_service.fetch_user_playlists(access_token)
            social_posts = data_service.map_playlists_to_social_posts(request.user, playlists_spotify_data)
            data_service.bulk_update_social_posts(
                user=request.user,
                platform="spotify",
                post_type="playlists",
                social_posts=social_posts)

        except Exception as e:
            return error_response(
                message=f"Error fetching Spotify playlists: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(data=playlists_spotify_data, message="Spotify playlists fetched successfully.")


class SpotifyFollowingSyncView(APIView):
    """Trigger background fetch of Spotify followings."""
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     fetch_spotify_tracks_task.delay(request.user.id)
    #     return Response(
    #         {"message": "Spotify track fetch task started."},
    #         status=status.HTTP_202_ACCEPTED
    #     )

    def post(self, request, *args, **kwargs):
        """Fetch Spotify tracks."""

        data_service = SpotifyDataService()
        auth_service = SpotifyAuthService()

        try:
            access_token = auth_service.get_access_token(request.user)
            following_spotify_data = data_service.fetch_user_following(access_token)
            social_posts = data_service.map_playlists_to_social_posts(request.user, following_spotify_data)
            data_service.bulk_update_social_posts(
                user=request.user,
                platform="spotify",
                post_type="artists",
                social_posts=social_posts)

        except Exception as e:
            return error_response(
                message=f"Error fetching Spotify following: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(data=following_spotify_data, message="Spotify following fetched successfully.")
