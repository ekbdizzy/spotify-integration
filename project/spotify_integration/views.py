from django.contrib.auth import login as django_login
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from spotify_integration.serializers import (SpotifyAuthSerializer,
                                             SpotifyCallbackSerializer)
from spotify_integration.services import SpotifyAuthService, SpotifyService, StateStorageService


class SpotifyAuthView(APIView):
    """View to handle Spotify authentication."""

    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    serializer_class = SpotifyCallbackSerializer
    storage_service = StateStorageService()
    spotify_service = SpotifyService()
    auth_service = SpotifyAuthService()

    def get(self, request, *args, **kwargs):
        """Handle Spotify callback."""

        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if error := serializer.validated_data.get("error"):
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (code := serializer.validated_data.get("code")):
            return Response(
                {"error": "Missing code parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state = serializer.validated_data.get("state")
        if not self.storage_service.is_valid_oauth_state(state):
            return Response(
                {"error": "Invalid or expired state parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_info = self.spotify_service.exchange_code_for_tokens(code)  # TODO add pydantic validation
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
            raise e

        return Response(
            {"message": "Spotify authentication successful."},
            status=status.HTTP_200_OK,
        )
