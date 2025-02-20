from django import template

register = template.Library()

@register.filter
def get_language_text(data, lang_code):
    """
    JSON formatidagi matndan joriy tilga mosini chiqaradi.
    Agar mavjud bo‘lmasa, 'uz' tilidagi matn olinadi.
    """
    if isinstance(data, dict):
        return data.get(lang_code, data.get('uz', 'Tavsif mavjud emas'))
    return data  # Agar JSON bo‘lmasa, o‘zini qaytaradi.


@register.filter
def get_language_text(dictionary, lang_code):
    """ JSON ichidan joriy til bo‘yicha qiymatni chiqaradi """
    return dictionary.get(lang_code, dictionary.get("uz", "Ma'lumot yo'q"))