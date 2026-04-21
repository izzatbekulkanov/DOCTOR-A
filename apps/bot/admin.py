from django.contrib import admin

from .models import BotChannel, BotDispatchLog, BotFileSubmission, BotSettings, BotTelegramUpdate


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ("bot_name", "chat_id", "is_active", "last_status", "last_tested_at", "updated_at")
    readonly_fields = ("last_status", "last_error", "last_response", "last_tested_at", "created_at", "updated_at")
    fieldsets = (
        ("Asosiy sozlamalar", {
            "fields": ("bot_name", "bot_token", "chat_id", "parse_mode", "is_active", "notes"),
        }),
        ("Oxirgi holat", {
            "fields": ("last_status", "last_error", "last_response", "last_tested_at"),
        }),
        ("Tizim ma'lumotlari", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return not BotSettings.objects.exists()


@admin.register(BotDispatchLog)
class BotDispatchLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "status", "target_chat_id", "created_at")
    list_filter = ("event_type", "status", "created_at")
    search_fields = ("target_chat_id", "message_preview", "error_text")
    readonly_fields = (
        "settings",
        "event_type",
        "status",
        "target_chat_id",
        "message_preview",
        "response_payload",
        "error_text",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(BotChannel)
class BotChannelAdmin(admin.ModelAdmin):
    list_display = ("display_name", "chat_id", "chat_type", "member_status", "is_bot_admin", "last_verified_at")
    list_filter = ("chat_type", "member_status", "is_bot_admin")
    search_fields = ("chat_id", "label", "chat_title", "chat_username")
    readonly_fields = ("chat_title", "chat_username", "chat_type", "member_status", "is_bot_admin", "last_error", "last_payload", "last_verified_at", "created_at", "updated_at")


@admin.register(BotTelegramUpdate)
class BotTelegramUpdateAdmin(admin.ModelAdmin):
    list_display = ("update_id", "update_type", "display_chat", "chat_id", "message_date", "created_at")
    list_filter = ("update_type", "chat_type", "has_photo", "has_reply_markup", "created_at")
    search_fields = ("chat_id", "chat_title", "chat_username", "text", "author_name")
    readonly_fields = (
        "update_id",
        "update_type",
        "chat_id",
        "chat_title",
        "chat_username",
        "chat_type",
        "message_id",
        "message_date",
        "author_name",
        "text",
        "has_photo",
        "has_reply_markup",
        "raw_payload",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(BotFileSubmission)
class BotFileSubmissionAdmin(admin.ModelAdmin):
    list_display = ("custom_id", "status", "author_display", "target_chat_id", "target_message_id", "created_at")
    list_filter = ("status", "file_type", "created_at", "published_at")
    search_fields = ("custom_id", "telegram_username", "telegram_first_name", "telegram_last_name", "target_chat_id", "generated_caption")
    readonly_fields = (
        "custom_id",
        "status",
        "telegram_user_id",
        "telegram_username",
        "telegram_first_name",
        "telegram_last_name",
        "source_chat_id",
        "source_message_id",
        "file_type",
        "file_id",
        "file_unique_id",
        "original_text",
        "target_channel",
        "target_chat_id",
        "target_message_id",
        "generated_caption",
        "error_text",
        "raw_payload",
        "published_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
