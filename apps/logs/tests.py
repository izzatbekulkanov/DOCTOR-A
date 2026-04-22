from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.logs.middleware import LogMiddleware


class LogMiddlewareTests(TestCase):
    def test_invalid_forwarded_ip_does_not_break_response(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="bad-ip-value")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()

        middleware = LogMiddleware(lambda request: HttpResponse("ok"))
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_log_create_error_is_swallowed(self):
        request = RequestFactory().get("/")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()

        middleware = LogMiddleware(lambda request: HttpResponse("ok"))
        with (
            patch("apps.logs.middleware.Log.objects.create", side_effect=RuntimeError("db error")),
            patch("apps.logs.middleware.logger.exception"),
        ):
            response = middleware(request)

        self.assertEqual(response.status_code, 200)
