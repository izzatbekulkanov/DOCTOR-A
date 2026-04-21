import json
import re

import requests
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone
from django.utils.html import strip_tags


DEFAULT_BOT_NAME = "Doctor A Bot"
DEFAULT_BOT_TOKEN = ""
DEFAULT_BOT_CHAT_ID = ""
DEFAULT_BOT_PARSE_MODE = "HTML"
TELEGRAM_TIMEOUT_SECONDS = 15


def _safe_get_bot_settings():
    try:
        from apps.bot.models import BotSettings

        return BotSettings.get_solo()
    except (OperationalError, ProgrammingError):
        return None


def _safe_create_dispatch_log(**kwargs):
    try:
        from apps.bot.models import BotDispatchLog

        return BotDispatchLog.objects.create(**kwargs)
    except (OperationalError, ProgrammingError):
        return None


def _normalize_message_preview(text):
    plain_text = strip_tags(text or "")
    compact_text = re.sub(r"\s+", " ", plain_text).strip()
    return compact_text[:500]


def _telegram_api_request(method, data=None, settings_obj=None):
    runtime_config = get_bot_runtime_config(settings_obj)
    if not runtime_config["has_token"]:
        return {
            "ok": False,
            "description": "Bot token sozlanmagan.",
        }

    url = f"https://api.telegram.org/bot{runtime_config['token']}/{method}"
    try:
        response = requests.post(url, data=data or {}, timeout=TELEGRAM_TIMEOUT_SECONDS)
        try:
            payload = response.json()
        except ValueError:
            payload = {
                "ok": response.ok,
                "description": response.text[:500],
            }
        if not response.ok and "description" not in payload:
            payload["description"] = response.text[:500]
        return payload
    except requests.RequestException as exc:
        return {
            "ok": False,
            "description": str(exc),
        }


def get_bot_runtime_config(settings_obj=None):
    settings_obj = settings_obj or _safe_get_bot_settings()
    token = (getattr(settings_obj, "bot_token", "") or DEFAULT_BOT_TOKEN).strip()
    chat_id = (getattr(settings_obj, "chat_id", "") or DEFAULT_BOT_CHAT_ID).strip()
    if settings_obj is None:
        parse_mode = DEFAULT_BOT_PARSE_MODE
    else:
        parse_mode = (getattr(settings_obj, "parse_mode", "") or "").strip()
    bot_name = (getattr(settings_obj, "bot_name", "") or DEFAULT_BOT_NAME).strip()
    is_active = getattr(settings_obj, "is_active", True)

    return {
        "settings": settings_obj,
        "bot_name": bot_name,
        "token": token,
        "chat_id": chat_id,
        "parse_mode": parse_mode,
        "is_active": is_active,
        "has_token": bool(token),
        "has_chat_id": bool(chat_id),
        "is_configured": bool(token and chat_id),
        "using_fallback_token": bool(not getattr(settings_obj, "bot_token", "")),
        "using_fallback_chat_id": bool(not getattr(settings_obj, "chat_id", "")),
    }


def _update_settings_status(settings_obj, *, status, payload=None, error_text="", update_tested_at=False):
    if not settings_obj:
        return

    settings_obj.last_status = status
    settings_obj.last_error = error_text
    settings_obj.last_response = payload or {}
    if update_tested_at:
        settings_obj.last_tested_at = timezone.now()
    settings_obj.save(update_fields=["last_status", "last_error", "last_response", "last_tested_at", "updated_at"])


def inspect_bot_chat(chat_id, settings_obj=None):
    runtime_config = get_bot_runtime_config(settings_obj)
    if not runtime_config["has_token"]:
        return {
            "ok": False,
            "chat_id": chat_id,
            "title": "",
            "username": "",
            "type": "",
            "member_status": "unknown",
            "is_bot_admin": False,
            "error": "Bot token sozlanmagan.",
            "payload": {},
        }

    me_payload = _telegram_api_request("getMe", settings_obj=settings_obj)
    if not me_payload.get("ok"):
        return {
            "ok": False,
            "chat_id": chat_id,
            "title": "",
            "username": "",
            "type": "",
            "member_status": "error",
            "is_bot_admin": False,
            "error": me_payload.get("description", "getMe xatoligi"),
            "payload": {"me": me_payload},
        }

    chat_payload = _telegram_api_request("getChat", data={"chat_id": chat_id}, settings_obj=settings_obj)
    if not chat_payload.get("ok"):
        return {
            "ok": False,
            "chat_id": chat_id,
            "title": "",
            "username": "",
            "type": "",
            "member_status": "not_found",
            "is_bot_admin": False,
            "error": chat_payload.get("description", "Kanal topilmadi"),
            "payload": {"me": me_payload, "chat": chat_payload},
        }

    bot_user_id = (me_payload.get("result") or {}).get("id")
    member_payload = _telegram_api_request(
        "getChatMember",
        data={"chat_id": chat_id, "user_id": bot_user_id},
        settings_obj=settings_obj,
    )

    chat_result = chat_payload.get("result") or {}
    if not member_payload.get("ok"):
        return {
            "ok": False,
            "chat_id": chat_id,
            "title": chat_result.get("title", ""),
            "username": chat_result.get("username", ""),
            "type": chat_result.get("type", ""),
            "member_status": "error",
            "is_bot_admin": False,
            "error": member_payload.get("description", "A'zolik tekshiruvida xato"),
            "payload": {"me": me_payload, "chat": chat_payload, "member": member_payload},
        }

    member_result = member_payload.get("result") or {}
    member_status = member_result.get("status") or "unknown"
    is_bot_admin = member_status in {"administrator", "creator"}

    return {
        "ok": True,
        "chat_id": chat_id,
        "title": chat_result.get("title", ""),
        "username": chat_result.get("username", ""),
        "type": chat_result.get("type", ""),
        "member_status": member_status,
        "is_bot_admin": is_bot_admin,
        "error": "",
        "payload": {"me": me_payload, "chat": chat_payload, "member": member_payload},
    }


def fetch_bot_updates(settings_obj=None, *, limit=50, offset=None, timeout=None):
    request_data = {"limit": limit}
    if offset is not None:
        request_data["offset"] = offset
    if timeout is not None:
        request_data["timeout"] = timeout
    return _telegram_api_request("getUpdates", data=request_data, settings_obj=settings_obj)


def get_telegram_file(file_id, settings_obj=None):
    return _telegram_api_request("getFile", data={"file_id": file_id}, settings_obj=settings_obj)


def check_bot_health(settings_obj=None):
    return _telegram_api_request("getMe", settings_obj=settings_obj)


def set_bot_webhook(webhook_url, settings_obj=None):
    return _telegram_api_request("setWebhook", data={"url": webhook_url}, settings_obj=settings_obj)


def delete_bot_webhook(settings_obj=None):
    return _telegram_api_request("deleteWebhook", settings_obj=settings_obj)


def answer_callback_query(callback_query_id, text="", settings_obj=None):
    request_data = {"callback_query_id": callback_query_id}
    if text:
        request_data["text"] = text
    return _telegram_api_request("answerCallbackQuery", data=request_data, settings_obj=settings_obj)


def send_chat_message(
    chat_id,
    text,
    settings_obj=None,
    parse_mode="HTML",
    reply_markup=None,
    reply_to_message_id=None,
):
    request_data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        request_data["parse_mode"] = parse_mode
    if reply_markup:
        request_data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    if reply_to_message_id:
        request_data["reply_to_message_id"] = reply_to_message_id
    return _telegram_api_request("sendMessage", data=request_data, settings_obj=settings_obj)


def forward_message_to_chat(target_chat_id, from_chat_id, message_id, settings_obj=None):
    request_data = {
        "chat_id": target_chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    return _telegram_api_request("forwardMessage", data=request_data, settings_obj=settings_obj)


def copy_message_to_chat(target_chat_id, from_chat_id, message_id, settings_obj=None, caption="", parse_mode="HTML"):
    request_data = {
        "chat_id": target_chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    if caption:
        request_data["caption"] = caption
    if parse_mode:
        request_data["parse_mode"] = parse_mode
    return _telegram_api_request("copyMessage", data=request_data, settings_obj=settings_obj)


def send_message(text, event_type="notification", allow_inactive=False, target_chat_id=None):
    runtime_config = get_bot_runtime_config()
    settings_obj = runtime_config["settings"]
    resolved_chat_id = (target_chat_id or runtime_config["chat_id"]).strip()
    payload = {
        "ok": False,
        "description": "",
    }

    if not runtime_config["has_token"] or not resolved_chat_id:
        payload["description"] = "Bot token yoki chat ID sozlanmagan."
        _safe_create_dispatch_log(
            settings=settings_obj,
            event_type=event_type,
            status="skipped",
            target_chat_id=resolved_chat_id,
            message_preview=_normalize_message_preview(text),
            response_payload=payload,
            error_text=payload["description"],
        )
        _update_settings_status(
            settings_obj,
            status="skipped",
            payload=payload,
            error_text=payload["description"],
            update_tested_at=event_type == "test",
        )
        return payload

    if settings_obj and not settings_obj.is_active and not allow_inactive:
        payload["description"] = "Bot o'chirilgan."
        _safe_create_dispatch_log(
            settings=settings_obj,
            event_type=event_type,
            status="skipped",
            target_chat_id=resolved_chat_id,
            message_preview=_normalize_message_preview(text),
            response_payload=payload,
            error_text=payload["description"],
        )
        _update_settings_status(
            settings_obj,
            status="skipped",
            payload=payload,
            error_text=payload["description"],
            update_tested_at=event_type == "test",
        )
        return payload

    request_data = {
        "chat_id": resolved_chat_id,
        "text": text,
    }
    if runtime_config["parse_mode"]:
        request_data["parse_mode"] = runtime_config["parse_mode"]

    url = f"https://api.telegram.org/bot{runtime_config['token']}/sendMessage"

    try:
        payload = _telegram_api_request("sendMessage", data=request_data, settings_obj=settings_obj)
        status = "success" if payload.get("ok") else "error"
        error_text = "" if status == "success" else payload.get("description", "")

        _safe_create_dispatch_log(
            settings=settings_obj,
            event_type=event_type,
            status=status,
            target_chat_id=resolved_chat_id,
            message_preview=_normalize_message_preview(text),
            response_payload=payload,
            error_text=error_text,
        )
        _update_settings_status(
            settings_obj,
            status=status,
            payload=payload,
            error_text=error_text,
            update_tested_at=event_type == "test",
        )
        return payload
    except Exception as exc:
        payload = {"ok": False, "description": str(exc)}
        _safe_create_dispatch_log(
            settings=settings_obj,
            event_type=event_type,
            status="error",
            target_chat_id=resolved_chat_id,
            message_preview=_normalize_message_preview(text),
            response_payload=payload,
            error_text=str(exc),
        )
        _update_settings_status(
            settings_obj,
            status="error",
            payload=payload,
            error_text=str(exc),
            update_tested_at=event_type == "test",
        )
        return payload
