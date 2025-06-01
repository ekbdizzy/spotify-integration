from django.contrib.auth import login as django_login, logout
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from spotify_integration.models import SocialCredential
from spotify_integration.serializers import (SpotifyAuthSerializer,
                                             SpotifyCallbackSerializer)
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

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


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
            logger.error(f"Spotify authentication error: {error}")
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (code := serializer.validated_data.get("code")):
            logger.error(f"Spotify authentication error: {code}")
            return Response(
                {"error": "Missing code parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state = serializer.validated_data.get("state")
        if not self.storage_service.is_valid_oauth_state(state):
            logger.error(f"Invalid or expired state parameter: {state}")
            return Response(
                {"error": "Invalid or expired state parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_info: TokenInfo = self.spotify_service.exchange_code_for_tokens(code)
            user, created = self.auth_service.authenticate_or_create_user(token_info)
            self.auth_service.create_or_update_user_credentials(user, token_info)
            django_login(request, user)

            # TODO start a background task to sync the user's Spotify data

            return Response(
                {
                    "message": "Spotify authentication successful.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Spotify authentication error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Spotify authentication successful."},
            status=status.HTTP_200_OK,
        )


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
                return Response(
                    {"message": "Spotify account disconnected successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "No Spotify account connected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.error(f"Spotify disconnect error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
                return Response(
                    {"error": "No Spotify account connected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if credentials.refresh_token is None:
                return Response(
                    {"error": "No refresh token available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token_info: TokenInfo = self.spotify_service.refresh_access_token(credentials.refresh_token_value)
            self.auth_service.create_or_update_user_credentials(request.user, token_info)

            return Response(
                {"message": "Spotify access token refreshed successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Spotify refresh error: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SpotifyTrackListView(APIView):
    """Trigger background fetch of Spotify tracks."""
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     fetch_spotify_tracks_task.delay(request.user.id)
    #     return Response(
    #         {"message": "Spotify track fetch task started."},
    #         status=status.HTTP_202_ACCEPTED
    #     )

    def get(self, request, *args, **kwargs):
        """Fetch Spotify tracks."""

        data_service = SpotifyDataService()
        auth_service = SpotifyAuthService()

        try:
            access_token = auth_service.get_access_token(request.user)
            tracks_data = data_service.fetch_user_tracks(access_token)
            return Response(
                tracks_data,
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            # TODO update credentials if expired
            logger.error(f"Spotify authentication error: {e}")

        except Exception as e:
            logger.error(f"Error fetching Spotify tracks: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
