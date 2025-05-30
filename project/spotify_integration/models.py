from django.conf import settings
from django.db import models


class SocialCredential(models.Model):
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
        max_length=50, 
    )
    refresh_token = models.BinaryField(
        null=True, blank=True, max_length=50
    )
    platform_user_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name="Social media platform user ID",
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_credentials"
        unique_together = ["user", "platform"]

    def __str__(self):
        return f"{self.provider} credential for {self.user.username}"
