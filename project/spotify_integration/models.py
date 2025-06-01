from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone

from spotify_integration.schemes import SocialPostScheme

PLATFORM_CHOICES = [
    ("spotify", "Spotify"),
]


class EncryptedFieldMixin:
    """Mixin for handling encrypted fields."""

    @staticmethod
    def encrypt_token(token: str) -> bytes:
        fernet = Fernet(settings.FERNET_KEY.encode())
        return fernet.encrypt(token.encode())

    @staticmethod
    def decrypt_token(encrypted_token: bytes) -> str:
        fernet = Fernet(settings.FERNET_KEY.encode())
        return fernet.decrypt(encrypted_token).decode()


class SocialCredentialManager(models.Manager):
    def get_access_token(self, user: User) -> str | None:
        """Retrieve the access token for a given user.
        If the token is expired, it returns None."""
        credential = self.filter(user=user, platform="spotify").first()
        if credential and not credential.is_expired:
            return credential.access_token_value
        return None


class SocialCredential(models.Model, EncryptedFieldMixin):
    """Model to store social credentials for users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_credentials",
    )
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
        verbose_name="Social media platform",
    )
    access_token = models.BinaryField(
        max_length=500,
    )
    refresh_token = models.BinaryField(null=True, blank=True, max_length=500)
    platform_user_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name="Social media platform user ID",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_credentials"
        unique_together = ["user", "platform"]

    objects = SocialCredentialManager()

    def __str__(self):
        return f"{self.platform} credential for {self.user.username}"

    @property
    def access_token_value(self):
        """Decrypt and return the access token."""
        token = self.decrypt_token(bytes(self.access_token))
        return token

    @access_token_value.setter
    def access_token_value(self, token: str):
        """Encrypt and set the access token."""
        fernet = Fernet(settings.FERNET_KEY.encode())
        self.access_token = fernet.encrypt(token.encode())

    @property
    def refresh_token_value(self):
        """Decrypt and return the refresh token."""
        if self.refresh_token:
            return self.decrypt_token(bytes(self.refresh_token))
        return None

    @refresh_token_value.setter
    def refresh_token_value(self, token: str):
        """Encrypt and set the refresh token."""
        if token:
            fernet = Fernet(settings.FERNET_KEY.encode())
            self.refresh_token = fernet.encrypt(token.encode())
        else:
            self.refresh_token = None

    @property
    def is_expired(self) -> bool:
        """Check if the credential is expired."""
        if not self.expires_at:
            return True
        return self.expires_at <= timezone.now()


class SocialPost(models.Model):
    """Model to store social media posts."""

    POST_TYPE_CHOICES = [
        ("tracks", "Tracks"),
        ("playlists", "Playlists"),
        ("following", "Follows"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_posts",
    )
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
        verbose_name="Social media platform",
    )
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, db_index=True, null=True)
    external_id = models.CharField(max_length=50, unique=True, verbose_name="External post ID")
    external_url = models.URLField(max_length=250, unique=True,
                                   verbose_name="Link to entity (song, artist, etc...) on Spotify")
    external_username = models.CharField(max_length=100, verbose_name="Link to user's profile on Spotify")
    external_user_url = models.URLField(max_length=250, null=True, blank=True,
                                        verbose_name="Link to external user profile")
    posted_at = models.DateTimeField(verbose_name="Date of event", null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Title of the post")
    text = models.TextField(null=True, blank=True, verbose_name="Text of the post")
    videos_url = models.JSONField(null=True, blank=True, verbose_name="Videos URL")
    images_url = models.JSONField(null=True, blank=True, verbose_name="Images URL")
    links_url = models.JSONField(null=True, blank=True, verbose_name="Links URL")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_posts"
        unique_together = ["user", "platform", "external_url"]

    def __str__(self):
        return f"Post on {self.platform} by {self.user.username}"

    @classmethod
    @transaction.atomic
    def bulk_update_social_posts(cls,
                                 user: User,
                                 platform: str,
                                 post_type: str,
                                 social_posts: list[SocialPostScheme]
                                 ) -> None:
        """
        Synchronize social posts for a user/platform/post_type:
        - Add new posts
        - Do NOT update existing ones
        - Remove only posts of the same (user, platform, post_type) that are missing
        """
        if not social_posts:
            cls.objects.filter(user=user, platform=platform, post_type=post_type).delete()
            return

        incoming_by_url = {post.external_url: post for post in social_posts}

        existing_posts = cls.objects.filter(
            user=user,
            platform=platform,
            post_type=post_type
        ).only("external_url")

        existing_urls = {post.external_url for post in existing_posts}
        incoming_urls = set(incoming_by_url.keys())

        urls_to_add = incoming_urls - existing_urls
        urls_to_remove = existing_urls - incoming_urls

        posts_to_create = []
        for url in urls_to_add:
            post = incoming_by_url[url]
            posts_to_create.append(cls(
                user=user,
                platform=platform,
                post_type=post_type,
                external_id=post.external_id,
                external_url=post.external_url,
                external_username=post.external_username,
                external_user_url=post.external_user_url,
                posted_at=post.posted_at,
                title=post.title,
                text=post.text,
                videos_url=[video.model_dump() for video in (post.videos_url or [])],
                images_url=[image.model_dump() for image in (post.images_url or [])],
                links_url=[link.model_dump() for link in (post.links_url or [])],
            ))

        # Bulk insert (ignores duplicates, if any)
        for batch_start_index in range(0, len(posts_to_create), settings.BATCH_SIZE):
            cls.objects.bulk_create(
                posts_to_create[batch_start_index:batch_start_index + settings.BATCH_SIZE],
                ignore_conflicts=True
            )

        # Remove redundant posts only for current user, platform, post_type
        if urls_to_remove:
            cls.objects.filter(
                user=user,
                platform=platform,
                post_type=post_type,
                external_url__in=list(urls_to_remove)
            ).delete()
