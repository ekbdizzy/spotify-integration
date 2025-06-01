import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from spotify_integration.services import SpotifyDataService, SpotifyAuthService, SpotifyService
from spotify_integration.models import SocialCredential

from spotify_integration.services.spotify_service import SpotifyApiError

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_spotify_tracks_task(self, user_id: int):
    """Fetch Spotify tracks in the background."""

    data_service = SpotifyDataService()
    auth_service = SpotifyAuthService()

    try:
        user = User.objects.get(pk=user_id)
        access_token = auth_service.get_access_token(user)
        tracks_spotify_data = data_service.fetch_user_tracks(access_token)
        social_posts = data_service.map_tracks_to_social_posts(user, tracks_spotify_data)
        data_service.bulk_update_social_posts(
            user=user,
            platform="spotify",
            post_type="tracks",
            social_posts=social_posts,
        )
        logging.info(f"Fetched Spotify tracks for user {user.id} successfully.")

    except User.DoesNotExist:
        logging.error(f"User with ID {user_id} does not exist.", exc_info=True)

    except SpotifyApiError as e:
        logging.warning(f"Spotify API error for user {user_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {e}", exc_info=True)
        raise SpotifyApiError("Failed to fetch Spotify tracks.") from e


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_spotify_playlists_task(self, user_id: int):
    """Fetch Spotify playlists in the background."""

    data_service = SpotifyDataService()
    auth_service = SpotifyAuthService()

    try:
        user = User.objects.get(pk=user_id)
        access_token = auth_service.get_access_token(user)
        playlists_spotify_data = data_service.fetch_user_playlists(access_token)
        social_posts = data_service.map_playlists_to_social_posts(user, playlists_spotify_data)
        data_service.bulk_update_social_posts(
            user=user,
            platform="spotify",
            post_type="playlists",
            social_posts=social_posts,
        )
        logging.info(f"Fetched Spotify playlists for user {user.id} successfully.")

    except User.DoesNotExist:
        logging.error(f"User with ID {user_id} does not exist.", exc_info=True)

    except SpotifyApiError as e:
        logging.warning(f"Spotify API error for user {user_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {e}", exc_info=True)
        raise SpotifyApiError("Failed to fetch Spotify playlists.") from e


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_spotify_following_task(self, user_id: int):
    """Fetch Spotify following in the background."""

    data_service = SpotifyDataService()
    auth_service = SpotifyAuthService()

    try:
        user = User.objects.get(pk=user_id)
        access_token = auth_service.get_access_token(user)
        following_spotify_data = data_service.fetch_user_following(access_token)
        social_posts = data_service.map_following_artists_to_social_posts(user, following_spotify_data)
        data_service.bulk_update_social_posts(
            user=user,
            platform="spotify",
            post_type="following",
            social_posts=social_posts,
        )
        logging.info(f"Fetched Spotify following for user {user.id} successfully.")

    except User.DoesNotExist:
        logging.error(f"User with ID {user_id} does not exist.", exc_info=True)

    except SpotifyApiError as e:
        logging.warning(f"Spotify API error for user {user_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {e}", exc_info=True)
        raise SpotifyApiError("Failed to fetch Spotify following.") from e


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_access_token_task(self, user_id: int):
    """Refresh Spotify access token in the background."""

    spotify_service = SpotifyService()
    auth_service = SpotifyAuthService()

    try:
        credentials = SocialCredential.objects.filter(user_id=user_id, platform="spotify").first()
        if credentials is None:
            logging.error(f"No Spotify account connected for user {user_id}.")
            return

        if credentials.refresh_token is None:
            logging.error(f"No Spotify refresh token available for user {user_id}.")
            return

        token_info = spotify_service.refresh_access_token(credentials.refresh_token_value)
        auth_service.create_or_update_user_credentials(User.objects.get(pk=user_id), token_info)
        logging.info(f"Refreshed Spotify access token for user {user_id} successfully.")

    except Exception as e:
        logging.error(f"Spotify refresh token error for user {user_id}: {e}", exc_info=True)
        raise self.retry(exc=e)
