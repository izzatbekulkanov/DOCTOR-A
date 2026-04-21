import json
import math
import mimetypes
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.parse import urlparse

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from config.telegram_bot import (
    DEFAULT_BOT_CHAT_ID,
    DEFAULT_BOT_NAME,
    DEFAULT_BOT_PARSE_MODE,
    DEFAULT_BOT_TOKEN,
    answer_callback_query,
    check_bot_health,
    copy_message_to_chat,
    delete_bot_webhook,
    fetch_bot_updates,
    forward_message_to_chat,
    get_bot_runtime_config,
    get_telegram_file,
    inspect_bot_chat,
    send_chat_message,
    send_message,
    set_bot_webhook,
)

from .models import BotChannel, BotDispatchLog, BotFileSubmission, BotSettings, BotTelegramUpdate
from .worker import DEFAULT_POLL_TIMEOUT, DEFAULT_SLEEP, get_worker_state, start_worker_process, stop_worker_processes


CUSTOM_ID_PATTERN = re.compile(r"\b\d{3,}\b")


def parse_worker_period_form(data):
    def parse_numeric(raw_value, *, default, minimum, integer=False):
        value = str(raw_value or "").strip() or str(default)
        value = value.replace(",", ".")
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ValueError
        if integer:
            numeric_value = int(numeric_value)
        return max(minimum, numeric_value)

    poll_timeout = parse_numeric(
        data.get("poll_timeout", DEFAULT_POLL_TIMEOUT),
        default=DEFAULT_POLL_TIMEOUT,
        minimum=1,
        integer=True,
    )
    sleep = parse_numeric(
        data.get("sleep", DEFAULT_SLEEP),
        default=DEFAULT_SLEEP,
        minimum=0.2,
    )
    return poll_timeout, sleep


@method_decorator(login_required, name="dispatch")
class BotControlView(View):
    template_name = "bot/bot_control.html"
    paginate_by = 12
    joined_statuses = {"creator", "administrator", "member", "restricted"}

    @staticmethod
    def mask_value(value, *, prefix=3, suffix=3):
        value = (value or "").strip()
        if not value:
            return "-"
        if value.startswith("@"):
            return value
        if len(value) <= prefix + suffix + 1:
            return value
        return f"{value[:prefix]}...{value[-suffix:]}"

    def get_settings_object(self):
        return BotSettings.get_solo()

    @staticmethod
    def normalize_chat_identifier(value):
        raw_value = (value or "").strip()
        if not raw_value:
            return ""

        if raw_value.startswith("http://") or raw_value.startswith("https://"):
            parsed = urlparse(raw_value)
            path = (parsed.path or "").strip("/")
            if path.startswith("s/"):
                path = path[2:]
            if path and "/" in path:
                path = path.split("/", 1)[0]
            if path:
                raw_value = path

        raw_value = raw_value.rstrip("/")
        if raw_value.startswith("t.me/"):
            raw_value = raw_value.split("t.me/", 1)[1]
        if raw_value.startswith("@"):
            return raw_value
        if raw_value.startswith("-100") or raw_value.lstrip("-").isdigit():
            return raw_value
        return f"@{raw_value}"

    def get_channels_queryset(self):
        return BotChannel.objects.all().order_by("label", "chat_title", "chat_id")

    @staticmethod
    def get_update_payload(update):
        for key in ("channel_post", "edited_channel_post", "message", "edited_message", "callback_query"):
            if key in update:
                return key, update.get(key) or {}
        return "unknown", {}

    @staticmethod
    def get_update_author(payload):
        if payload.get("author_signature"):
            return payload["author_signature"]

        from_user = payload.get("from") or {}
        full_name = " ".join(
            part for part in (from_user.get("first_name"), from_user.get("last_name")) if part
        ).strip()
        if full_name:
            return full_name
        if from_user.get("username"):
            return f"@{from_user['username']}"

        sender_chat = payload.get("sender_chat") or {}
        return sender_chat.get("title") or sender_chat.get("username") or ""

    @staticmethod
    def parse_update_datetime(timestamp):
        if not timestamp:
            return None
        return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())

    def normalize_update_record(self, update):
        update_type, payload = self.get_update_payload(update)
        if update_type == "callback_query":
            chat = (payload.get("message") or {}).get("chat") or {}
            text = payload.get("data") or ""
        else:
            chat = payload.get("chat") or {}
            text = payload.get("text") or payload.get("caption") or ""

        return {
            "update_type": update_type,
            "chat_id": str(chat.get("id", "") or ""),
            "chat_title": chat.get("title", "") or "",
            "chat_username": chat.get("username", "") or "",
            "chat_type": chat.get("type", "") or "",
            "message_id": payload.get("message_id"),
            "message_date": self.parse_update_datetime(payload.get("date")),
            "author_name": self.get_update_author(payload),
            "text": text,
            "has_photo": bool(payload.get("photo")),
            "has_reply_markup": bool(payload.get("reply_markup")),
            "raw_payload": update,
        }

    @staticmethod
    def should_track_update_chat(defaults):
        return defaults.get("chat_type") in {"channel", "supergroup", "group"}

    @staticmethod
    def mark_update_workflow(update_record, status, error_text=""):
        update_record.workflow_processed = True
        update_record.workflow_status = status
        update_record.workflow_error = error_text
        update_record.save(
            update_fields=[
                "workflow_processed",
                "workflow_status",
                "workflow_error",
                "updated_at",
            ]
        )

    def process_update_workflow(self, update_record, settings_obj):
        if update_record.workflow_processed:
            return "skipped"

        webhook_processor = TelegramWebhookView()
        callback_query = webhook_processor.get_callback_payload(update_record.raw_payload)
        if callback_query:
            try:
                result = webhook_processor.handle_callback_query(callback_query, settings_obj)
            except Exception as exc:
                self.mark_update_workflow(update_record, "error", str(exc))
                return "error"

            if result.get("ok"):
                status = result.get("status") or "callback"
                self.mark_update_workflow(update_record, status)
                return status

            error_text = result.get("description") or result.get("error") or _("noma'lum xato")
            self.mark_update_workflow(update_record, "error", error_text)
            return "error"

        message = webhook_processor.get_message_payload(update_record.raw_payload)
        if not message:
            self.mark_update_workflow(update_record, "ignored")
            return "ignored"

        if not webhook_processor.should_process_message(message):
            self.mark_update_workflow(update_record, "ignored")
            return "ignored"

        try:
            result = webhook_processor.handle_message(message, settings_obj)
        except Exception as exc:
            self.mark_update_workflow(update_record, "error", str(exc))
            return "error"

        if result.get("ok"):
            status = result.get("status") or "processed"
            self.mark_update_workflow(update_record, status)
            return status

        error_text = result.get("description") or result.get("error") or _("noma'lum xato")
        self.mark_update_workflow(update_record, "error", error_text)
        return "error"

    def store_updates(self, updates, *, settings_obj=None, process_workflow=False):
        created_count = 0
        updated_count = 0
        channel_count = 0
        workflow_processed_count = 0
        workflow_ignored_count = 0
        workflow_error_count = 0

        for update in updates:
            update_id = update.get("update_id")
            if update_id is None:
                continue

            defaults = self.normalize_update_record(update)
            update_record, created = BotTelegramUpdate.objects.update_or_create(
                update_id=update_id,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            if process_workflow and not update_record.workflow_processed:
                workflow_status = self.process_update_workflow(update_record, settings_obj)
                if workflow_status == "ignored":
                    workflow_ignored_count += 1
                elif workflow_status == "error":
                    workflow_error_count += 1
                elif workflow_status != "skipped":
                    workflow_processed_count += 1

            chat_id = defaults.get("chat_id")
            if chat_id and self.should_track_update_chat(defaults):
                channel, channel_created = BotChannel.objects.get_or_create(
                    chat_id=chat_id,
                    defaults={
                        "label": defaults.get("chat_title") or defaults.get("chat_username") or chat_id,
                        "chat_title": defaults.get("chat_title", ""),
                        "chat_username": defaults.get("chat_username", ""),
                        "chat_type": defaults.get("chat_type", ""),
                    },
                )
                if channel_created:
                    channel_count += 1
                else:
                    update_fields = []
                    for field in ("chat_title", "chat_username", "chat_type"):
                        value = defaults.get(field, "")
                        if value and getattr(channel, field) != value:
                            setattr(channel, field, value)
                            update_fields.append(field)
                    if update_fields:
                        update_fields.append("updated_at")
                        channel.save(update_fields=update_fields)

        return (
            created_count,
            updated_count,
            channel_count,
            workflow_processed_count,
            workflow_ignored_count,
            workflow_error_count,
        )

    def ensure_primary_channel(self, bot_settings):
        chat_id = self.normalize_chat_identifier(bot_settings.chat_id)
        if not chat_id:
            return None
        if bot_settings.chat_id != chat_id:
            bot_settings.chat_id = chat_id
            bot_settings.save(update_fields=["chat_id", "updated_at"])
        channel, created = BotChannel.objects.get_or_create(
            chat_id=chat_id,
            defaults={"label": "Asosiy yuborish kanali"},
        )
        if not created and not channel.label:
            channel.label = "Asosiy yuborish kanali"
            channel.save(update_fields=["label", "updated_at"])
        return channel

    def sync_channel_state(self, channel, bot_settings):
        normalized_chat_id = self.normalize_chat_identifier(channel.chat_id)
        if normalized_chat_id and normalized_chat_id != channel.chat_id:
            channel.chat_id = normalized_chat_id
            channel.save(update_fields=["chat_id", "updated_at"])

        inspection = inspect_bot_chat(channel.chat_id, settings_obj=bot_settings)
        channel.chat_title = inspection.get("title", "") or ""
        channel.chat_username = inspection.get("username", "") or ""
        channel.chat_type = inspection.get("type", "") or ""
        channel.member_status = inspection.get("member_status", "unknown") or "unknown"
        channel.is_bot_admin = bool(inspection.get("is_bot_admin"))
        channel.last_error = inspection.get("error", "") or ""
        channel.last_payload = inspection.get("payload", {}) or {}
        channel.last_verified_at = timezone.now()
        channel.save(
            update_fields=[
                "chat_title",
                "chat_username",
                "chat_type",
                "member_status",
                "is_bot_admin",
                "last_error",
                "last_payload",
                "last_verified_at",
                "updated_at",
            ]
        )
        return inspection

    def get_logs_queryset(self, request):
        queryset = BotDispatchLog.objects.select_related("settings").all()

        search_query = request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(message_preview__icontains=search_query)
                | Q(target_chat_id__icontains=search_query)
                | Q(error_text__icontains=search_query)
            )

        status_filter = request.GET.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        event_filter = request.GET.get("event", "").strip()
        if event_filter:
            queryset = queryset.filter(event_type=event_filter)

        return queryset.order_by("-created_at", "-id")

    def get_test_message(self, bot_name):
        timestamp = timezone.localtime().strftime("%Y-%m-%d %H:%M")
        return _(
            "Sinov xabari.\nBot: %(bot_name)s\nVaqt: %(timestamp)s"
        ) % {
            "bot_name": bot_name,
            "timestamp": timestamp,
        }

    def build_redirect_url(self, request):
        return redirect(reverse("bot-control"))

    def get_context_data(self, request):
        bot_settings = self.get_settings_object()
        runtime_config = get_bot_runtime_config(bot_settings)
        worker_state = get_worker_state(bot_settings)
        self.ensure_primary_channel(bot_settings)
        logs_queryset = self.get_logs_queryset(request)
        logs_page = Paginator(logs_queryset, self.paginate_by).get_page(request.GET.get("page"))
        tracked_channels = list(self.get_channels_queryset())
        joined_channels = [channel for channel in tracked_channels if channel.member_status in self.joined_statuses]
        admin_channels = [channel for channel in tracked_channels if channel.is_bot_admin]
        selectable_channels = joined_channels or tracked_channels
        telegram_updates_queryset = BotTelegramUpdate.objects.all().order_by("-update_id")
        telegram_updates = Paginator(telegram_updates_queryset, 20).get_page(request.GET.get("updates_page"))
        submission_search_query = request.GET.get("submission_id", "").strip()
        search_custom_id = TelegramWebhookView.extract_custom_id(submission_search_query)
        if search_custom_id:
            TelegramWebhookView().find_channel_submissions(search_custom_id, bot_settings)
        file_submissions_queryset = BotFileSubmission.objects.select_related("target_channel").all()
        if submission_search_query:
            file_submissions_queryset = file_submissions_queryset.filter(
                Q(custom_id__icontains=submission_search_query)
                | Q(generated_caption__icontains=submission_search_query)
                | Q(telegram_username__icontains=submission_search_query)
            )
        file_submissions = Paginator(file_submissions_queryset, 20).get_page(request.GET.get("submissions_page"))
        selected_test_channel_id = request.GET.get("test_channel", "").strip()
        if not selected_test_channel_id and selectable_channels:
            selected_test_channel_id = str(selectable_channels[0].id)

        all_logs = BotDispatchLog.objects.all()
        week_ago = timezone.now() - timedelta(days=7)

        success_count = all_logs.filter(status="success").count()
        error_count = all_logs.filter(status="error").count()
        skipped_count = all_logs.filter(status="skipped").count()
        weekly_success_count = all_logs.filter(status="success", created_at__gte=week_ago).count()
        weekly_error_count = all_logs.filter(status="error", created_at__gte=week_ago).count()
        last_log = all_logs.first()

        filter_query = {
            key: value
            for key, value in {
                "q": request.GET.get("q", "").strip(),
                "status": request.GET.get("status", "").strip(),
                "event": request.GET.get("event", "").strip(),
            }.items()
            if value
        }
        telegram_updates_query = urlencode(
            {
                key: value
                for key, value in request.GET.items()
                if key != "updates_page" and value
            }
        )
        file_submissions_query = urlencode(
            {
                key: value
                for key, value in request.GET.items()
                if key != "submissions_page" and value
            }
        )

        parse_mode_value = bot_settings.parse_mode
        if not parse_mode_value and runtime_config["parse_mode"]:
            parse_mode_value = runtime_config["parse_mode"]

        return {
            "breadcrumbs": [
                {"title": _("Bosh sahifa"), "url": reverse("admin-index")},
                {"title": _("Bot"), "url": reverse("bot-control"), "active": True},
            ],
            "webhook_url": request.build_absolute_uri(reverse("telegram-webhook")),
            "bot_settings": bot_settings,
            "worker_state": worker_state,
            "bot_logs": logs_page,
            "current_path": request.get_full_path(),
            "page_query": urlencode(filter_query),
            "search_query": request.GET.get("q", "").strip(),
            "status_filter": request.GET.get("status", "").strip(),
            "event_filter": request.GET.get("event", "").strip(),
            "status_choices": BotDispatchLog._meta.get_field("status").choices,
            "event_choices": BotDispatchLog.EVENT_TYPE_CHOICES,
            "parse_mode_choices": BotSettings.PARSE_MODE_CHOICES,
            "tracked_channels": tracked_channels,
            "joined_channels": joined_channels,
            "admin_channels": admin_channels,
            "selectable_channels": selectable_channels,
            "telegram_updates": telegram_updates,
            "telegram_updates_count": BotTelegramUpdate.objects.count(),
            "telegram_updates_query": telegram_updates_query,
            "file_submissions": file_submissions,
            "file_submissions_count": BotFileSubmission.objects.count(),
            "file_submissions_query": file_submissions_query,
            "submission_search_query": submission_search_query,
            "selected_test_channel_id": selected_test_channel_id,
            "default_publish_channel_id": str(bot_settings.default_publish_channel_id or ""),
            "tracked_channels_count": len(tracked_channels),
            "joined_channels_count": len(joined_channels),
            "admin_channels_count": len(admin_channels),
            "effective_bot_name": bot_settings.bot_name or runtime_config["bot_name"],
            "effective_token": bot_settings.bot_token or DEFAULT_BOT_TOKEN,
            "effective_chat_id": bot_settings.chat_id or DEFAULT_BOT_CHAT_ID,
            "effective_parse_mode": parse_mode_value,
            "effective_masked_token": self.mask_value(bot_settings.bot_token or DEFAULT_BOT_TOKEN, prefix=6, suffix=4),
            "effective_masked_chat_id": self.mask_value(bot_settings.chat_id or DEFAULT_BOT_CHAT_ID),
            "has_token": runtime_config["has_token"],
            "has_chat_id": runtime_config["has_chat_id"],
            "using_fallback_token": runtime_config["using_fallback_token"],
            "using_fallback_chat_id": runtime_config["using_fallback_chat_id"],
            "is_configured": runtime_config["is_configured"],
            "success_count": success_count,
            "error_count": error_count,
            "skipped_count": skipped_count,
            "weekly_success_count": weekly_success_count,
            "weekly_error_count": weekly_error_count,
            "last_log": last_log,
            "last_log_status": last_log.status if last_log else "unknown",
            "last_test_message": self.get_test_message(bot_settings.bot_name or DEFAULT_BOT_NAME),
            "bot_name_default": DEFAULT_BOT_NAME,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        bot_settings = self.get_settings_object()
        action = request.POST.get("action", "").strip()

        if action == "save_settings":
            bot_settings.bot_name = request.POST.get("bot_name", "").strip() or DEFAULT_BOT_NAME
            bot_settings.bot_token = request.POST.get("bot_token", "").strip()
            bot_settings.chat_id = self.normalize_chat_identifier(request.POST.get("chat_id", ""))
            bot_settings.parse_mode = request.POST.get("parse_mode", DEFAULT_BOT_PARSE_MODE).strip()
            bot_settings.is_active = request.POST.get("is_active") == "on"
            bot_settings.notes = request.POST.get("notes", "").strip()
            default_channel_id = request.POST.get("default_publish_channel", "").strip()
            bot_settings.default_publish_channel = (
                BotChannel.objects.filter(id=default_channel_id).first()
                if default_channel_id
                else None
            )
            bot_settings.save()
            self.ensure_primary_channel(bot_settings)
            messages.success(request, _("Bot sozlamalari saqlandi."))
            return self.build_redirect_url(request)

        if action == "toggle_bot":
            bot_settings.is_active = request.POST.get("enabled") == "1"
            bot_settings.save(update_fields=["is_active", "updated_at"])
            messages.success(
                request,
                _("Bot yoqildi.") if bot_settings.is_active else _("Bot o'chirildi."),
            )
            return self.build_redirect_url(request)

        if action == "restart_bot":
            bot_settings.is_active = True
            health_payload = check_bot_health(bot_settings)
            webhook_url = request.build_absolute_uri(reverse("telegram-webhook"))
            webhook_payload = {}
            webhook_skipped = not webhook_url.startswith("https://")

            if health_payload.get("ok") and not webhook_skipped:
                webhook_payload = set_bot_webhook(webhook_url, bot_settings)

            restart_ok = health_payload.get("ok") and (webhook_skipped or webhook_payload.get("ok"))
            bot_settings.last_status = "success" if restart_ok else "error"
            bot_settings.last_error = ""
            if not health_payload.get("ok"):
                bot_settings.last_error = health_payload.get("description", "")
            elif webhook_payload and not webhook_payload.get("ok"):
                bot_settings.last_error = webhook_payload.get("description", "")
            bot_settings.last_response = {
                "health": health_payload,
                "webhook": webhook_payload,
                "webhook_skipped": webhook_skipped,
                "webhook_url": webhook_url,
            }
            bot_settings.last_tested_at = timezone.now()
            bot_settings.save(
                update_fields=[
                    "is_active",
                    "last_status",
                    "last_error",
                    "last_response",
                    "last_tested_at",
                    "updated_at",
                ]
            )

            if restart_ok and webhook_skipped:
                messages.success(
                    request,
                    _("Bot qayta ishga tushirildi. Local/HTTP serverda webhook ulanmaydi, getUpdates orqali ishlaydi."),
                )
            elif restart_ok:
                messages.success(request, _("Bot qayta ishga tushirildi va webhook qayta ulandi."))
            else:
                messages.error(
                    request,
                    _("Bot qayta ishga tushmadi: %(error)s") % {
                        "error": bot_settings.last_error or _("noma'lum xato"),
                    },
                )
            return self.build_redirect_url(request)

        if action == "start_worker":
            try:
                poll_timeout_value, sleep_value = parse_worker_period_form(request.POST)
            except ValueError:
                messages.error(request, _("Polling periodi noto'g'ri kiritildi."))
                return self.build_redirect_url(request)

            bot_settings.is_active = True
            bot_settings.save(update_fields=["is_active", "updated_at"])
            result = start_worker_process(poll_timeout=poll_timeout_value, sleep=sleep_value)
            if result.get("started"):
                messages.success(request, _("Bot worker ishga tushdi. PID: %(pid)s") % {"pid": result.get("pid")})
            else:
                messages.info(request, _("Bot worker allaqachon ishlab turibdi."))
            return self.build_redirect_url(request)

        if action == "stop_worker":
            stopped_count = stop_worker_processes()
            if stopped_count:
                messages.success(request, _("Bot worker to'xtatildi. Processlar: %(count)s") % {"count": stopped_count})
            else:
                messages.info(request, _("Ishlab turgan bot worker topilmadi."))
            return self.build_redirect_url(request)

        if action == "restart_worker":
            stopped_count = stop_worker_processes()
            try:
                poll_timeout_value, sleep_value = parse_worker_period_form(request.POST)
            except ValueError:
                messages.error(request, _("Polling periodi noto'g'ri kiritildi."))
                return self.build_redirect_url(request)

            bot_settings.is_active = True
            bot_settings.save(update_fields=["is_active", "updated_at"])
            result = start_worker_process(poll_timeout=poll_timeout_value, sleep=sleep_value)
            if result.get("started"):
                messages.success(
                    request,
                    _("Bot worker qayta ishga tushdi. To'xtatilgan: %(stopped)s, yangi PID: %(pid)s") % {
                        "stopped": stopped_count,
                        "pid": result.get("pid"),
                    },
                )
            else:
                messages.warning(request, _("Bot worker qayta ishga tushmadi, mavjud process ishlamoqda."))
            return self.build_redirect_url(request)

        if action == "check_status":
            response_payload = check_bot_health(bot_settings)
            bot_settings.last_status = "success" if response_payload.get("ok") else "error"
            bot_settings.last_error = "" if response_payload.get("ok") else response_payload.get("description", "")
            bot_settings.last_response = response_payload
            bot_settings.last_tested_at = timezone.now()
            bot_settings.save(update_fields=["last_status", "last_error", "last_response", "last_tested_at", "updated_at"])
            if response_payload.get("ok"):
                bot_user = response_payload.get("result") or {}
                messages.success(request, _("Bot ishlayapti: @%(username)s") % {"username": bot_user.get("username", "-")})
            else:
                messages.error(request, _("Bot holatini tekshirib bo'lmadi: %(error)s") % {"error": bot_settings.last_error or _("noma'lum xato")})
            return self.build_redirect_url(request)

        if action == "set_webhook":
            webhook_url = request.build_absolute_uri(reverse("telegram-webhook"))
            response_payload = set_bot_webhook(webhook_url, bot_settings)
            if response_payload.get("ok"):
                messages.success(request, _("Webhook ulandi. Endi botga kelgan xabarlar tizimga tushadi."))
            else:
                messages.error(
                    request,
                    _("Webhook ulanmagan: %(error)s") % {
                        "error": response_payload.get("description") or _("noma'lum xato"),
                    },
                )
            return self.build_redirect_url(request)

        if action == "delete_webhook":
            response_payload = delete_bot_webhook(bot_settings)
            if response_payload.get("ok"):
                messages.success(request, _("Webhook o'chirildi."))
            else:
                messages.error(
                    request,
                    _("Webhook o'chirilmadi: %(error)s") % {
                        "error": response_payload.get("description") or _("noma'lum xato"),
                    },
                )
            return self.build_redirect_url(request)

        if action == "send_test":
            target_channel_id = request.POST.get("target_channel_id", "").strip()
            if not target_channel_id:
                messages.error(request, _("Sinov yuborish uchun avval kanal tanlang."))
                return self.build_redirect_url(request)

            target_channel = get_object_or_404(BotChannel, id=target_channel_id)
            test_message = request.POST.get("test_message", "").strip()
            if not test_message:
                test_message = self.get_test_message(bot_settings.bot_name or DEFAULT_BOT_NAME)

            response_payload = send_message(
                test_message,
                event_type="test",
                allow_inactive=True,
                target_chat_id=target_channel.chat_id,
            )
            if response_payload.get("ok"):
                messages.success(request, _("Sinov xabari %(channel)s kanaliga yuborildi.") % {"channel": target_channel.display_name})
            else:
                messages.error(
                    request,
                    _("Sinov xabari yuborilmadi: %(error)s") % {
                        "error": response_payload.get("description") or response_payload.get("error") or _("noma'lum xato"),
                    },
                )
            return self.build_redirect_url(request)

        if action == "fetch_updates":
            response_payload = fetch_bot_updates(bot_settings, limit=50)
            if not response_payload.get("ok"):
                messages.error(
                    request,
                    _("Telegram update'larni olib bo'lmadi: %(error)s") % {
                        "error": response_payload.get("description") or _("noma'lum xato"),
                    },
                )
                return self.build_redirect_url(request)

            updates = response_payload.get("result") or []
            (
                created_count,
                updated_count,
                channel_count,
                workflow_processed_count,
                workflow_ignored_count,
                workflow_error_count,
            ) = self.store_updates(updates, settings_obj=bot_settings, process_workflow=True)
            messages.success(
                request,
                _("Telegram update'lar olindi. Yangi: %(created)s, yangilangan: %(updated)s, yangi chatlar: %(channels)s, qayta ishlangan: %(processed)s, o'tkazilgan: %(ignored)s, xato: %(errors)s") % {
                    "created": created_count,
                    "updated": updated_count,
                    "channels": channel_count,
                    "processed": workflow_processed_count,
                    "ignored": workflow_ignored_count,
                    "errors": workflow_error_count,
                },
            )
            return self.build_redirect_url(request)

        if action == "add_channel":
            chat_id = self.normalize_chat_identifier(request.POST.get("tracked_chat_id", ""))
            label = request.POST.get("tracked_label", "").strip()
            if not chat_id:
                messages.error(request, _("Kanal username yoki ID kiriting."))
                return self.build_redirect_url(request)

            channel, created = BotChannel.objects.get_or_create(
                chat_id=chat_id,
                defaults={"label": label},
            )
            if not created:
                if label:
                    channel.label = label
                    channel.save(update_fields=["label", "updated_at"])
                messages.info(request, _("Bu kanal allaqachon kuzatuvda mavjud edi."))
            else:
                messages.success(request, _("Kanal kuzatuv ro'yxatiga qo'shildi."))

            if bot_settings.is_configured:
                inspection = self.sync_channel_state(channel, bot_settings)
                if inspection.get("ok"):
                    messages.success(request, _("Kanal holati Telegram orqali tekshirildi."))
                else:
                    messages.warning(
                        request,
                        _("Kanal qo'shildi, lekin tekshiruvda xato chiqdi: %(error)s. Username/ID ni tekshiring yoki botni avval kanalga qo'shing.") % {
                            "error": inspection.get("error") or _("noma'lum xato"),
                        },
                    )
            return self.build_redirect_url(request)

        if action == "verify_channel":
            channel_id = request.POST.get("channel_id", "").strip()
            channel = get_object_or_404(BotChannel, id=channel_id)
            inspection = self.sync_channel_state(channel, bot_settings)
            if inspection.get("ok"):
                messages.success(request, _("Kanal holati yangilandi."))
            else:
                error_text = inspection.get("error") or _("noma'lum xato")
                if "chat not found" in error_text.lower():
                    error_text = _("Kanal topilmadi. Username/ID ni tekshiring yoki botni avval kanalga qo'shing.")
                messages.error(
                    request,
                    _("Kanal holatini tekshirib bo'lmadi: %(error)s") % {
                        "error": error_text,
                    },
                )
            return self.build_redirect_url(request)

        if action == "verify_all_channels":
            channels = list(self.get_channels_queryset())
            if not channels:
                messages.info(request, _("Tekshirish uchun kanallar mavjud emas."))
                return self.build_redirect_url(request)

            success_count = 0
            error_count = 0
            for channel in channels:
                inspection = self.sync_channel_state(channel, bot_settings)
                if inspection.get("ok"):
                    success_count += 1
                else:
                    error_count += 1

            messages.success(
                request,
                _("Kanallar tekshirildi. Muvaffaqiyatli: %(success)s, xato: %(error)s") % {
                    "success": success_count,
                    "error": error_count,
                },
            )
            return self.build_redirect_url(request)

        if action == "delete_channel":
            channel_id = request.POST.get("channel_id", "").strip()
            channel = get_object_or_404(BotChannel, id=channel_id)
            channel_name = channel.display_name
            channel.delete()
            messages.success(request, _("%(name)s kuzatuv ro'yxatidan o'chirildi.") % {"name": channel_name})
            return self.build_redirect_url(request)

        messages.error(request, _("Noto'g'ri amal yuborildi."))
        return self.build_redirect_url(request)


@method_decorator(login_required, name="dispatch")
class BotWorkerStatusView(View):
    def get(self, request, *args, **kwargs):
        bot_settings = BotSettings.get_solo()
        worker_state = get_worker_state(bot_settings)
        processes = worker_state.get("processes") or []
        last_polling = worker_state.get("last_polling") or {}
        period = worker_state.get("period") or {}

        return JsonResponse(
            {
                "ok": True,
                "is_active": bot_settings.is_active,
                "last_status": bot_settings.last_status,
                "last_error": bot_settings.last_error,
                "is_running": worker_state.get("is_running", False),
                "pids": [process.get("pid") for process in processes if process.get("pid")],
                "primary_pid": worker_state.get("primary_pid") or "",
                "period": period,
                "period_label": period.get("period_label") or "Ishlamayapti",
                "last_polling": last_polling,
                "last_polling_label": last_polling.get("processed_at") or "-",
            }
        )


@method_decorator(login_required, name="dispatch")
class BotFileProxyView(View):
    @staticmethod
    def get_submission_file_id(submission):
        if submission.file_id:
            return submission.file_id

        payload = submission.raw_payload or {}
        if "channel_post" in payload or "message" in payload or "edited_channel_post" in payload:
            _update_type, payload = BotControlView.get_update_payload(payload)

        _file_type, file_id, _file_unique_id = TelegramWebhookView.extract_file_info(payload)
        return file_id

    @staticmethod
    def get_original_filename(submission, file_path=""):
        payload = submission.raw_payload or {}
        if "channel_post" in payload or "message" in payload or "edited_channel_post" in payload:
            _update_type, payload = BotControlView.get_update_payload(payload)

        path_filename = (file_path or "").rsplit("/", 1)[-1]
        path_extension = ""
        if "." in path_filename:
            path_extension = "." + path_filename.rsplit(".", 1)[1]

        document = payload.get("document") or {}
        filename = document.get("file_name") or path_filename or f"telegram-file-{submission.id}"
        if path_extension and "." not in filename:
            filename = f"{filename}{path_extension}"
        return filename

    @staticmethod
    def build_content_disposition(filename):
        filename = re.sub(r'[\r\n"]+', "_", filename or "").strip() or "telegram-file"
        ascii_filename = filename.encode("ascii", "ignore").decode("ascii").strip() or "telegram-file"
        return f"inline; filename=\"{ascii_filename}\"; filename*=UTF-8''{quote(filename, safe='')}"

    def get(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(BotFileSubmission, pk=pk)
        file_id = self.get_submission_file_id(submission)
        if not file_id:
            raise Http404("Telegram file_id topilmadi.")

        settings_obj = BotSettings.get_solo()
        runtime_config = get_bot_runtime_config(settings_obj)
        if not runtime_config["has_token"]:
            raise Http404("Bot token sozlanmagan.")

        file_payload = get_telegram_file(file_id, settings_obj=settings_obj)
        if not file_payload.get("ok"):
            raise Http404(file_payload.get("description") or "Telegram fayl topilmadi.")

        file_path = (file_payload.get("result") or {}).get("file_path")
        if not file_path:
            raise Http404("Telegram fayl yo'li topilmadi.")

        file_url = f"https://api.telegram.org/file/bot{runtime_config['token']}/{file_path}"
        try:
            telegram_response = requests.get(file_url, timeout=30)
        except requests.RequestException as exc:
            raise Http404(str(exc)) from exc

        if not telegram_response.ok:
            raise Http404("Telegram faylni yuklab bo'lmadi.")

        content_type = telegram_response.headers.get("Content-Type")
        if not content_type:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        response = HttpResponse(telegram_response.content, content_type=content_type)
        filename = self.get_original_filename(submission, file_path=file_path)
        response["Content-Disposition"] = self.build_content_disposition(filename)
        return response


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    file_fields = ("document", "photo", "video", "audio", "voice", "animation")
    search_button_text = "Qidirish"
    search_callback_prefix = "bs"
    file_type_labels = {
        "document": "Hujjat",
        "photo": "Rasm",
        "video": "Video",
        "audio": "Audio",
        "voice": "Ovozli xabar",
        "animation": "Animatsiya",
    }
    file_type_icons = {
        "document": "📄",
        "photo": "🖼️",
        "video": "🎬",
        "audio": "🎵",
        "voice": "🎤",
        "animation": "✨",
    }
    search_steps = (
        ("y", "year", "Yilni tanlang"),
        ("m", "month", "Oyni tanlang"),
        ("d", "day", "Kunni tanlang"),
        ("h", "hour", "Soatni tanlang"),
    )

    @classmethod
    def main_menu_markup(cls):
        return {
            "keyboard": [[{"text": cls.search_button_text}]],
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "is_persistent": True,
        }

    @staticmethod
    def get_message_text(message):
        return (message.get("text") or message.get("caption") or "").strip()

    @classmethod
    def is_start_message(cls, message):
        text = cls.get_message_text(message)
        command = text.split(maxsplit=1)[0].lower() if text else ""
        return command == "/start" or command.startswith("/start@")

    @classmethod
    def is_search_menu_message(cls, message):
        text = cls.get_message_text(message)
        command = text.split(maxsplit=1)[0].lower() if text else ""
        return (
            text.lower() == cls.search_button_text.lower()
            or command == "/search"
            or command.startswith("/search@")
        )

    def should_process_message(self, message):
        file_type, _file_id, _file_unique_id = self.extract_file_info(message)
        if file_type:
            return True
        text = self.get_message_text(message)
        return bool(
            self.extract_custom_id(text)
            or self.is_start_message(message)
            or self.is_search_menu_message(message)
        )

    def get_submission_datetime(self, submission):
        value = submission.published_at or submission.created_at
        if not value:
            return timezone.localtime()
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return timezone.localtime(value)

    def build_search_callback(self, custom_id, **filters):
        parts = [self.search_callback_prefix, custom_id]
        for key in ("y", "m", "d", "h", "r"):
            value = filters.get(key)
            if value not in (None, ""):
                parts.append(f"{key}:{value}")
        return "|".join(parts)

    def parse_search_callback(self, data):
        parts = (data or "").split("|")
        if len(parts) < 2 or parts[0] != self.search_callback_prefix:
            return "", {}

        filters = {}
        for item in parts[2:]:
            key, separator, value = item.partition(":")
            if separator and key in {"y", "m", "d", "h", "r"}:
                filters[key] = value
        return parts[1], filters

    @staticmethod
    def build_inline_keyboard(buttons, columns=2):
        rows = []
        for index in range(0, len(buttons), columns):
            rows.append(buttons[index:index + columns])
        return {"inline_keyboard": rows}

    @staticmethod
    def get_message_payload(update):
        for key in ("message", "edited_message"):
            if key in update:
                return update.get(key) or {}
        return {}

    @staticmethod
    def get_callback_payload(update):
        return update.get("callback_query") or {}

    @staticmethod
    def get_user_data(message):
        from_user = message.get("from") or {}
        return {
            "telegram_user_id": from_user.get("id"),
            "telegram_username": from_user.get("username", "") or "",
            "telegram_first_name": from_user.get("first_name", "") or "",
            "telegram_last_name": from_user.get("last_name", "") or "",
        }

    @staticmethod
    def get_chat_id(message):
        chat = message.get("chat") or {}
        return str(chat.get("id", "") or "")

    @staticmethod
    def parse_message_datetime(timestamp):
        if not timestamp:
            return None
        return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())

    @staticmethod
    def extract_custom_id(text):
        match = CUSTOM_ID_PATTERN.search(text or "")
        return match.group(0) if match else ""

    @staticmethod
    def unwrap_message_payload(payload):
        if not isinstance(payload, dict):
            return {}
        for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
            if key in payload and isinstance(payload.get(key), dict):
                return payload.get(key) or {}
        return payload

    @classmethod
    def extract_file_object(cls, message):
        payload = cls.unwrap_message_payload(message)
        if payload.get("document"):
            return "document", payload["document"]
        if payload.get("photo"):
            return "photo", (payload.get("photo") or [])[-1]
        if payload.get("video"):
            return "video", payload["video"]
        if payload.get("audio"):
            return "audio", payload["audio"]
        if payload.get("voice"):
            return "voice", payload["voice"]
        if payload.get("animation"):
            return "animation", payload["animation"]
        return "", {}

    @classmethod
    def extract_file_info(cls, message):
        file_type, file_obj = cls.extract_file_object(message)
        if file_obj:
            return file_type, file_obj.get("file_id", ""), file_obj.get("file_unique_id", "")
        return "", "", ""

    @staticmethod
    def get_author_line(submission):
        author = submission.author_display
        if submission.telegram_user_id:
            return f"{author} | Telegram ID: {submission.telegram_user_id}"
        return author

    @staticmethod
    def format_file_size(size_bytes):
        if not size_bytes:
            return ""

        size = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                if size.is_integer():
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return ""

    def get_submission_payload(self, submission):
        return self.unwrap_message_payload(submission.raw_payload or {})

    def get_submission_file_metadata(self, submission):
        payload = self.get_submission_payload(submission)
        file_type, file_obj = self.extract_file_object(payload)
        filename = (file_obj.get("file_name") or "").strip()
        if not filename and file_type == "audio":
            filename = " - ".join(
                part for part in (file_obj.get("performer"), file_obj.get("title")) if part
            ).strip()

        mime_type = (file_obj.get("mime_type") or "").strip()
        extension = ""
        if filename and "." in filename:
            extension = filename.rsplit(".", 1)[1].upper()
        elif mime_type and "/" in mime_type:
            extension = mime_type.split("/", 1)[1].split(";")[0].replace(".", " ").replace("-", " ").upper()

        type_label = self.file_type_labels.get(file_type, "Fayl")
        if extension and extension not in type_label.upper():
            type_label = f"{type_label} ({extension})"

        size_bytes = file_obj.get("file_size") or 0
        return {
            "file_type": file_type,
            "icon": self.file_type_icons.get(file_type, "📎"),
            "type_label": type_label,
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "size_label": self.format_file_size(size_bytes),
        }

    def build_submission_detail_lines(self, submission):
        metadata = self.get_submission_file_metadata(submission)
        lines = [f"{metadata['icon']} Turi: {metadata['type_label']}"]
        if metadata["filename"]:
            lines.append(f"📝 Nomi: {metadata['filename']}")
        if metadata["size_label"]:
            lines.append(f"⚖️ Hajmi: {metadata['size_label']}")
        if metadata["mime_type"]:
            lines.append(f"🏷 Format: {metadata['mime_type']}")
        return lines

    def get_submission_source_datetime(self, submission):
        payload = self.get_submission_payload(submission)
        if payload.get("date"):
            parsed = self.parse_message_datetime(payload.get("date"))
            if parsed:
                return parsed
        return self.get_submission_datetime(submission)

    def build_caption(self, submission, target_channel):
        today = timezone.localdate().strftime("%Y-%m-%d")
        return (
            "Fayl bazaga qo'shildi\n"
            f"ID: {submission.custom_id}\n"
            f"Kanal: {target_channel.display_name}\n"
            f"Muallif: {self.get_author_line(submission)}\n"
            f"Sana: {today}"
        )
        return (
            "✅ Fayl bazaga qo‘shildi\n"
            f"📂 ID: {submission.custom_id}\n"
            f"📢 Kanal: {target_channel.display_name}\n"
            f"✍️ Muallif: {self.get_author_line(submission)}\n"
            f"🗓 Sana: {today}"
        )

    def build_publish_confirmation(self, submission):
        return (
            "Sizning fayl mazmuni ushbu kanalga yuborildi.\n"
            f"Kanal: {submission.target_channel.display_name if submission.target_channel else submission.target_chat_id}\n"
            f"ID: {submission.custom_id}\n"
            f"Message ID: {submission.target_message_id or '-'}"
        )

    def build_search_result_caption(self, submission):
        published_at = self.get_submission_datetime(submission).strftime("%Y-%m-%d %H:%M")
        channel_name = submission.target_channel.display_name if submission.target_channel else submission.target_chat_id
        return (
            "Fayl topildi\n"
            f"ID: {submission.custom_id}\n"
            f"Kanal: {channel_name or '-'}\n"
            f"Muallif: {self.get_author_line(submission)}\n"
            f"Sana: {published_at}"
        )

    def get_submission_file_metadata(self, submission):
        payload = self.get_submission_payload(submission)
        file_type, file_obj = self.extract_file_object(payload)
        filename = (file_obj.get("file_name") or "").strip()
        if not filename and file_type == "audio":
            filename = " - ".join(
                part for part in (file_obj.get("performer"), file_obj.get("title")) if part
            ).strip()

        mime_type = (file_obj.get("mime_type") or "").strip()
        extension = ""
        if filename and "." in filename:
            extension = filename.rsplit(".", 1)[1].upper()
        elif mime_type and "/" in mime_type:
            extension = mime_type.split("/", 1)[1].split(";")[0].replace(".", " ").replace("-", " ").upper()

        type_label = self.file_type_labels.get(file_type, "Fayl")
        if extension and extension not in type_label.upper():
            type_label = f"{type_label} ({extension})"

        size_bytes = file_obj.get("file_size") or 0
        return {
            "file_type": file_type,
            "type_label": type_label,
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "size_label": self.format_file_size(size_bytes),
        }

    def build_submission_detail_lines(self, submission):
        metadata = self.get_submission_file_metadata(submission)
        icon_map = {
            "document": "\U0001F4C4",
            "photo": "\U0001F5BC\ufe0f",
            "video": "\U0001F3AC",
            "audio": "\U0001F3B5",
            "voice": "\U0001F3A4",
            "animation": "\u2728",
        }
        icon = icon_map.get(metadata["file_type"]) or chr(0x1F4CE)
        lines = [f"{icon} Turi: {metadata['type_label']}"]
        if metadata["filename"]:
            lines.append(f"\U0001F4DD Nomi: {metadata['filename']}")
        if metadata["size_label"]:
            lines.append(f"\u2696\ufe0f Hajmi: {metadata['size_label']}")
        if metadata["mime_type"]:
            lines.append(f"\U0001F3F7 Format: {metadata['mime_type']}")
        return lines

    def build_caption(self, submission, target_channel):
        created_at = self.get_submission_source_datetime(submission).strftime("%Y-%m-%d %H:%M")
        return "\n".join(
            [
                "\u2705 Fayl bazaga qo'shildi",
                f"\U0001F194 ID: {submission.custom_id}",
                f"\U0001F4E2 Kanal: {target_channel.display_name}",
                f"\U0001F464 Muallif: {self.get_author_line(submission)}",
                *self.build_submission_detail_lines(submission),
                f"\U0001F5D3 Sana: {created_at}",
            ]
        )

    def build_publish_confirmation(self, submission):
        channel_name = submission.target_channel.display_name if submission.target_channel else submission.target_chat_id
        return "\n".join(
            [
                "\u2705 Siz yuborgan fayl kanalga yuborildi.",
                f"\U0001F4E2 Kanal: {channel_name}",
                f"\U0001F194 ID: {submission.custom_id}",
                *self.build_submission_detail_lines(submission),
                f"\U0001F4E8 Kanal xabari ID: {submission.target_message_id or '-'}",
            ]
        )

    def build_search_result_caption(self, submission):
        published_at = self.get_submission_datetime(submission).strftime("%Y-%m-%d %H:%M")
        channel_name = submission.target_channel.display_name if submission.target_channel else submission.target_chat_id
        return "\n".join(
            [
                "\U0001F50E Fayl topildi",
                f"\U0001F194 ID: {submission.custom_id}",
                f"\U0001F4E2 Kanal: {channel_name or '-'}",
                f"\U0001F464 Muallif: {self.get_author_line(submission)}",
                *self.build_submission_detail_lines(submission),
                f"\U0001F5D3 Sana: {published_at}",
                f"\U0001F4E8 Kanal xabari ID: {submission.target_message_id or '-'}",
            ]
        )

    @staticmethod
    def reply(chat_id, text, settings_obj, reply_markup=None):
        if not chat_id:
            return {"ok": False, "description": "chat_id topilmadi"}
        return send_chat_message(
            chat_id,
            text,
            settings_obj=settings_obj,
            parse_mode="",
            reply_markup=reply_markup,
        )

    def deliver_submission(self, chat_id, submission, settings_obj):
        caption = self.build_search_result_caption(submission)
        if submission.target_chat_id and submission.target_message_id:
            response_payload = copy_message_to_chat(
                chat_id,
                submission.target_chat_id,
                submission.target_message_id,
                settings_obj=settings_obj,
                caption=caption,
                parse_mode="",
            )
            if response_payload.get("ok"):
                return {"ok": True, "status": "found"}
            error_text = response_payload.get("description") or "faylni yuborib bo'lmadi"
            self.reply(chat_id, f"Fayl topildi, lekin yuborib bo'lmadi: {error_text}", settings_obj)
            return {"ok": False, "status": "error", "description": error_text}

        self.reply(chat_id, caption, settings_obj)
        return {"ok": True, "status": "found"}

    def prompt_search_results(self, chat_id, custom_id, submissions, settings_obj, filters=None):
        filters = filters or {}
        filtered = self.filter_search_submissions(submissions, filters)
        if not filtered:
            self.reply(chat_id, f"ID {custom_id} bo'yicha tanlangan vaqt oralig'ida yozuv topilmadi.", settings_obj)
            return {"ok": True, "status": "not_found"}

        if filters.get("r"):
            selected = next((item for item in filtered if str(item.id) == str(filters["r"])), None)
            if selected:
                return self.deliver_submission(chat_id, selected, settings_obj)

        if len(filtered) == 1:
            return self.deliver_submission(chat_id, filtered[0], settings_obj)

        for callback_key, datetime_attr, prompt in self.search_steps:
            if filters.get(callback_key):
                continue

            grouped_values = sorted(
                {getattr(self.get_submission_datetime(item), datetime_attr) for item in filtered},
                reverse=True,
            )
            if len(grouped_values) == 1:
                filters = {**filters, callback_key: str(grouped_values[0])}
                filtered = self.filter_search_submissions(submissions, filters)
                if len(filtered) == 1:
                    return self.deliver_submission(chat_id, filtered[0], settings_obj)
                continue

            buttons = []
            for value in grouped_values:
                next_filters = {**filters, callback_key: str(value)}
                labels = {
                    "y": str(value),
                    "m": f"{value:02d}",
                    "d": f"{value:02d}",
                    "h": f"{value:02d}:00",
                }
                buttons.append(
                    {
                        "text": labels[callback_key],
                        "callback_data": self.build_search_callback(custom_id, **next_filters),
                    }
                )
            self.reply(
                chat_id,
                f"ID {custom_id} bo'yicha {len(filtered)} ta yozuv topildi. {prompt}:",
                settings_obj,
                reply_markup=self.build_inline_keyboard(buttons),
            )
            return {"ok": True, "status": f"choose_{datetime_attr}"}

        buttons = []
        for item in filtered[:30]:
            value = self.get_submission_datetime(item)
            buttons.append(
                {
                    "text": f"{value.strftime('%Y-%m-%d %H:%M')} - {(item.target_channel.display_name if item.target_channel else item.target_chat_id or '-')}",
                    "callback_data": self.build_search_callback(custom_id, r=item.id),
                }
            )
        self.reply(
            chat_id,
            f"ID {custom_id} bo'yicha bir soatda bir nechta yozuv bor. Kerakli vaqtni tanlang:",
            settings_obj,
            reply_markup=self.build_inline_keyboard(buttons, columns=1),
        )
        return {"ok": True, "status": "choose_record"}

    def get_default_channel(self, settings_obj):
        if settings_obj.default_publish_channel:
            return settings_obj.default_publish_channel
        chat_id = BotControlView.normalize_chat_identifier(settings_obj.chat_id)
        if not chat_id:
            return None
        channel, _created = BotChannel.objects.get_or_create(
            chat_id=chat_id,
            defaults={"label": "Asosiy yuborish kanali"},
        )
        return channel

    def update_matches_custom_id(self, update_record, custom_id):
        text = (update_record.text or "").strip()
        if not text:
            return False
        return custom_id in CUSTOM_ID_PATTERN.findall(text)

    def submission_has_file_reference(self, submission):
        if submission.file_id or submission.file_type:
            return True
        if submission.publish_method in {"forward", "copy"} and submission.target_message_id:
            return True

        payload = submission.raw_payload or {}
        if "channel_post" in payload or "message" in payload or "edited_channel_post" in payload:
            _update_type, payload = BotControlView.get_update_payload(payload)
        file_type, file_id, _file_unique_id = self.extract_file_info(payload)
        return bool(file_type or file_id)

    def find_channel_submissions(self, custom_id, settings_obj):
        target_channel = self.get_default_channel(settings_obj)
        if not target_channel:
            return []

        updates = BotTelegramUpdate.objects.filter(
            update_type__in=["channel_post", "edited_channel_post"],
            chat_id=target_channel.chat_id,
            message_id__isnull=False,
            text__icontains=custom_id,
        ).order_by("-message_date", "-update_id")[:50]

        submissions = []
        for update_record in updates:
            if not self.update_matches_custom_id(update_record, custom_id):
                continue

            existing = BotFileSubmission.objects.filter(
                custom_id=custom_id,
                target_chat_id=update_record.chat_id,
                target_message_id=update_record.message_id,
                status="published",
            ).first()
            if existing:
                if self.submission_has_file_reference(existing):
                    submissions.append(existing)
                continue

            _update_type, payload = BotControlView.get_update_payload(update_record.raw_payload)
            file_type, file_id, file_unique_id = self.extract_file_info(payload)
            if not file_type and not file_id:
                continue
            submissions.append(
                BotFileSubmission.objects.create(
                    custom_id=custom_id,
                    status="published",
                    target_channel=target_channel,
                    target_chat_id=update_record.chat_id,
                    target_message_id=update_record.message_id,
                    file_type=file_type,
                    file_id=file_id,
                    file_unique_id=file_unique_id,
                    original_text=update_record.text,
                    generated_caption=update_record.text or f"ID: {custom_id}",
                    raw_payload=payload,
                    publish_method="channel_search",
                    published_at=update_record.message_date or timezone.now(),
                )
            )
        return submissions

    def sync_channel_from_update(self, update_record):
        if not update_record.chat_id:
            return None

        channel, _created = BotChannel.objects.get_or_create(
            chat_id=update_record.chat_id,
            defaults={
                "label": update_record.chat_title or update_record.chat_username or update_record.chat_id,
                "chat_title": update_record.chat_title or "",
                "chat_username": update_record.chat_username or "",
                "chat_type": update_record.chat_type or "channel",
            },
        )
        update_fields = ["updated_at"]
        if update_record.chat_title and channel.chat_title != update_record.chat_title:
            channel.chat_title = update_record.chat_title
            update_fields.append("chat_title")
        if update_record.chat_username and channel.chat_username != update_record.chat_username:
            channel.chat_username = update_record.chat_username
            update_fields.append("chat_username")
        if update_record.chat_type and channel.chat_type != update_record.chat_type:
            channel.chat_type = update_record.chat_type
            update_fields.append("chat_type")
        if not channel.label:
            channel.label = update_record.chat_title or update_record.chat_username or update_record.chat_id
            update_fields.append("label")
        if len(update_fields) > 1:
            channel.save(update_fields=list(dict.fromkeys(update_fields)))
        return channel

    def find_channel_submissions(self, custom_id, settings_obj):
        updates = BotTelegramUpdate.objects.filter(
            update_type__in=["channel_post", "edited_channel_post"],
            message_id__isnull=False,
            text__icontains=custom_id,
        ).order_by("-message_date", "-update_id")[:100]

        submissions = []
        for update_record in updates:
            if not self.update_matches_custom_id(update_record, custom_id):
                continue

            target_channel = self.sync_channel_from_update(update_record)
            if not target_channel:
                continue

            existing = BotFileSubmission.objects.filter(
                custom_id=custom_id,
                target_chat_id=update_record.chat_id,
                target_message_id=update_record.message_id,
                status="published",
            ).first()
            if existing:
                if not existing.target_channel_id:
                    existing.target_channel = target_channel
                    existing.save(update_fields=["target_channel", "updated_at"])
                if self.submission_has_file_reference(existing):
                    submissions.append(existing)
                continue

            payload = self.unwrap_message_payload(update_record.raw_payload)
            file_type, file_id, file_unique_id = self.extract_file_info(payload)
            if not file_type and not file_id:
                continue

            submissions.append(
                BotFileSubmission.objects.create(
                    custom_id=custom_id,
                    status="published",
                    target_channel=target_channel,
                    target_chat_id=update_record.chat_id,
                    target_message_id=update_record.message_id,
                    file_type=file_type,
                    file_id=file_id,
                    file_unique_id=file_unique_id,
                    original_text=update_record.text,
                    generated_caption=update_record.text or f"ID: {custom_id}",
                    raw_payload=payload,
                    publish_method="channel_search",
                    published_at=update_record.message_date or timezone.now(),
                )
            )
        return submissions

    def get_search_submissions(self, custom_id, settings_obj):
        submissions = list(
            BotFileSubmission.objects.select_related("target_channel")
            .filter(custom_id=custom_id, status="published", target_message_id__isnull=False)
            .order_by("-published_at", "-created_at", "-id")
        )
        submissions = [item for item in submissions if self.submission_has_file_reference(item)]
        if submissions:
            return submissions
        return self.find_channel_submissions(custom_id, settings_obj)

    def filter_search_submissions(self, submissions, filters):
        result = []
        for submission in submissions:
            value = self.get_submission_datetime(submission)
            if filters.get("y") and value.year != int(filters["y"]):
                continue
            if filters.get("m") and value.month != int(filters["m"]):
                continue
            if filters.get("d") and value.day != int(filters["d"]):
                continue
            if filters.get("h") and value.hour != int(filters["h"]):
                continue
            result.append(submission)
        return result

    def create_pending_submission(self, message, custom_id=""):
        file_type, file_id, file_unique_id = self.extract_file_info(message)
        user_data = self.get_user_data(message)
        text = message.get("caption") or message.get("text") or ""
        source_chat_id = self.get_chat_id(message)
        source_message_id = message.get("message_id")

        existing = BotFileSubmission.objects.filter(
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
        ).order_by("-created_at").first()
        if existing:
            update_fields = ["updated_at"]
            for field, value in user_data.items():
                if value and getattr(existing, field) != value:
                    setattr(existing, field, value)
                    update_fields.append(field)
            for field, value in {
                "file_type": file_type,
                "file_id": file_id,
                "file_unique_id": file_unique_id,
                "original_text": text,
                "raw_payload": message,
            }.items():
                if value and getattr(existing, field) != value:
                    setattr(existing, field, value)
                    update_fields.append(field)
            if custom_id and existing.custom_id != custom_id:
                existing.custom_id = custom_id
                update_fields.append("custom_id")
            existing.save(update_fields=list(dict.fromkeys(update_fields)))
            return existing

        return BotFileSubmission.objects.create(
            custom_id=custom_id,
            status="awaiting_id" if not custom_id else "error",
            **user_data,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            file_type=file_type,
            file_id=file_id,
            file_unique_id=file_unique_id,
            original_text=text,
            raw_payload=message,
        )

    def publish_submission(self, submission, settings_obj):
        if not settings_obj.is_active:
            submission.status = "error"
            submission.error_text = "Bot o'chirilgan."
            submission.save(update_fields=["status", "error_text", "updated_at"])
            return {"ok": False, "description": submission.error_text}

        target_channel = self.get_default_channel(settings_obj)
        if not target_channel:
            submission.status = "error"
            submission.error_text = "Yuborish uchun asosiy kanal tanlanmagan."
            submission.save(update_fields=["status", "error_text", "updated_at"])
            return {"ok": False, "description": submission.error_text}

        caption = self.build_caption(submission, target_channel)
        response_payload = copy_message_to_chat(
            target_channel.chat_id,
            submission.source_chat_id,
            submission.source_message_id,
            settings_obj=settings_obj,
            caption=caption,
            parse_mode="",
        )
        publish_method = "copy"
        if not response_payload.get("ok"):
            response_payload = forward_message_to_chat(
                target_channel.chat_id,
                submission.source_chat_id,
                submission.source_message_id,
                settings_obj=settings_obj,
            )
            publish_method = "forward"
        if response_payload.get("ok"):
            result = response_payload.get("result") or {}
            submission.status = "published"
            submission.target_channel = target_channel
            submission.target_chat_id = target_channel.chat_id
            submission.target_message_id = result.get("message_id")
            submission.target_meta_message_id = None
            submission.publish_method = publish_method
            submission.generated_caption = caption
            submission.error_text = ""
            submission.published_at = timezone.now()
            submission.save(
                update_fields=[
                    "status",
                    "target_channel",
                    "target_chat_id",
                    "target_message_id",
                    "target_meta_message_id",
                    "publish_method",
                    "generated_caption",
                    "error_text",
                    "published_at",
                    "updated_at",
                ]
            )
            response_payload["status"] = "published"
            response_payload["publish_method"] = publish_method
        else:
            submission.status = "error"
            submission.error_text = response_payload.get("description", "Telegramga yuborishda xato")
            submission.generated_caption = caption
            submission.save(update_fields=["status", "error_text", "generated_caption", "updated_at"])
            response_payload["status"] = "error"
        return response_payload

    def handle_start_message(self, message, settings_obj):
        chat_id = self.get_chat_id(message)
        start_message = (
            "Assalomu alaykum!\n"
            "Fayl qo'shish uchun faylni botga yuboring, keyin ID raqamini yozing.\n"
            "Qidirish uchun Qidirish tugmasini bosing va ID raqamini yuboring."
        )
        self.reply(chat_id, start_message, settings_obj, reply_markup=self.main_menu_markup())
        return {"ok": True, "status": "start"}

    def handle_search_menu_message(self, message, settings_obj):
        chat_id = self.get_chat_id(message)
        self.reply(
            chat_id,
            "Qidirish uchun ID raqamini yuboring.",
            settings_obj,
            reply_markup=self.main_menu_markup(),
        )
        return {"ok": True, "status": "search_prompt"}

    def handle_message(self, message, settings_obj):
        if self.is_start_message(message):
            return self.handle_start_message(message, settings_obj)
        if self.is_search_menu_message(message):
            return self.handle_search_menu_message(message, settings_obj)

        file_type, _file_id, _file_unique_id = self.extract_file_info(message)
        if file_type:
            return self.handle_file_message(message, settings_obj)
        return self.handle_id_message(message, settings_obj)

    def handle_callback_query(self, callback_query, settings_obj):
        callback_query_id = callback_query.get("id")
        if callback_query_id:
            answer_callback_query(callback_query_id, settings_obj=settings_obj)

        custom_id, filters = self.parse_search_callback(callback_query.get("data") or "")
        message = callback_query.get("message") or {}
        chat_id = self.get_chat_id(message)
        if not custom_id or not chat_id:
            return {"ok": True, "status": "ignored"}

        submissions = self.get_search_submissions(custom_id, settings_obj)
        if not submissions:
            self.reply(chat_id, f"ID {custom_id} bo'yicha yozuv topilmadi.", settings_obj)
            return {"ok": True, "status": "not_found"}

        return self.prompt_search_results(chat_id, custom_id, submissions, settings_obj, filters=filters)

    def handle_file_message(self, message, settings_obj):
        chat_id = self.get_chat_id(message)
        text = message.get("caption") or ""
        custom_id = self.extract_custom_id(text)
        submission = self.create_pending_submission(message, custom_id=custom_id)

        if submission.status == "published":
            self.reply(chat_id, self.build_publish_confirmation(submission), settings_obj)
            return {"ok": True, "status": "already_published"}

        if not custom_id:
            self.reply(chat_id, "Fayl qabul qilindi. Endi shu fayl uchun ID raqamini yuboring.", settings_obj)
            return {"ok": True, "status": "awaiting_id"}

        submission.status = "awaiting_id"
        submission.save(update_fields=["status", "updated_at"])
        response_payload = self.publish_submission(submission, settings_obj)
        if response_payload.get("ok"):
            self.reply(chat_id, self.build_publish_confirmation(submission), settings_obj)
        else:
            error_text = response_payload.get("description") or "noma'lum xato"
            self.reply(chat_id, f"Fayl yuborilmadi: {error_text}", settings_obj)
        return response_payload

    def handle_id_message(self, message, settings_obj):
        chat_id = self.get_chat_id(message)
        user_data = self.get_user_data(message)
        custom_id = self.extract_custom_id(message.get("text") or "")
        if not custom_id:
            self.reply(chat_id, "ID raqamini yuboring yoki avval fayl tashlang.", settings_obj)
            return {"ok": True, "status": "ignored"}

        pending = BotFileSubmission.objects.filter(
            telegram_user_id=user_data["telegram_user_id"],
            status="awaiting_id",
        ).order_by("-created_at").first()
        if pending:
            pending.custom_id = custom_id
            pending.save(update_fields=["custom_id", "updated_at"])
            response_payload = self.publish_submission(pending, settings_obj)
            if response_payload.get("ok"):
                self.reply(chat_id, self.build_publish_confirmation(pending), settings_obj)
            else:
                error_text = response_payload.get("description") or "noma'lum xato"
                self.reply(chat_id, f"Fayl yuborilmadi: {error_text}", settings_obj)
            return response_payload

        submissions = self.get_search_submissions(custom_id, settings_obj)
        if not submissions:
            self.reply(chat_id, f"ID {custom_id} bo'yicha yozuv topilmadi.", settings_obj)
            return {"ok": True, "status": "not_found"}

        return self.prompt_search_results(chat_id, custom_id, submissions, settings_obj)

    def post(self, request, *args, **kwargs):
        try:
            update = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

        settings_obj = BotSettings.get_solo()
        callback_query = self.get_callback_payload(update)
        if callback_query:
            result = self.handle_callback_query(callback_query, settings_obj)
            return JsonResponse({"ok": True, "result": result})

        message = self.get_message_payload(update)
        if not message:
            return JsonResponse({"ok": True, "status": "ignored"})

        result = self.handle_message(message, settings_obj)

        return JsonResponse({"ok": True, "result": result})
