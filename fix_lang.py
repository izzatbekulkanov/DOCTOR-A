import re

with open('/Users/macbookpro/Documents/GitHub/DOCTOR-A/templates/v1/partials/_header.html', 'r', encoding='utf-8') as f:
    header = f.read()

# Replace the old lang-select-item
new_dropdown = """								<li class="dropdown language-option" style="margin-left: 10px;">
									{% load i18n %}
									{% get_current_language as CURRENT_LANG %}
									<a class="dropdown-toggle" href="#" id="v1LanguageDropdown" role="button" data-toggle="dropdown" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="display: inline-flex; align-items: center; gap: 6px; cursor: pointer;">
										<i class="bx bx-globe"></i>
										<span style="font-size: 13px; font-weight: 600; color: #545454; margin-top: 2px;">
											{% if CURRENT_LANG == 'uz' %}O'zbek
											{% elif CURRENT_LANG == 'ru' %}Русский
											{% elif CURRENT_LANG == 'en' %}English
											{% elif CURRENT_LANG == 'de' %}Deutsch
											{% elif CURRENT_LANG == 'tr' %}Türkçe
											{% endif %}
										</span>
									</a>
									<div class="dropdown-menu dropdown-menu-right" aria-labelledby="v1LanguageDropdown" style="border: none; box-shadow: 0 5px 25px rgba(0,0,0,0.1); border-radius: 8px; min-width: 140px; padding: 10px 0; margin-top: 15px; border-top: 2px solid #e21919;">
										<form action="{% url 'set_language' %}" method="post" style="margin:0;">
											{% csrf_token %}
											<input name="next" type="hidden" value="{{ request.get_full_path }}">
											
											<button type="submit" name="language" value="uz" class="dropdown-item" style="padding: 8px 20px; font-size: 14px; transition: 0.3s; {% if CURRENT_LANG == 'uz' %}color: #e21919; font-weight: 600; background: transparent;{% endif %}">🇺🇿 O'zbek</button>
											<button type="submit" name="language" value="ru" class="dropdown-item" style="padding: 8px 20px; font-size: 14px; transition: 0.3s; {% if CURRENT_LANG == 'ru' %}color: #e21919; font-weight: 600; background: transparent;{% endif %}">🇷🇺 Русский</button>
											<button type="submit" name="language" value="en" class="dropdown-item" style="padding: 8px 20px; font-size: 14px; transition: 0.3s; {% if CURRENT_LANG == 'en' %}color: #e21919; font-weight: 600; background: transparent;{% endif %}">🇬🇧 English</button>
											<button type="submit" name="language" value="de" class="dropdown-item" style="padding: 8px 20px; font-size: 14px; transition: 0.3s; {% if CURRENT_LANG == 'de' %}color: #e21919; font-weight: 600; background: transparent;{% endif %}">🇩🇪 Deutsch</button>
											<button type="submit" name="language" value="tr" class="dropdown-item" style="padding: 8px 20px; font-size: 14px; transition: 0.3s; {% if CURRENT_LANG == 'tr' %}color: #e21919; font-weight: 600; background: transparent;{% endif %}">🇹🇷 Türkçe</button>
										</form>
									</div>
								</li>"""

# Replace anything from <li class="lang-select-item">...</li>
header = re.sub(
    r'<li class="lang-select-item">.*?</li>',
    new_dropdown,
    header,
    flags=re.DOTALL
)

with open('/Users/macbookpro/Documents/GitHub/DOCTOR-A/templates/v1/partials/_header.html', 'w', encoding='utf-8') as f:
    f.write(header)

print("✅ done replacing")
