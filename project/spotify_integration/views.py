from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from spotify_integration.services.spotify_auth_service import \
    SpotifyAuthService
from spotify_integration.services.spotify_service import SpotifyService


class SpotifyAuthView(APIView):
    """
    View to handle Spotify authentication.
    """

    def get(self, request, *args, **kwargs):
        """Get URL for Spotify authentication."""
        spotify_service = SpotifyService()
        auth_url, state = spotify_service.get_auth_url()

        request.session["spotify_oauth_state"] = state
        return Response(
            {"auth_url": auth_url, "state": state},
            status=status.HTTP_200_OK,
        )


class SpotifyCallbackView(APIView):
    """
    View to handle Spotify callback after authentication.
    """

    def get(self, request, *args, **kwargs):
        """Handle Spotify callback."""
        state = request.GET.get("state")
        code = request.GET.get("code")
        error = request.GET.get("error")

        if error:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if code is None:
            return Response(
                {"error": "Missing code parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if state != request.session.get("spotify_oauth_state"):
            return Response(
                {"error": "Invalid state parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            spotify_service = SpotifyService()
            auth_service = SpotifyAuthService()

            token_info = spotify_service.exchange_code_for_tokens(code)
            credentials = token_info.get("credentials")

            # TODO start a background task to sync the user's Spotify data

            return Response(
                {
                    "message": "Spotify authentication successful.",
                    "credentials": credentials,
                },
                status=status.HTTP_200_OK,
            )

        except:
            pass

        finally:
            request.session.pop("spotify_oauth_state", None)

        return Response(
            {"message": "Spotify authentication successful."},
            status=status.HTTP_200_OK,
        )
