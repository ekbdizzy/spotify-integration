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
