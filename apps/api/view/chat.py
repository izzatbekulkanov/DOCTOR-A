import json
import logging
import re

import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

GEMINI_TIMEOUT_SECONDS = 30
MAX_USER_MESSAGE_LENGTH = 2000
MAX_HISTORY_TURNS = 10
MAX_CONTEXT_CHARS = 8000

BASE_SYSTEM_INSTRUCTION = (
    "Siz Doctor A Med Clinic veb-saytining yordamchi suniy intellekt suhbatdoshisiz. "
    "Klinika Namangan shahrida joylashgan. "
    "Foydalanuvchilar bilan iltifot va hurmat bilan muloqot qiling. "
    "Javoblaringiz qisqa, tushunarli, aniq va tartibli bo'lsin (ro'yxatlarni bullet bilan ko'rsating). "
    "Foydalanuvchining tilida javob bering (o'zbek, rus yoki ingliz). "
    "Tibbiy tashxis qo'ymang yoki dori-darmon tavsiya qilmang — buning o'rniga shifokor bilan maslahatlashishni taklif qiling. "
    "Quyida saytdan olingan haqiqiy ma'lumotlar berilgan — savolga aniq shu ma'lumotlar asosida javob bering. "
    "Agar so'ralgan ma'lumot kontekstda yo'q bo'lsa, halol ayting va Bog'lanish sahifasiga yo'naltiring."
)


# Kalit so'zlar — qaysi context blokini yuklashni aniqlash uchun
DOCTOR_KEYWORDS = re.compile(
    r"shifokor|doktor|vrach|doctor|narkolog|kardiolog|terapevt|pediatr|"
    r"nevropatolog|nevrolog|xirurg|hirurg|gastroenterolog|akusher|"
    r"urolog|dermatolog|ginekolog|stomatolog|lor|mutaxassis|specialist",
    re.IGNORECASE,
)
NEWS_KEYWORDS = re.compile(r"yangilik|news|новост", re.IGNORECASE)
ANNOUNCEMENT_KEYWORDS = re.compile(r"e['\u2019]?lon|elon|announcement|объявлен", re.IGNORECASE)
SERVICE_KEYWORDS = re.compile(r"xizmat|service|услуг", re.IGNORECASE)
EQUIPMENT_KEYWORDS = re.compile(r"qurilma|uskuna|equipment|оборудовани", re.IGNORECASE)
CONTACT_KEYWORDS = re.compile(
    r"telefon|phone|aloqa|contact|address|manzil|адрес|контакт|"
    r"qachon|ish vaqti|working hours|часы",
    re.IGNORECASE,
)
ABOUT_KEYWORDS = re.compile(
    r"klinika|clinic|biz haqimizda|about|haqida|о нас|tarix|history",
    re.IGNORECASE,
)


def _clean_text(text, max_length=300):
    if not text:
        return ""
    plain = strip_tags(str(text)).replace("\xa0", " ").strip()
    plain = re.sub(r"\s+", " ", plain)
    if len(plain) > max_length:
        plain = plain[:max_length].rstrip() + "..."
    return plain


def _localize(value, lang="uz"):
    if isinstance(value, dict):
        return value.get(lang) or value.get("uz") or value.get("en") or next(iter(value.values()), "")
    return value or ""


def _build_doctors_context(lang="uz"):
    try:
        from apps.members.models import CustomUser
    except Exception:
        return ""

    qs = CustomUser.objects.filter(
        is_active_employee=True,
        is_superuser=False,
        is_staff=True,
    ).exclude(medical_specialty="").order_by("full_name")[:50]

    if not qs:
        return ""

    lines = ["KLINIKA SHIFOKORLARI:"]
    for doctor in qs:
        parts = [doctor.full_name or doctor.username]
        if doctor.medical_specialty:
            parts.append(f"mutaxassisligi: {doctor.medical_specialty}")
        if doctor.job_title:
            parts.append(f"lavozim: {doctor.job_title}")
        if doctor.department:
            parts.append(f"bo'lim: {doctor.department}")
        if doctor.phone_number:
            parts.append(f"tel: {doctor.phone_number}")
        if doctor.work_start_time and doctor.work_end_time:
            parts.append(
                f"ish vaqti: {doctor.work_start_time.strftime('%H:%M')}-{doctor.work_end_time.strftime('%H:%M')}"
            )
        lines.append("- " + "; ".join(parts))
    return "\n".join(lines)


def _build_news_context(lang="uz"):
    try:
        from apps.news.models import News
    except Exception:
        return ""

    qs = News.objects.filter(is_published=True).order_by("-published_date")[:8]
    if not qs:
        return ""

    lines = ["KLINIKA YANGILIKLARI (eng so'nggilari):"]
    for item in qs:
        title = _localize(item.title, lang) or "Yangilik"
        content = _localize(item.content, lang)
        date_str = item.published_date.strftime("%Y-%m-%d") if item.published_date else ""
        line = f"- [{date_str}] {title}"
        summary = _clean_text(content, 200)
        if summary:
            line += f" — {summary}"
        lines.append(line)
    return "\n".join(lines)


def _build_announcements_context(lang="uz"):
    try:
        from apps.news.models import Announcement
    except Exception:
        return ""

    qs = Announcement.objects.filter(is_published=True).order_by("-published_date")[:8]
    if not qs:
        return ""

    lines = ["KLINIKA E'LONLARI:"]
    for item in qs:
        title = _localize(item.title, lang) or "E'lon"
        content = _localize(item.content, lang)
        date_str = item.published_date.strftime("%Y-%m-%d") if item.published_date else ""
        line = f"- [{date_str}] {title}"
        summary = _clean_text(content, 200)
        if summary:
            line += f" — {summary}"
        lines.append(line)
    return "\n".join(lines)


def _build_services_context(lang="uz"):
    try:
        from apps.medical.models import ClinicService
    except Exception:
        return ""

    qs = ClinicService.objects.filter(is_active=True).order_by("sort_order", "id")[:30]
    if not qs:
        return ""

    lines = ["KLINIKA XIZMATLARI:"]
    for item in qs:
        title = _localize(item.title, lang)
        summary = _localize(item.summary, lang)
        line = f"- {title}"
        if summary:
            line += f" — {_clean_text(summary, 150)}"
        lines.append(line)
    return "\n".join(lines)


def _build_equipment_context(lang="uz"):
    try:
        from apps.medical.models import ClinicEquipment
    except Exception:
        return ""

    qs = ClinicEquipment.objects.filter(is_active=True)[:20]
    if not qs:
        return ""

    lines = ["KLINIKA QURILMALARI:"]
    for item in qs:
        name = _localize(item.name, lang)
        desc = _localize(item.description, lang)
        line = f"- {name}"
        if desc:
            line += f" — {_clean_text(desc, 150)}"
        lines.append(line)
    return "\n".join(lines)


def _build_contact_context(lang="uz"):
    try:
        from apps.medical.models import SiteSettings, ContactPhone
    except Exception:
        return ""

    site = SiteSettings.objects.first()
    lines = ["KLINIKA ALOQA MA'LUMOTLARI:"]
    has_data = False

    if site:
        if site.contact_phone:
            lines.append(f"- Asosiy telefon: {site.contact_phone}")
            has_data = True
        if site.contact_email:
            lines.append(f"- Email: {site.contact_email}")
            has_data = True
        if site.address:
            address = _clean_text(_localize(site.address, lang) or site.address, 300)
            if address:
                lines.append(f"- Manzil: {address}")
                has_data = True
        if site.working_hours:
            wh = _clean_text(_localize(site.working_hours, lang) or site.working_hours, 300)
            if wh:
                lines.append(f"- Ish vaqti: {wh}")
                has_data = True
        if site.telegram_url:
            lines.append(f"- Telegram: {site.telegram_url}")
            has_data = True
        if site.instagram_url:
            lines.append(f"- Instagram: {site.instagram_url}")
            has_data = True

    extra_phones = ContactPhone.objects.all()[:5]
    for phone in extra_phones:
        desc = _localize(phone.description, lang) if phone.description else ""
        line = f"- Qo'shimcha telefon: {phone.phone_number}"
        if desc:
            line += f" ({_clean_text(desc, 80)})"
        lines.append(line)
        has_data = True

    return "\n".join(lines) if has_data else ""


def _build_about_context(lang="uz"):
    try:
        from apps.medical.models import DoctorAInfo
    except Exception:
        return ""

    qs = DoctorAInfo.objects.order_by("-created_at")[:3]
    if not qs:
        return ""

    lines = ["KLINIKA HAQIDA:"]
    for item in qs:
        title = _localize(item.title, lang)
        desc = _localize(item.description, lang)
        if title:
            lines.append(f"- {title}: {_clean_text(desc, 400)}")
        elif desc:
            lines.append(f"- {_clean_text(desc, 400)}")
    return "\n".join(lines)


def build_clinic_context(user_message, lang="uz"):
    """Foydalanuvchi savoliga qarab kerakli ma'lumot bloklarini birlashtiradi."""
    msg = user_message or ""
    sections = []

    # Always include short contact info — bu eng tez-tez kerak
    contact = _build_contact_context(lang)
    if contact:
        sections.append(contact)

    if DOCTOR_KEYWORDS.search(msg):
        block = _build_doctors_context(lang)
        if block:
            sections.append(block)

    if NEWS_KEYWORDS.search(msg):
        block = _build_news_context(lang)
        if block:
            sections.append(block)

    if ANNOUNCEMENT_KEYWORDS.search(msg):
        block = _build_announcements_context(lang)
        if block:
            sections.append(block)

    if SERVICE_KEYWORDS.search(msg):
        block = _build_services_context(lang)
        if block:
            sections.append(block)

    if EQUIPMENT_KEYWORDS.search(msg):
        block = _build_equipment_context(lang)
        if block:
            sections.append(block)

    if ABOUT_KEYWORDS.search(msg):
        block = _build_about_context(lang)
        if block:
            sections.append(block)

    # Agar hech qanday kalit so'z mos kelmagan bo'lsa — short overview ber
    if len(sections) <= 1:
        for builder in (_build_doctors_context, _build_services_context, _build_announcements_context):
            block = builder(lang)
            if block and block not in sections:
                sections.append(block)

    combined = "\n\n".join(sections)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[:MAX_CONTEXT_CHARS].rstrip() + "\n[...]"
    return combined


def detect_language(message):
    msg = message or ""
    if re.search(r"[а-яА-Я]", msg):
        return "ru"
    if re.search(r"[a-zA-Z]", msg) and not re.search(r"[ўғҳқўЎҒҲҚЎ]", msg):
        # Ehtimoliy ingliz, lekin o'zbek lotin alifbosi ham [a-z] dan iborat
        # Shunchaki default 'uz' qoldiramiz, AI o'zi tilini aniqlaydi
        return "uz"
    return "uz"


@method_decorator(csrf_exempt, name="dispatch")
class AIChatView(View):
    """Google Gemini API ga proxy. Frontendga API kalitni oshkor qilmaydi."""

    def post(self, request, *args, **kwargs):
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return JsonResponse(
                {"ok": False, "error": "AI chat sozlanmagan."},
                status=503,
            )

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "Noto'g'ri so'rov formati."}, status=400)

        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return JsonResponse({"ok": False, "error": "Xabar bo'sh."}, status=400)

        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            user_message = user_message[:MAX_USER_MESSAGE_LENGTH]

        history = payload.get("history") or []
        if not isinstance(history, list):
            history = []

        lang = detect_language(user_message)
        clinic_context = build_clinic_context(user_message, lang=lang)
        system_text = BASE_SYSTEM_INSTRUCTION
        if clinic_context:
            system_text += "\n\n=== SAYTDAGI HAQIQIY MA'LUMOTLAR ===\n" + clinic_context

        contents = self._build_contents(history, user_message)

        body = {
            "contents": contents,
            "systemInstruction": {
                "role": "user",
                "parts": [{"text": system_text}],
            },
            "generationConfig": {
                "temperature": 0.6,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            },
        }

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent?key={api_key}"
        )

        try:
            response = requests.post(
                url,
                json=body,
                timeout=GEMINI_TIMEOUT_SECONDS,
                headers={"Content-Type": "application/json"},
            )
        except requests.RequestException as exc:
            logger.warning("Gemini request failed: %s", exc)
            return JsonResponse(
                {"ok": False, "error": "AI xizmatiga ulanib bo'lmadi."},
                status=502,
            )

        if response.status_code >= 400:
            logger.warning("Gemini API error %s: %s", response.status_code, response.text[:500])
            error_message = "AI xizmati xato qaytardi."
            try:
                error_payload = response.json()
                api_error = (error_payload or {}).get("error", {})
                api_status = api_error.get("status") or ""
                if response.status_code == 429 or api_status == "RESOURCE_EXHAUSTED":
                    error_message = "AI xizmatining limiti tugadi, biroz keyin urinib ko'ring."
                elif response.status_code in (401, 403):
                    error_message = "AI xizmatiga kirish ruxsati yo'q."
                elif response.status_code == 404:
                    error_message = "AI modeli topilmadi. Administrator bilan bog'laning."
            except ValueError:
                pass
            return JsonResponse(
                {"ok": False, "error": error_message},
                status=502,
            )

        try:
            data = response.json()
        except ValueError:
            return JsonResponse(
                {"ok": False, "error": "AI xizmatidan noto'g'ri javob keldi."},
                status=502,
            )

        reply_text = self._extract_reply(data)
        if not reply_text:
            return JsonResponse(
                {"ok": False, "error": "AI bo'sh javob qaytardi."},
                status=502,
            )

        return JsonResponse({"ok": True, "reply": reply_text})

    @staticmethod
    def _build_contents(history, user_message):
        contents = []
        trimmed = history[-(MAX_HISTORY_TURNS * 2):]
        for entry in trimmed:
            role = entry.get("role")
            text = (entry.get("text") or "").strip()
            if not text or role not in {"user", "assistant"}:
                continue
            contents.append({
                "role": "user" if role == "user" else "model",
                "parts": [{"text": text[:MAX_USER_MESSAGE_LENGTH]}],
            })

        contents.append({
            "role": "user",
            "parts": [{"text": user_message}],
        })
        return contents

    @staticmethod
    def _extract_reply(data):
        try:
            candidates = data.get("candidates") or []
            if not candidates:
                return ""
            parts = (candidates[0].get("content") or {}).get("parts") or []
            chunks = [part.get("text", "") for part in parts if part.get("text")]
            return "\n".join(chunks).strip()
        except (AttributeError, KeyError, IndexError, TypeError):
            return ""
