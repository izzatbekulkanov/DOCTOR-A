from django import template

register = template.Library()

@register.filter
def get_language_text(description, lang_code):
    """
    JSON tavsiflardan joriy tilga mos bo'lganini olish.
    Agar joriy til yo‘q bo‘lsa, O‘zbekcha ('uz') olinadi.
    """
    if isinstance(description, dict):
        return description.get(lang_code, description.get('uz', 'Tavsif mavjud emas'))
    return description  # Agar JSON bo‘lmasa, o‘zini qaytaradi.
