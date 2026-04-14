from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from config.middleware import DefaultLocaleMiddleware


class DefaultLocaleMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = DefaultLocaleMiddleware(lambda request: HttpResponse("ok"))

    def test_defaults_to_uzbek_when_cookie_is_missing(self):
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="ru,en;q=0.9")

        response = self.middleware(request)

        self.assertEqual(request.LANGUAGE_CODE, "uz")
        self.assertEqual(response.headers["Content-Language"], "uz")

    def test_respects_language_cookie_when_present(self):
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="en")
        request.COOKIES["django_language"] = "ru"

        response = self.middleware(request)

        self.assertEqual(request.LANGUAGE_CODE, "ru")
        self.assertEqual(response.headers["Content-Language"], "ru")

    def test_invalid_language_cookie_falls_back_to_uzbek(self):
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="de")
        request.COOKIES["django_language"] = "invalid"

        response = self.middleware(request)

        self.assertEqual(request.LANGUAGE_CODE, "uz")
        self.assertEqual(response.headers["Content-Language"], "uz")
