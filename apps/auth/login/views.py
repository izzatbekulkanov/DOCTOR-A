from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View


User = get_user_model()


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(View):
    template_name = "auth/login.html"
    invalid_credentials_message = _("Login yoki parol noto'g'ri.")

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
