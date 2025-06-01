from rest_framework import serializers


class SpotifyAuthSerializer(serializers.Serializer):
    """Serializer for handling Spotify authentication data."""

    class Meta:
        fields = ['auth_url', 'state']

    auth_url = serializers.URLField(
        read_only=True, help_text="URL for Spotify authentication"
    )
    state = serializers.CharField(
        read_only=True, help_text="State parameter for CSRF protection"
    )


class SpotifyCallbackSerializer(serializers.Serializer):
    """Serializer for handling Spotify callback data."""

    class Meta:
        fields = ['state', 'code', 'error']

    state = serializers.CharField(
        required=True, help_text="State parameter from Spotify"
    )
    code = serializers.CharField(
        required=True, help_text="Authorization code from Spotify"
    )
    error = serializers.CharField(
        required=False, allow_blank=True, help_text="Error message"
    )
