from django.test import TestCase
from django.urls import reverse

from apps.news.models import News
from apps.members.models import CustomUser


class NewsRichTextTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="editor",
            password="testpass123",
            full_name="Editor User",
        )

    def test_news_detail_post_saves_html_and_allows_clearing_language_content(self):
        news = News.objects.create(
            title={"uz": "Eski sarlavha", "en": "Old title"},
            content={"uz": "Eski matn", "en": "Old content"},
            author=self.user,
            is_published=True,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("news-detail"),
            {
                "news_id": news.id,
                "title_uz": "Yangi sarlavha",
                "content_uz": "<p><strong>Qalin</strong> matn</p>",
                "title_en": "",
                "content_en": "",
            },
        )

        self.assertEqual(response.status_code, 200)

        news.refresh_from_db()
        self.assertEqual(news.title["uz"], "Yangi sarlavha")
        self.assertEqual(news.content["uz"], "<p><strong>Qalin</strong> matn</p>")
        self.assertEqual(news.title["en"], "")
        self.assertEqual(news.content["en"], "")

    def test_landing_news_detail_renders_saved_html_without_escaping(self):
        news = News.objects.create(
            title={"uz": "HTML yangilik"},
            content={"uz": "<p><strong>HTML</strong> ko‘rinishi</p>"},
            author=self.user,
            is_published=True,
        )

        response = self.client.get(reverse("landing-v1-news-detail", args=[news.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>HTML</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;HTML&lt;/strong&gt;")
