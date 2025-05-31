import secrets

from django.conf import settings
from redis import Redis


class StateStorageService:
    def __init__(self, ):
        self.redis_client = Redis.from_url(settings.REDIS_URL)
        self.state_prefix = "oauth_state"
        self.state_ttl = settings.REDIS_OAUTH_STATE_EXPIRE

    def generate_oauth_state(self):
        """Set a unique state for OAuth."""
        state = secrets.token_urlsafe(32)
        key = f"{self.state_prefix}:{state}"
        self.redis_client.setex(key, settings.REDIS_OAUTH_STATE_EXPIRE, state)
        return state

    def is_valid_oauth_state(self, state):
        """Validate the OAuth state."""
        key = f"{self.state_prefix}:{state}"
        if self.redis_client.exists(key):
            self.redis_client.delete(key)
            return True
        return False
