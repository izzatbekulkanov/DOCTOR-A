from django import template
import json

register = template.Library()

@register.filter
def get_language_text(data, lang_code):
    """
    JSON formatidagi matndan joriy tilga mos keladigan matnni chiqaradi.
    Agar mavjud bo‘lmasa, 'uz' tilidagi matn olinadi.
    """
    if isinstance(data, str):  # JSON string bo'lsa
        try:
            data = json.loads(data)  # JSON formatga o‘tkazamiz
        except json.JSONDecodeError:
            return data  # Agar xatolik bo‘lsa, o‘zini qaytaradi

    if isinstance(data, dict):  # Agar lug‘at bo‘lsa
        return data.get(lang_code, data.get('uz', 'Tavsif mavjud emas'))

    return data  # Agar JSON bo‘lmasa, o‘zini qaytaradi

@register.filter
def get_initials(value):
    if not value:
        return ""
    parts = value.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return value[:1].upper()

@register.filter
def lookup(value, key):
    return value.get(key, '')


@register.filter(name='multiply')
def multiply(value, arg):
    """Ikki qiymatni ko'paytiradi."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value  # Agar xatolik yuz bersa, asl qiymatni qaytaradi