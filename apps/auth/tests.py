from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class LoginViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="doctora",
            email="doctora@example.com",
            password=self.password,
        )
        self.login_url = reverse("login")

    def test_login_page_sets_csrf_cookie_and_disables_cache(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("no-cache", response.headers.get("Cache-Control", ""))

    def test_login_accepts_email_and_safe_next_url(self):
        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.email,
                "password": self.password,
                "next": reverse("users-view"),
            },
        )

        self.assertRedirects(response, reverse("users-view"), fetch_redirect_response=False)

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.username,
                "password": self.password,
                "next": "https://evil.example.com/steal",
            },
        )

        self.assertRedirects(response, reverse("admin-index"), fetch_redirect_response=False)

    def test_login_does_not_require_turnstile(self):
        response = self.client.post(
            self.login_url,
            {
                "email-username": self.user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(response, reverse("admin-index"), fetch_redirect_response=False)
