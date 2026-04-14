from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class DefaultLocaleMiddleware(LocaleMiddleware):
    """
    Default to the project language when the user hasn't explicitly chosen one.

    Django's stock LocaleMiddleware falls back to the browser's
    Accept-Language header. For this project we want Uzbek by default, while
    still respecting the language cookie written by set_language.
    """

    def process_request(self, request):
        urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = (
            is_language_prefix_patterns_used(urlconf)
        )

        language = None
        if i18n_patterns_used:
            language = translation.get_language_from_path(request.path_info)

        if language is None:
            language = self._get_language_from_cookie(request) or settings.LANGUAGE_CODE

        if (
            language is None
            and i18n_patterns_used
            and not prefixed_default_language
        ):
            language = settings.LANGUAGE_CODE

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    @staticmethod
    def _get_language_from_cookie(request):
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if not language:
            return None

        try:
            return translation.get_supported_language_variant(language)
        except LookupError:
            return None
