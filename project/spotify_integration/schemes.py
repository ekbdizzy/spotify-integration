from datetime import datetime

from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int = 3600  # Default to 1 hour
    scope: str
    token_type: str


class SpotifyProfile(BaseModel):
    country: str | None = None
    display_name: str | None = None
    email: str | None = None
    explicit_content: dict | None = Field(default_factory=dict)
    external_urls: dict | None = Field(default_factory=dict)
    followers: dict | None = Field(default_factory=dict)
    href: str | None = None
    id: str | None = None
    images: list[dict] | None = Field(default_factory=list)
    product: str | None = None
    type: str | None = None
    uri: str | None = None

    model_config = {
        "extra": "ignore"
    }


class Image(BaseModel):
    height: int | None = None
    width: int | None = None
    url: str


class SocialVideo(BaseModel):
    url: str  # Link to video
    thumbnail_url: str | None = None  # Thumbnail image URL (optional)
    title: str | None = None  # Title of the video (optional)
    description: str | None = None  # Description of the video (optional)


class SocialLink(BaseModel):
    url: str  # Link to external resource
    platform: str | None = None  # Title of the link (optional)


class SocialPostScheme(BaseModel):
    platform: str  # spotify
    external_id: str  # External post id
    external_url: str  # Link to entity (song, artist, etc...) on Spotify
    external_username: str  # Username of authorised user
    external_user_url: str  # Link to user's profile on Spotify
    posted_at: datetime | None = None  # Date of event
    title: str | None = None  # Title (different for different events) (optional)
    text: str | None = None  # Text (different for different events) (optional)
    videos_url: list[SocialVideo] = None
    images_url: list[Image] | None = None
    links_url: list[SocialLink] | None = None
