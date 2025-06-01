from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
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

    def fetch_user_tracks(self, access_token: str) -> dict:
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
            return {"count": total_count, "tracks_len": len(tracks), "tracks": tracks}
        except requests.RequestException as e:
            logger.error(f"Error fetching user tracks: {e}")
            raise SpotifyApiError("Failed to fetch user tracks from Spotify.")
