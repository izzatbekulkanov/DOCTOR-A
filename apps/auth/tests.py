from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


User = get_user_model()


@override_settings(
    TURNSTILE_SITE_KEY="site-key",
    TURNSTILE_SECRET_KEY="secret-key",
    TURNSTILE_REQUIRED=True,
)
class LoginViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="doctora",
            email="doctora@example.com",
            password=self.password,
        )
        self.login_url = reverse("login")

    def test_login_requires_turnstile_token(self):
        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.username,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("apps.auth.login.views.requests.post")
    def test_login_rejects_failed_turnstile_verification(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.username,
                "password": self.password,
                "cf-turnstile-response": "invalid-token",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("apps.auth.login.views.requests.post")
    def test_login_accepts_email_and_safe_next_url(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.email,
                "password": self.password,
                "cf-turnstile-response": "valid-token",
                "next": reverse("users-view"),
            },
        )

        self.assertRedirects(response, reverse("users-view"), fetch_redirect_response=False)

    @patch("apps.auth.login.views.requests.post")
    def test_login_ignores_external_next_url(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.username,
                "password": self.password,
                "cf-turnstile-response": "valid-token",
                "next": "https://evil.example.com/steal",
            },
        )

        self.assertRedirects(response, reverse("admin-index"), fetch_redirect_response=False)


@override_settings(
    TURNSTILE_SITE_KEY="site-key",
    TURNSTILE_SECRET_KEY="",
    TURNSTILE_REQUIRED=False,
)
class LoginViewWithoutTurnstileTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="clinicadmin",
            email="clinicadmin@example.com",
            password=self.password,
        )

    def test_login_works_when_turnstile_disabled(self):
        response = self.client.post(
            reverse("login"),
            {
                "email-username": self.user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(response, reverse("admin-index"), fetch_redirect_response=False)
