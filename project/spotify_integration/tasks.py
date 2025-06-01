import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from spotify_integration.services import SpotifyDataService, SpotifyAuthService

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
