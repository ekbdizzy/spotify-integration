from django.contrib import admin

from spotify_integration.models import SocialCredential, SocialPost


@admin.register(SocialCredential)
class SocialCredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "platform_user_id", "expires_at")
    search_fields = ("user__username", "platform", "platform_user_id")
    list_filter = ("platform",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "post_type", "created_at")
    search_fields = ("user__username", "platform", "post_type")
    list_filter = ("platform", "post_type")
    readonly_fields = ("created_at", "updated_at")
