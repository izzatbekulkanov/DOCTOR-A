import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.bot.models import BotSettings
from apps.bot.views import BotControlView
from config.telegram_bot import delete_bot_webhook, fetch_bot_updates


class Command(BaseCommand):
    help = "Run Telegram bot in long-polling mode for local/non-webhook environments."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Fetch and process updates once, then exit.")
        parser.add_argument("--keep-webhook", action="store_true", help="Do not delete Telegram webhook before polling.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum updates per request.")
        parser.add_argument("--offset", type=int, default=None, help="Telegram update offset.")
        parser.add_argument("--poll-timeout", type=int, default=10, help="Telegram long-polling timeout in seconds.")
        parser.add_argument("--sleep", type=float, default=1.0, help="Delay between polling requests.")

    def handle(self, *args, **options):
        settings_obj = BotSettings.get_solo()
        if not settings_obj.bot_token:
            raise CommandError("Bot token sozlanmagan.")

        if not options["keep_webhook"]:
            webhook_response = delete_bot_webhook(settings_obj)
            if webhook_response.get("ok"):
                self.stdout.write(self.style.SUCCESS("Webhook o'chirildi, polling rejimi ishga tushadi."))
            else:
                error_text = webhook_response.get("description") or "noma'lum xato"
                self.stdout.write(
                    self.style.WARNING(
                        f"Webhook o'chirishda xato: {error_text}"
                    )
                )

        processor = BotControlView()
        offset = options["offset"]
        self.stdout.write(self.style.SUCCESS("Telegram bot long-polling rejimida ishga tushdi."))

        while True:
            settings_obj.refresh_from_db()
            if not settings_obj.is_active:
                self.stdout.write("Bot o'chirilgan. Kutish rejimi...")
                if options["once"]:
                    break
                time.sleep(options["sleep"])
                continue

            response_payload = fetch_bot_updates(
                settings_obj,
                limit=options["limit"],
                offset=offset,
                timeout=options["poll_timeout"],
            )
            if not response_payload.get("ok"):
                error_text = response_payload.get("description") or "noma'lum xato"
                self.stdout.write(
                    self.style.ERROR(
                        f"Update olishda xato: {error_text}"
                    )
                )
                if options["once"]:
                    break
                time.sleep(options["sleep"])
                continue

            updates = response_payload.get("result") or []
            counts = (0, 0, 0, 0, 0, 0)
            if updates:
                counts = processor.store_updates(updates, settings_obj=settings_obj, process_workflow=True)
                update_ids = [update.get("update_id") for update in updates if update.get("update_id") is not None]
                if update_ids:
                    offset = max(update_ids) + 1

                self.stdout.write(
                    "Update'lar: "
                    f"yangi={counts[0]}, yangilangan={counts[1]}, "
                    f"qayta ishlangan={counts[3]}, o'tkazilgan={counts[4]}, xato={counts[5]}"
                )

            settings_obj.last_status = "success"
            settings_obj.last_error = ""
            settings_obj.last_response = {
                "polling": True,
                "processed_at": timezone.now().isoformat(),
                "poll_timeout": options["poll_timeout"],
                "sleep": options["sleep"],
                "counts": {
                    "created": counts[0],
                    "updated": counts[1],
                    "channels": counts[2],
                    "processed": counts[3],
                    "ignored": counts[4],
                    "errors": counts[5],
                },
                "next_offset": offset,
            }
            settings_obj.last_tested_at = timezone.now()
            settings_obj.save(
                update_fields=[
                    "last_status",
                    "last_error",
                    "last_response",
                    "last_tested_at",
                    "updated_at",
                ]
            )

            if options["once"]:
                break

            time.sleep(options["sleep"])
