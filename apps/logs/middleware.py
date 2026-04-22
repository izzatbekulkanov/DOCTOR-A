import ipaddress
import logging

from django.contrib.auth import get_user_model
from django.utils.timezone import now

from .models import Log

User = get_user_model()
logger = logging.getLogger(__name__)


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            user = request.user if request.user.is_authenticated else None

            log = Log.objects.create(
                timestamp=now(),
                ip_address=ip_address,
                method=request.method,
                path=request.get_full_path(),
                status_code=response.status_code,
                user_agent=user_agent,
                user=user,
            )

            # Terminalga chiqarish
            # self.print_log(log)
        except Exception:
            logger.exception("Request logini saqlashda xatolik yuz berdi.")

        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        if not ip:
            return None

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return None

        return ip

    @staticmethod
    def print_log(log):
        """Log ma'lumotlarini terminalga chiqarish"""
        print(f"""

        Vaqt: {log.timestamp}
        IP Manzil: {log.ip_address}
        Metod: {log.method}
        Path: {log.path}
        Status Code: {log.status_code}
        User Agent: {log.user_agent}
        Foydalanuvchi: {log.user.username if log.user else "Anonim"}
        """)
