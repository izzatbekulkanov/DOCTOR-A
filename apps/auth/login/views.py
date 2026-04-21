import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View


User = get_user_model()


class LoginView(View):
    template_name = "auth/login.html"
    invalid_credentials_message = _("Login yoki parol noto'g'ri.")
    turnstile_required_message = _("Robot emasligingizni tasdiqlang.")
    turnstile_failed_message = _("Turnstile tekshiruvi muvaffaqiyatsiz bo'ldi. Qayta urinib ko'ring.")
    turnstile_unavailable_message = _("Kirish himoyasi vaqtincha sozlanmagan.")

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("admin-index")
        return self._render_form(request)

    def post(self, request):
        username_or_email = (request.POST.get("email-username") or "").strip()
        password = request.POST.get("password") or ""

        if not username_or_email or not password:
            messages.error(request, _("Login va parolni kiriting."))
            return self._render_form(request, status=400, login_value=username_or_email)

        turnstile_valid, turnstile_error = self._verify_turnstile(request)
        if not turnstile_valid:
            messages.error(request, turnstile_error)
            return self._render_form(request, status=400, login_value=username_or_email)

        username = self._resolve_username(username_or_email)
        authenticated_user = authenticate(request, username=username, password=password)
        if not authenticated_user:
            messages.error(request, self.invalid_credentials_message)
            return self._render_form(request, status=401, login_value=username_or_email)

        login(request, authenticated_user)
        return redirect(self._get_success_url(request))

    def _render_form(self, request, status=200, login_value=""):
        return render(
            request,
            self.template_name,
            {
                "next": self._get_next_url(request),
                "login_value": login_value,
                "turnstile_enabled": bool(settings.TURNSTILE_SITE_KEY),
                "turnstile_required": settings.TURNSTILE_REQUIRED,
                "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
                "turnstile_script_url": settings.TURNSTILE_SCRIPT_URL,
            },
            status=status,
        )

    def _get_success_url(self, request):
        next_url = self._get_next_url(request)
        if next_url:
            return next_url
        return reverse("admin-index")

    def _get_next_url(self, request):
        candidate = (request.POST.get("next") or request.GET.get("next") or "").strip()
        if not candidate:
            return ""

        allowed_hosts = set(settings.ALLOWED_HOSTS)
        host = request.get_host()
        if host:
            allowed_hosts.add(host)

        if url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts=allowed_hosts,
            require_https=request.is_secure(),
        ):
            return candidate
        return ""

    def _resolve_username(self, username_or_email):
        if "@" not in username_or_email:
            return username_or_email

        matched_user = User.objects.filter(email__iexact=username_or_email).only("username").first()
        if matched_user:
            return matched_user.username
        return username_or_email

    def _verify_turnstile(self, request):
        if not settings.TURNSTILE_REQUIRED:
            return True, ""

        token = (request.POST.get("cf-turnstile-response") or "").strip()
        if not token:
            return False, self.turnstile_required_message

        if not settings.TURNSTILE_SECRET_KEY:
            return False, self.turnstile_unavailable_message

        payload = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }
        client_ip = self._get_client_ip(request)
        if client_ip:
            payload["remoteip"] = client_ip

        try:
            response = requests.post(
                settings.TURNSTILE_VERIFY_URL,
                data=payload,
                timeout=settings.TURNSTILE_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException:
            return False, self.turnstile_failed_message

        return bool(result.get("success")), self.turnstile_failed_message

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return (
            request.META.get("HTTP_CF_CONNECTING_IP")
            or request.META.get("REMOTE_ADDR", "")
        ).strip()
