from django.conf import settings
from django.db import models
from django.utils import timezone
from cryptography.fernet import Fernet


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


class SocialCredential(models.Model, EncryptedFieldMixin):
    """
    Model to store social credentials for users.
    """

    PLATFORM_CHOICES = [
        ("spotify", "Spotify"),
    ]

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

    def __str__(self):
        return f"{self.platform} credential for {self.user.username}"

    @property
    def access_token_value(self):
        """Decrypt and return the access token."""
        return self.decrypt_token(self.access_token)

    @access_token_value.setter
    def access_token_value(self, token: str):
        """Encrypt and set the access token."""
        fernet = Fernet(settings.FERNET_KEY.encode())
        self.access_token = fernet.encrypt(token.encode())

    @property
    def refresh_token_value(self):
        """Decrypt and return the refresh token."""
        if self.refresh_token:
            return self.decrypt_token(self.refresh_token)
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
