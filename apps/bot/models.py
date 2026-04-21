from django.db import models
from django.utils.translation import gettext_lazy as _


BOT_STATUS_CHOICES = [
    ("unknown", _("Noma'lum")),
    ("success", _("Muvaffaqiyatli")),
    ("error", _("Xato")),
    ("skipped", _("O'tkazib yuborildi")),
]

CHANNEL_MEMBER_STATUS_CHOICES = [
    ("unknown", _("Noma'lum")),
    ("creator", _("Ega")),
    ("administrator", _("Administrator")),
    ("member", _("A'zo")),
    ("restricted", _("Cheklangan")),
    ("left", _("Chiqib ketgan")),
    ("kicked", _("Bloklangan")),
    ("not_found", _("Topilmadi")),
    ("error", _("Xato")),
]


class BotSettings(models.Model):
    PARSE_MODE_CHOICES = [
        ("HTML", "HTML"),
        ("Markdown", "Markdown"),
        ("MarkdownV2", "MarkdownV2"),
        ("", _("Oddiy matn")),
    ]

    bot_name = models.CharField(max_length=120, default="Doctor A Bot")
    bot_token = models.CharField(max_length=255, blank=True, help_text=_("Telegram bot tokenini kiriting"))
    chat_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Kanal username yoki chat ID. Masalan: @Doctor_a_HOSPITAL"),
    )
    parse_mode = models.CharField(
        max_length=20,
        choices=PARSE_MODE_CHOICES,
        default="HTML",
        blank=True,
        help_text=_("Xabarlarni qanday formatda yuborishni tanlang"),
    )
    default_publish_channel = models.ForeignKey(
        "BotChannel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_settings",
        help_text=_("Bot orqali kelgan fayllar yuboriladigan asosiy kanal"),
    )
    is_active = models.BooleanField(default=True, help_text=_("Bot tizim xabarlarini yuborishi mumkin"))
    notes = models.TextField(blank=True, help_text=_("Bot haqida ichki izohlar"))
    last_status = models.CharField(max_length=20, choices=BOT_STATUS_CHOICES, default="unknown")
    last_error = models.TextField(blank=True)
    last_response = models.JSONField(default=dict, blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bot sozlamasi")
        verbose_name_plural = _("Bot sozlamalari")

    def __str__(self):
        return self.bot_name or "Doctor A Bot"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        instance, _created = cls.objects.get_or_create(pk=1, defaults={"bot_name": "Doctor A Bot"})
        return instance

    @property
    def is_configured(self):
        return bool(self.bot_token and self.chat_id)

    @property
    def masked_token(self):
        token = (self.bot_token or "").strip()
        if not token:
            return "-"
        if len(token) <= 10:
            return token
        return f"{token[:6]}...{token[-4:]}"

    @property
    def masked_chat_id(self):
        chat_id = (self.chat_id or "").strip()
        if not chat_id:
            return "-"
        if chat_id.startswith("@"):
            return chat_id
        if len(chat_id) <= 6:
            return chat_id
        return f"{chat_id[:3]}...{chat_id[-3:]}"


class BotDispatchLog(models.Model):
    EVENT_TYPE_CHOICES = [
        ("notification", _("Tizim xabari")),
        ("test", _("Sinov xabari")),
        ("manual", _("Qo'lda yuborilgan")),
    ]

    settings = models.ForeignKey(
        BotSettings,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatch_logs",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default="notification")
    status = models.CharField(max_length=20, choices=BOT_STATUS_CHOICES, default="unknown")
    target_chat_id = models.CharField(max_length=255, blank=True)
    message_preview = models.TextField(blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bot jo'natish logi")
        verbose_name_plural = _("Bot jo'natish loglari")
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.get_status_display()}"


class BotChannel(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255, blank=True)
    chat_title = models.CharField(max_length=255, blank=True)
    chat_username = models.CharField(max_length=255, blank=True)
    chat_type = models.CharField(max_length=50, blank=True)
    member_status = models.CharField(max_length=32, choices=CHANNEL_MEMBER_STATUS_CHOICES, default="unknown")
    is_bot_admin = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)
    last_payload = models.JSONField(default=dict, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bot kanali")
        verbose_name_plural = _("Bot kanallari")
        ordering = ["label", "chat_title", "chat_id"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.label or self.chat_title or self.chat_username or self.chat_id

    @property
    def resolved_username(self):
        username = (self.chat_username or "").strip()
        if not username:
            return ""
        return username if username.startswith("@") else f"@{username}"

    @property
    def is_joined(self):
        return self.member_status in {"creator", "administrator", "member", "restricted"}


class BotTelegramUpdate(models.Model):
    update_id = models.BigIntegerField(unique=True)
    update_type = models.CharField(max_length=64, blank=True)
    chat_id = models.CharField(max_length=255, blank=True)
    chat_title = models.CharField(max_length=255, blank=True)
    chat_username = models.CharField(max_length=255, blank=True)
    chat_type = models.CharField(max_length=50, blank=True)
    message_id = models.BigIntegerField(null=True, blank=True)
    message_date = models.DateTimeField(null=True, blank=True)
    author_name = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    has_photo = models.BooleanField(default=False)
    has_reply_markup = models.BooleanField(default=False)
    raw_payload = models.JSONField(default=dict, blank=True)
    workflow_processed = models.BooleanField(default=False)
    workflow_status = models.CharField(max_length=32, blank=True)
    workflow_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Telegram update")
        verbose_name_plural = _("Telegram update'lar")
        ordering = ["-update_id"]

    def __str__(self):
        return f"{self.update_id} - {self.display_chat}"

    @property
    def display_chat(self):
        return self.chat_title or self.chat_username or self.chat_id or "-"

    @property
    def display_text(self):
        if self.text:
            return self.text
        if self.has_photo:
            return _("Rasmli xabar")
        return _("Matn yo'q")


class BotFileSubmission(models.Model):
    STATUS_CHOICES = [
        ("awaiting_id", _("ID kutilmoqda")),
        ("published", _("Yuborilgan")),
        ("error", _("Xato")),
    ]

    custom_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="awaiting_id")

    telegram_user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    telegram_username = models.CharField(max_length=255, blank=True)
    telegram_first_name = models.CharField(max_length=255, blank=True)
    telegram_last_name = models.CharField(max_length=255, blank=True)

    source_chat_id = models.CharField(max_length=255, blank=True)
    source_message_id = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_id = models.CharField(max_length=512, blank=True)
    file_unique_id = models.CharField(max_length=255, blank=True)
    original_text = models.TextField(blank=True)

    target_channel = models.ForeignKey(
        BotChannel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="file_submissions",
    )
    target_chat_id = models.CharField(max_length=255, blank=True)
    target_message_id = models.BigIntegerField(null=True, blank=True)
    target_meta_message_id = models.BigIntegerField(null=True, blank=True)
    publish_method = models.CharField(max_length=32, blank=True, default="")
    generated_caption = models.TextField(blank=True)
    error_text = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bot fayl yozuvi")
        verbose_name_plural = _("Bot fayl yozuvlari")
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.custom_id or f"Pending #{self.id}"

    @property
    def author_display(self):
        full_name = " ".join(
            part for part in (self.telegram_first_name, self.telegram_last_name) if part
        ).strip()
        if self.telegram_username and full_name:
            return f"{full_name} (@{self.telegram_username})"
        if self.telegram_username:
            return f"@{self.telegram_username}"
        return full_name or str(self.telegram_user_id or "-")
