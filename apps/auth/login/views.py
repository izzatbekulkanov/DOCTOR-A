from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.views import View

from apps.auth.views import AuthView

User = get_user_model()  # ✅ Django ichki foydalanuvchi modelini olish

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            print("✅ Foydalanuvchi oldin login qilgan:", request.user)
            return redirect("admin-index")  # ✅ Foydalanuvchi login bo'lsa, `admin-index` sahifasiga yuborish

        # ✅ `next` parametrini olish va kontekstga qo'shish
        next_url = request.GET.get("next", "")
        print(f"🟢 GET so‘rov qabul qilindi. next = {next_url}")
        return render(request, "auth/login.html", {"next": next_url})

    def post(self, request):
        print("🔵 POST so‘rov qabul qilindi. Login jarayoni boshlanmoqda...")

        username_or_email = request.POST.get("email-username")
        password = request.POST.get("password")
        next_url = request.POST.get("next", "")  # ✅ `next` parametrini olish

        print(f"🔹 Kiritilgan login ma'lumotlari: username_or_email = {username_or_email}, next_url = {next_url}")

        if not username_or_email or not password:
            print("❌ Xato: Username yoki parol kiritilmagan.")
            messages.error(request, "Iltimos, username yoki email va parolni kiriting.")
            return redirect("login")

        # ✅ Foydalanuvchi email orqali login qilmoqchi bo'lsa, `username` ni olish
        if "@" in username_or_email:
            user = User.objects.filter(email=username_or_email).first()
            if user:
                username = user.username
                print(f"✅ Email orqali topilgan username: {username}")
            else:
                print("❌ Xato: Kiritilgan email tizimda topilmadi.")
                messages.error(request, "Email noto'g'ri.")
                return redirect("login")
        else:
            username = username_or_email
            print(f"🔹 Foydalanuvchi username orqali login qilmoqda: {username}")

        # ✅ Autentifikatsiya qilish
        authenticated_user = authenticate(request, username=username, password=password)
        if authenticated_user:
            print(f"✅ Autentifikatsiya muvaffaqiyatli! Foydalanuvchi: {authenticated_user}")
            login(request, authenticated_user)

            # ✅ `next` parametri mavjud bo'lsa, unga yo'naltirish, aks holda `admin-index` ga
            redirect_url = next_url if next_url else "admin-index"
            print(f"➡️ {redirect_url} sahifasiga yo'naltirilmoqda...")
            return redirect(redirect_url)
        else:
            print("❌ Xato: Username yoki parol noto'g'ri.")
            messages.error(request, "Username yoki parol noto'g'ri.")
            return redirect("login")
