from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View


class LogoutView(View):
    """ Foydalanuvchini tizimdan chiqarish """

    def get(self, request):
        """ Logout qilish va login sahifasiga yo‘naltirish """
        if request.user.is_authenticated:
            print(f"🔴 Foydalanuvchi tizimdan chiqmoqda: {request.user}")
            logout(request)
        else:
            print("🔹 Foydalanuvchi allaqachon tizimdan chiqqan.")

        return redirect("main-dashboard")  # 🔄 Logout qilingandan keyin login sahifasiga qaytarish
