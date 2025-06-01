from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.contrib.auth.models import User
from spotify_integration.models import SocialPost
from spotify_integration.schemes import SocialPostScheme
from spotify_integration.services.spotify_service import SpotifyApiError
import logging
import requests

logger = logging.getLogger(__name__)


class SpotifyDataService:
    """Service to fetch data from Spotify API."""

    @staticmethod
    def _fetch_paginated_page(url: str, headers: dict, limit: int, offset: int) -> dict:
        response = requests.get(url,
                                headers=headers,
                                params={
                                    "limit": limit,
                                    "offset": offset
                                })
        return response.json()

    def fetch_user_tracks(self, access_token: str) -> list:
        """Fetch user's tracks from Spotify.
        Try to fetch first page and remaining pages in async mode if user has more than one page data."""
        limit = settings.DEFAULT_LIMIT
        workers = settings.MAX_THREADS
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        url = "https://api.spotify.com/v1/me/tracks"

        try:
            first_response = requests.get(url, headers=headers, params={"limit": limit, "offset": 0})
            first_page_data = first_response.json()
            if first_response.status_code != 200:
                logger.error(
                    f"Error fetching user tracks: {first_page_data.get('error', {}).get('message', 'Unknown error')}")
                raise SpotifyApiError("Failed to fetch user tracks from Spotify.")

            total_count = first_page_data.get("total", 0)
            tracks = first_page_data.get("items", [])

            if total_count > limit:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(
                        self._fetch_paginated_page, url, headers, limit, offset
                    ) for offset in range(limit, total_count, limit)]
                    for future in futures:
                        logger.info("started fetching page")
                        page_data = future.result()
                        if page_data.get("items"):
                            tracks.extend(page_data["items"])
            return tracks
        except requests.RequestException as e:
            logger.error(f"Error fetching user tracks: {e}")
            raise SpotifyApiError("Failed to fetch user tracks from Spotify.")

    def map_tracks_to_social_posts(self, user: User, tracks: list) -> list[SocialPostScheme]:
        """Map Spotify tracks to social post data."""

        result = []

        for track in tracks:
            platform = "spotify"
            external_id = f"track_{track["track"]["id"]}"
            external_url = track["track"]["external_urls"]["spotify"]
            external_user_url = f"https://open.spotify.com/user/{user.username}"
            posted_at = track["added_at"]
            title = track["track"]["name"]
            images_url = [
                {
                    "height": img["height"],
                    "width": img["width"],
                    "url": img["url"]
                } for img in track["track"]["album"]["images"]
            ] if track["track"]["album"]["images"] else None
            result.append(SocialPostScheme(
                platform=platform,
                external_id=external_id,
                external_url=external_url,
                external_username=user.username,
                external_user_url=external_user_url,
                posted_at=posted_at,
                title=title,
                images_url=images_url
            ))
        return result

    def bulk_update_social_posts(self,
                                 user: User,
                                 platform: str,
                                 post_type: str,
                                 social_posts: list[SocialPostScheme]
                                 ) -> None:
        """Bulk update social posts in the database."""

        if not social_posts:
            SocialPost.objects.filter(platform=platform, post_type=post_type, user=user).delete()
            return

        SocialPost.bulk_update_social_posts(
            user=user,
            platform=platform,
            post_type=post_type,
            social_posts=social_posts
        )
        logger.info(f"Bulk updated {len(social_posts)} social posts for user {user.username}.")
