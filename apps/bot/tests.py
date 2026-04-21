import json
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.members.models import CustomUser

from .models import BotChannel, BotDispatchLog, BotFileSubmission, BotSettings, BotTelegramUpdate


class BotControlViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="bot_admin",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_bot_control_page_renders_and_creates_singleton_settings(self):
        response = self.client.get(reverse("bot-control"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bot sozlamalari")
        self.assertTrue(BotSettings.objects.filter(pk=1).exists())

    def test_file_submissions_are_paginated(self):
        for index in range(25):
            BotFileSubmission.objects.create(custom_id=f"{20000 + index}", status="published")

        response = self.client.get(reverse("bot-control"), {"submissions_page": 2})

        self.assertEqual(response.status_code, 200)
        page = response.context["file_submissions"]
        self.assertEqual(page.number, 2)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(len(page.object_list), 5)

    def test_save_settings_updates_bot_singleton(self):
        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "save_settings",
                "bot_name": "Doctor A Notifications",
                "bot_token": "123456:ABCDEF",
                "chat_id": "@doctor_a_updates",
                "parse_mode": "HTML",
                "is_active": "on",
                "notes": "Main notification channel",
            },
        )

        self.assertEqual(response.status_code, 302)

        settings = BotSettings.get_solo()
        self.assertEqual(settings.bot_name, "Doctor A Notifications")
        self.assertEqual(settings.bot_token, "123456:ABCDEF")
        self.assertEqual(settings.chat_id, "@doctor_a_updates")
        self.assertEqual(settings.parse_mode, "HTML")
        self.assertTrue(settings.is_active)
        self.assertEqual(settings.notes, "Main notification channel")
        self.assertTrue(BotChannel.objects.filter(chat_id="@doctor_a_updates").exists())

    def test_add_channel_creates_tracked_channel(self):
        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "add_channel",
                "tracked_chat_id": "@doctor_a_news",
                "tracked_label": "News channel",
            },
        )

        self.assertEqual(response.status_code, 302)
        channel = BotChannel.objects.get(chat_id="@doctor_a_news")
        self.assertEqual(channel.label, "News channel")

    def test_add_channel_normalizes_t_me_link(self):
        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "add_channel",
                "tracked_chat_id": "https://t.me/doctor_a_news/",
                "tracked_label": "News channel",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(BotChannel.objects.filter(chat_id="@doctor_a_news").exists())

    @patch("config.telegram_bot.requests.post")
    def test_verify_channel_updates_admin_state(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "@doctor_a_updates"
        settings.parse_mode = "HTML"
        settings.is_active = True
        settings.save()

        channel = BotChannel.objects.create(chat_id="@doctor_a_updates", label="Main channel")

        me_response = Mock()
        me_response.ok = True
        me_response.json.return_value = {"ok": True, "result": {"id": 999001, "is_bot": True}}

        chat_response = Mock()
        chat_response.ok = True
        chat_response.json.return_value = {
            "ok": True,
            "result": {"title": "Doctor A Updates", "username": "doctor_a_updates", "type": "channel"},
        }

        member_response = Mock()
        member_response.ok = True
        member_response.json.return_value = {
            "ok": True,
            "result": {"status": "administrator"},
        }

        mocked_post.side_effect = [me_response, chat_response, member_response]

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "verify_channel",
                "channel_id": channel.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        channel.refresh_from_db()
        self.assertEqual(channel.chat_title, "Doctor A Updates")
        self.assertEqual(channel.chat_username, "doctor_a_updates")
        self.assertEqual(channel.chat_type, "channel")
        self.assertEqual(channel.member_status, "administrator")
        self.assertTrue(channel.is_bot_admin)
        self.assertIsNotNone(channel.last_verified_at)

    @patch("config.telegram_bot.requests.post")
    def test_send_test_message_creates_success_log(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "@doctor_a_updates"
        settings.parse_mode = "HTML"
        settings.is_active = True
        settings.save()
        channel = BotChannel.objects.create(chat_id="@doctor_a_updates", label="Main channel")

        mocked_response = Mock()
        mocked_response.ok = True
        mocked_response.text = '{"ok": true}'
        mocked_response.json.return_value = {"ok": True, "result": {"message_id": 77}}
        mocked_response.status_code = 200
        mocked_post.return_value = mocked_response

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "send_test",
                "target_channel_id": channel.id,
                "test_message": "Sinov yuborildi",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BotDispatchLog.objects.count(), 1)

        log = BotDispatchLog.objects.get()
        self.assertEqual(log.event_type, "test")
        self.assertEqual(log.status, "success")
        self.assertEqual(log.target_chat_id, "@doctor_a_updates")
        self.assertIn("Sinov yuborildi", log.message_preview)

        settings.refresh_from_db()
        self.assertEqual(settings.last_status, "success")
        self.assertTrue(settings.last_tested_at is not None)


    @patch("config.telegram_bot.requests.post")
    def test_restart_bot_reactivates_and_checks_health(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = False
        settings.save()

        health_response = Mock()
        health_response.ok = True
        health_response.json.return_value = {
            "ok": True,
            "result": {"id": 999001, "is_bot": True, "username": "doctor_a_bot"},
        }
        mocked_post.return_value = health_response

        response = self.client.post(reverse("bot-control"), {"action": "restart_bot"})

        self.assertEqual(response.status_code, 302)
        settings.refresh_from_db()
        self.assertTrue(settings.is_active)
        self.assertEqual(settings.last_status, "success")
        self.assertTrue(settings.last_response["webhook_skipped"])
        self.assertEqual(mocked_post.call_count, 1)

    @patch("config.telegram_bot.requests.post")
    def test_restart_bot_reconnects_webhook_on_https(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = False
        settings.save()

        health_response = Mock()
        health_response.ok = True
        health_response.json.return_value = {
            "ok": True,
            "result": {"id": 999001, "is_bot": True, "username": "doctor_a_bot"},
        }
        webhook_response = Mock()
        webhook_response.ok = True
        webhook_response.json.return_value = {"ok": True, "result": True}
        mocked_post.side_effect = [health_response, webhook_response]

        response = self.client.post(reverse("bot-control"), {"action": "restart_bot"}, secure=True)

        self.assertEqual(response.status_code, 302)
        settings.refresh_from_db()
        self.assertTrue(settings.is_active)
        self.assertEqual(settings.last_status, "success")
        self.assertFalse(settings.last_response["webhook_skipped"])
        self.assertEqual(mocked_post.call_count, 2)
        webhook_call_data = mocked_post.call_args_list[1].kwargs["data"]
        self.assertIn("/bot/telegram/webhook/", webhook_call_data["url"])

    @patch("apps.bot.views.start_worker_process")
    def test_start_worker_action_starts_polling_process(self, mocked_start):
        mocked_start.return_value = {"started": True, "pid": 12345}

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "start_worker",
                "poll_timeout": "12",
                "sleep": "2",
            },
        )

        self.assertEqual(response.status_code, 302)
        mocked_start.assert_called_once_with(poll_timeout=12, sleep=2.0)
        settings = BotSettings.get_solo()
        self.assertTrue(settings.is_active)

    @patch("apps.bot.views.start_worker_process")
    def test_start_worker_action_accepts_decimal_and_comma_period_values(self, mocked_start):
        mocked_start.return_value = {"started": True, "pid": 12345}

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "start_worker",
                "poll_timeout": "12.0",
                "sleep": "0,5",
            },
        )

        self.assertEqual(response.status_code, 302)
        mocked_start.assert_called_once_with(poll_timeout=12, sleep=0.5)

    @patch("apps.bot.views.start_worker_process")
    def test_start_worker_action_uses_defaults_for_blank_period_values(self, mocked_start):
        mocked_start.return_value = {"started": True, "pid": 12345}

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "start_worker",
                "poll_timeout": "",
                "sleep": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        mocked_start.assert_called_once_with(poll_timeout=10, sleep=1.0)

    @patch("apps.bot.views.start_worker_process")
    @patch("apps.bot.views.stop_worker_processes")
    def test_restart_worker_action_clamps_small_period_values(self, mocked_stop, mocked_start):
        mocked_stop.return_value = 1
        mocked_start.return_value = {"started": True, "pid": 22222}

        response = self.client.post(
            reverse("bot-control"),
            {
                "action": "restart_worker",
                "poll_timeout": "0",
                "sleep": "0.1",
            },
        )

        self.assertEqual(response.status_code, 302)
        mocked_stop.assert_called_once()
        mocked_start.assert_called_once_with(poll_timeout=1, sleep=0.2)

    @patch("apps.bot.views.stop_worker_processes")
    def test_stop_worker_action_stops_polling_process(self, mocked_stop):
        mocked_stop.return_value = 2

        response = self.client.post(reverse("bot-control"), {"action": "stop_worker"})

        self.assertEqual(response.status_code, 302)
        mocked_stop.assert_called_once()

    @patch("apps.bot.views.get_worker_state")
    def test_worker_status_endpoint_returns_processes_and_period(self, mocked_worker_state):
        settings = BotSettings.get_solo()
        settings.is_active = True
        settings.last_status = "success"
        settings.last_response = {
            "polling": True,
            "processed_at": "2026-04-22T02:15:00+05:00",
        }
        settings.save()
        mocked_worker_state.return_value = {
            "is_running": True,
            "processes": [{"pid": 28820}, {"pid": 44472}],
            "primary_pid": 44472,
            "period": {
                "poll_timeout": 10,
                "sleep": 1.0,
                "period_label": "10s long-poll, 1s tanaffus",
            },
            "last_polling": settings.last_response,
        }

        response = self.client.get(reverse("bot-worker-status"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_running"])
        self.assertEqual(payload["pids"], [28820, 44472])
        self.assertEqual(payload["period_label"], "10s long-poll, 1s tanaffus")
        self.assertEqual(payload["last_polling_label"], "2026-04-22T02:15:00+05:00")

    @patch("apps.bot.views.requests.get")
    @patch("apps.bot.views.get_telegram_file")
    def test_file_proxy_downloads_file_from_telegram(self, mocked_get_file, mocked_requests_get):
        settings = BotSettings.get_solo()
        settings.bot_token = "123456:ABCDEF"
        settings.save()
        submission = BotFileSubmission.objects.create(
            custom_id="26575",
            status="published",
            file_type="photo",
            file_id="telegram-file-123",
        )

        mocked_get_file.return_value = {
            "ok": True,
            "result": {"file_path": "photos/file_123.jpg"},
        }
        telegram_response = Mock()
        telegram_response.ok = True
        telegram_response.headers = {"Content-Type": "image/jpeg"}
        telegram_response.content = b"image-bytes"
        mocked_requests_get.return_value = telegram_response

        response = self.client.get(reverse("bot-file-proxy", args=[submission.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"image-bytes")
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("file_123.jpg", response["Content-Disposition"])
        mocked_requests_get.assert_called_once()

    @patch("config.telegram_bot.requests.post")
    def test_webhook_start_sends_menu_keyboard(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.is_active = True
        settings.save()

        mocked_response = Mock()
        mocked_response.ok = True
        mocked_response.json.return_value = {"ok": True, "result": {"message_id": 501}}
        mocked_post.return_value = mocked_response

        payload = {
            "update_id": 11,
            "message": {
                "message_id": 10,
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "text": "/start",
            },
        }

        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        request_data = mocked_post.call_args.kwargs["data"]
        self.assertEqual(request_data["chat_id"], "10001")
        self.assertIn("Assalomu alaykum", request_data["text"])
        self.assertIn("Qidirish", request_data["reply_markup"])

    @patch("config.telegram_bot.requests.post")
    def test_webhook_search_button_prompts_for_id(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.is_active = True
        settings.save()

        mocked_response = Mock()
        mocked_response.ok = True
        mocked_response.json.return_value = {"ok": True, "result": {"message_id": 502}}
        mocked_post.return_value = mocked_response

        payload = {
            "update_id": 12,
            "message": {
                "message_id": 11,
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "text": "Qidirish",
            },
        }

        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        request_data = mocked_post.call_args.kwargs["data"]
        self.assertIn("ID raqamini yuboring", request_data["text"])
        self.assertIn("Qidirish", request_data["reply_markup"])

    @patch("config.telegram_bot.requests.post")
    def test_fetch_updates_stores_readable_updates_and_channels(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.parse_mode = "HTML"
        settings.is_active = True
        settings.save()

        mocked_response = Mock()
        mocked_response.ok = True
        mocked_response.json.return_value = {
            "ok": True,
            "result": [
                {
                    "update_id": 590096125,
                    "channel_post": {
                        "message_id": 32271,
                        "from": {
                            "id": 7550954976,
                            "is_bot": False,
                            "first_name": "Izzatbek",
                            "last_name": "Ulkanov",
                            "username": "izzatbekulkanov",
                        },
                        "author_signature": "Izzatbek Ulkanov",
                        "chat": {
                            "id": -1002960212973,
                            "title": "Doctor - A MRT",
                            "type": "channel",
                        },
                        "date": 1776800587,
                        "text": "27689",
                    },
                }
            ],
        }
        mocked_post.return_value = mocked_response

        response = self.client.post(reverse("bot-control"), {"action": "fetch_updates"})

        self.assertEqual(response.status_code, 302)
        update = BotTelegramUpdate.objects.get(update_id=590096125)
        self.assertEqual(update.chat_id, "-1002960212973")
        self.assertEqual(update.chat_title, "Doctor - A MRT")
        self.assertEqual(update.author_name, "Izzatbek Ulkanov")
        self.assertEqual(update.text, "27689")
        self.assertTrue(update.workflow_processed)
        self.assertEqual(update.workflow_status, "ignored")
        self.assertTrue(BotChannel.objects.filter(chat_id="-1002960212973").exists())

    @patch("config.telegram_bot.requests.post")
    def test_fetch_updates_processes_file_then_id_to_default_channel(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.parse_mode = "HTML"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        get_updates_response = Mock()
        get_updates_response.ok = True
        get_updates_response.json.return_value = {
            "ok": True,
            "result": [
                {
                    "update_id": 590096200,
                    "message": {
                        "message_id": 44,
                        "from": {
                            "id": 10001,
                            "first_name": "Qudratboy",
                            "username": "doktor_a_MRT",
                        },
                        "chat": {"id": 10001, "type": "private"},
                        "date": 1776800587,
                        "document": {
                            "file_id": "file-123",
                            "file_unique_id": "unique-123",
                            "file_name": "mrt.pdf",
                            "file_size": 2097152,
                            "mime_type": "application/pdf",
                        },
                    },
                },
                {
                    "update_id": 590096201,
                    "message": {
                        "message_id": 45,
                        "from": {
                            "id": 10001,
                            "first_name": "Qudratboy",
                            "username": "doktor_a_MRT",
                        },
                        "chat": {"id": 10001, "type": "private"},
                        "date": 1776800590,
                        "text": "26575",
                    },
                },
            ],
        }

        pending_reply_response = Mock()
        pending_reply_response.ok = True
        pending_reply_response.json.return_value = {"ok": True, "result": {"message_id": 500}}

        copy_response = Mock()
        copy_response.ok = True
        copy_response.json.return_value = {"ok": True, "result": {"message_id": 777}}

        final_reply_response = Mock()
        final_reply_response.ok = True
        final_reply_response.json.return_value = {"ok": True, "result": {"message_id": 779}}

        mocked_post.side_effect = [
            get_updates_response,
            pending_reply_response,
            copy_response,
            final_reply_response,
        ]

        response = self.client.post(reverse("bot-control"), {"action": "fetch_updates"})

        self.assertEqual(response.status_code, 302)
        submission = BotFileSubmission.objects.get(custom_id="26575")
        self.assertEqual(submission.status, "published")
        self.assertEqual(submission.source_message_id, 44)
        self.assertEqual(submission.file_id, "file-123")
        self.assertEqual(submission.target_chat_id, "-1002960212973")
        self.assertEqual(submission.target_message_id, 777)
        self.assertIsNone(submission.target_meta_message_id)
        self.assertEqual(submission.publish_method, "copy")
        self.assertIn("Qudratboy", submission.generated_caption)
        self.assertFalse(BotChannel.objects.filter(chat_id="10001").exists())

        file_update = BotTelegramUpdate.objects.get(update_id=590096200)
        id_update = BotTelegramUpdate.objects.get(update_id=590096201)
        self.assertTrue(file_update.workflow_processed)
        self.assertEqual(file_update.workflow_status, "awaiting_id")
        self.assertTrue(id_update.workflow_processed)
        self.assertEqual(id_update.workflow_status, "published")
        copy_data = mocked_post.call_args_list[2].kwargs["data"]
        self.assertIn("Fayl bazaga qo'shildi", copy_data["caption"])
        self.assertIn("Qudratboy", copy_data["caption"])
        self.assertIn("Turi: Hujjat (PDF)", copy_data["caption"])
        self.assertIn("Hajmi: 2 MB", copy_data["caption"])
        final_reply_data = mocked_post.call_args_list[3].kwargs["data"]
        self.assertIn("fayl kanalga yuborildi", final_reply_data["text"])
        self.assertIn("Doctor A | MRT", final_reply_data["text"])
        self.assertIn("Hajmi: 2 MB", final_reply_data["text"])

    @patch("config.telegram_bot.requests.post")
    def test_same_id_can_publish_multiple_files(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        responses = []
        for message_id in (777, 778, 779, 880, 881, 882):
            response = Mock()
            response.ok = True
            response.json.return_value = {"ok": True, "result": {"message_id": message_id}}
            responses.append(response)
        mocked_post.side_effect = responses

        for source_message_id in (44, 45):
            payload = {
                "update_id": source_message_id,
                "message": {
                    "message_id": source_message_id,
                    "from": {"id": 10001, "first_name": "Qudratboy", "username": "doktor_a_MRT"},
                    "chat": {"id": 10001, "type": "private"},
                    "date": 1776800587,
                    "document": {"file_id": f"file-{source_message_id}", "file_unique_id": f"unique-{source_message_id}"},
                    "caption": "11111",
                },
            }
            response = self.client.post(
                reverse("telegram-webhook"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)

        submissions = BotFileSubmission.objects.filter(custom_id="11111", status="published")
        self.assertEqual(submissions.count(), 2)
        self.assertEqual(list(submissions.order_by("source_message_id").values_list("source_message_id", flat=True)), [44, 45])

    @patch("config.telegram_bot.requests.post")
    def test_long_polling_command_processes_updates(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.is_active = True
        settings.save()

        updates_response = Mock()
        updates_response.ok = True
        updates_response.json.return_value = {
            "ok": True,
            "result": [
                {
                    "update_id": 590096300,
                    "message": {
                        "message_id": 10,
                        "from": {"id": 10001, "first_name": "Qudratboy"},
                        "chat": {"id": 10001, "type": "private"},
                        "date": 1776800587,
                        "text": "/start",
                    },
                }
            ],
        }
        reply_response = Mock()
        reply_response.ok = True
        reply_response.json.return_value = {"ok": True, "result": {"message_id": 501}}
        mocked_post.side_effect = [updates_response, reply_response]

        output = StringIO()
        call_command(
            "run_telegram_bot",
            "--once",
            "--keep-webhook",
            "--poll-timeout",
            "0",
            stdout=output,
        )

        update = BotTelegramUpdate.objects.get(update_id=590096300)
        self.assertTrue(update.workflow_processed)
        self.assertEqual(update.workflow_status, "start")
        reply_data = mocked_post.call_args_list[1].kwargs["data"]
        self.assertEqual(reply_data["chat_id"], "10001")
        self.assertIn("Qidirish", reply_data["reply_markup"])
        settings.refresh_from_db()
        self.assertTrue(settings.last_response["polling"])

    @patch("config.telegram_bot.requests.post")
    def test_id_search_falls_back_to_stored_channel_updates(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        BotTelegramUpdate.objects.create(
            update_id=590096400,
            update_type="channel_post",
            chat_id="-1002960212973",
            chat_title="Doctor A | MRT",
            chat_type="channel",
            message_id=888,
            text="26575",
            raw_payload={
                "update_id": 590096400,
                "channel_post": {
                    "message_id": 888,
                    "chat": {"id": -1002960212973, "title": "Doctor A | MRT", "type": "channel"},
                    "date": 1776800587,
                    "document": {
                        "file_id": "channel-file-123",
                        "file_unique_id": "channel-unique-123",
                    },
                    "caption": "26575",
                },
            },
        )

        copy_response = Mock()
        copy_response.ok = True
        copy_response.json.return_value = {"ok": True, "result": {"message_id": 900}}
        mocked_post.return_value = copy_response

        payload = {
            "update_id": 2,
            "message": {
                "message_id": 50,
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "text": "26575",
            },
        }
        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        submission = BotFileSubmission.objects.get(custom_id="26575")
        self.assertEqual(submission.target_message_id, 888)
        self.assertEqual(submission.publish_method, "channel_search")
        copy_data = mocked_post.call_args_list[0].kwargs["data"]
        self.assertEqual(copy_data["from_chat_id"], "-1002960212973")
        self.assertEqual(copy_data["message_id"], 888)
        self.assertIn("Fayl topildi", copy_data["caption"])
        self.assertEqual(mocked_post.call_count, 1)

    @patch("config.telegram_bot.requests.post")
    def test_id_search_falls_back_to_any_stored_channel_update(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = True
        settings.default_publish_channel = BotChannel.objects.create(chat_id="-1002960212973", label="Primary channel")
        settings.save()

        BotTelegramUpdate.objects.create(
            update_id=590096401,
            update_type="channel_post",
            chat_id="-1001111111111",
            chat_title="Legacy Archive",
            chat_type="channel",
            message_id=889,
            text="ID 44556 bo'yicha arxiv hujjati",
            raw_payload={
                "update_id": 590096401,
                "channel_post": {
                    "message_id": 889,
                    "chat": {"id": -1001111111111, "title": "Legacy Archive", "type": "channel"},
                    "date": 1776800587,
                    "document": {
                        "file_id": "legacy-file-1",
                        "file_unique_id": "legacy-unique-1",
                        "file_name": "archive.zip",
                        "file_size": 524288,
                        "mime_type": "application/zip",
                    },
                    "caption": "44556",
                },
            },
        )

        copy_response = Mock()
        copy_response.ok = True
        copy_response.json.return_value = {"ok": True, "result": {"message_id": 901}}
        mocked_post.return_value = copy_response

        payload = {
            "update_id": 5,
            "message": {
                "message_id": 51,
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "text": "44556",
            },
        }
        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        submission = BotFileSubmission.objects.get(custom_id="44556")
        self.assertEqual(submission.target_chat_id, "-1001111111111")
        self.assertEqual(submission.target_channel.display_name, "Legacy Archive")
        copy_data = mocked_post.call_args.kwargs["data"]
        self.assertEqual(copy_data["from_chat_id"], "-1001111111111")
        self.assertIn("Legacy Archive", copy_data["caption"])
        self.assertIn("Turi: Hujjat (ZIP)", copy_data["caption"])
        self.assertIn("Hajmi: 512 KB", copy_data["caption"])

    @patch("config.telegram_bot.requests.post")
    def test_id_search_with_multiple_results_prompts_year(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        for year, message_id in ((2025, 501), (2026, 601)):
            BotFileSubmission.objects.create(
                custom_id="11111",
                status="published",
                target_channel=channel,
                target_chat_id="-1002960212973",
                target_message_id=message_id,
                file_type="document",
                file_id=f"file-{message_id}",
                generated_caption=f"ID: 11111 - {year}",
                published_at=timezone.make_aware(datetime(year, 4, 22, 2, 15)),
            )

        prompt_response = Mock()
        prompt_response.ok = True
        prompt_response.json.return_value = {"ok": True, "result": {"message_id": 800}}
        mocked_post.return_value = prompt_response

        payload = {
            "update_id": 3,
            "message": {
                "message_id": 60,
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "text": "11111",
            },
        }
        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        prompt_data = mocked_post.call_args.kwargs["data"]
        self.assertIn("Yilni tanlang", prompt_data["text"])
        self.assertIn("2025", prompt_data["reply_markup"])
        self.assertIn("2026", prompt_data["reply_markup"])

    @patch("config.telegram_bot.requests.post")
    def test_id_search_year_callback_returns_single_result(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        BotFileSubmission.objects.create(
            custom_id="11111",
            status="published",
            target_channel=channel,
            target_chat_id="-1002960212973",
            target_message_id=501,
            file_type="document",
            file_id="file-501",
            generated_caption="ID: 11111 - 2025",
            published_at=timezone.make_aware(datetime(2025, 4, 22, 2, 15)),
        )
        BotFileSubmission.objects.create(
            custom_id="11111",
            status="published",
            target_channel=channel,
            target_chat_id="-1002960212973",
            target_message_id=601,
            file_type="document",
            file_id="file-601",
            generated_caption="ID: 11111 - 2026",
            published_at=timezone.make_aware(datetime(2026, 4, 22, 2, 15)),
        )

        answer_response = Mock()
        answer_response.ok = True
        answer_response.json.return_value = {"ok": True, "result": True}
        copy_response = Mock()
        copy_response.ok = True
        copy_response.json.return_value = {"ok": True, "result": {"message_id": 801}}
        mocked_post.side_effect = [answer_response, copy_response]

        payload = {
            "update_id": 4,
            "callback_query": {
                "id": "callback-1",
                "from": {"id": 10001, "first_name": "Qudratboy"},
                "message": {"message_id": 70, "chat": {"id": 10001, "type": "private"}},
                "data": "bs|11111|y:2026",
            },
        }
        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        copy_data = mocked_post.call_args_list[1].kwargs["data"]
        self.assertEqual(copy_data["from_chat_id"], "-1002960212973")
        self.assertEqual(copy_data["message_id"], 601)
        self.assertIn("Fayl topildi", copy_data["caption"])
        self.assertIn("2026", copy_data["caption"])
        self.assertEqual(mocked_post.call_count, 2)

    @patch("config.telegram_bot.requests.post")
    def test_webhook_file_with_id_publishes_to_default_channel(self, mocked_post):
        settings = BotSettings.get_solo()
        settings.bot_name = "Doctor A Bot"
        settings.bot_token = "123456:ABCDEF"
        settings.chat_id = "-1002960212973"
        settings.parse_mode = "HTML"
        settings.is_active = True
        channel = BotChannel.objects.create(chat_id="-1002960212973", label="Doctor A | MRT")
        settings.default_publish_channel = channel
        settings.save()

        copy_response = Mock()
        copy_response.ok = True
        copy_response.json.return_value = {"ok": True, "result": {"message_id": 777}}

        reply_response = Mock()
        reply_response.ok = True
        reply_response.json.return_value = {"ok": True, "result": {"message_id": 779}}

        mocked_post.side_effect = [copy_response, reply_response]

        payload = {
            "update_id": 1,
            "message": {
                "message_id": 44,
                "from": {
                    "id": 10001,
                    "first_name": "Qudratboy",
                    "username": "doktor_a_MRT",
                },
                "chat": {"id": 10001, "type": "private"},
                "date": 1776800587,
                "document": {
                    "file_id": "file-123",
                    "file_unique_id": "unique-123",
                    "file_name": "mrt.pdf",
                    "file_size": 2097152,
                    "mime_type": "application/pdf",
                },
                "caption": "26575",
            },
        }

        response = self.client.post(
            reverse("telegram-webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        submission = BotFileSubmission.objects.get(custom_id="26575")
        self.assertEqual(submission.status, "published")
        self.assertEqual(submission.target_chat_id, "-1002960212973")
        self.assertEqual(submission.target_message_id, 777)
        self.assertIsNone(submission.target_meta_message_id)
        self.assertEqual(submission.publish_method, "copy")
        self.assertIn("Qudratboy", submission.generated_caption)
        copy_data = mocked_post.call_args_list[0].kwargs["data"]
        self.assertIn("Fayl bazaga qo'shildi", copy_data["caption"])
        self.assertIn("Qudratboy", copy_data["caption"])
        self.assertIn("Turi: Hujjat (PDF)", copy_data["caption"])
        self.assertIn("Hajmi: 2 MB", copy_data["caption"])
        reply_data = mocked_post.call_args_list[1].kwargs["data"]
        self.assertIn("fayl kanalga yuborildi", reply_data["text"])
        self.assertIn("Doctor A | MRT", reply_data["text"])
        self.assertIn("Hajmi: 2 MB", reply_data["text"])
