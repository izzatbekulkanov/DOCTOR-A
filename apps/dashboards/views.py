from collections import Counter
from datetime import date
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView
from django.utils.html import strip_tags
from django.db.models import Q
from django.db import models
from django.utils.translation import get_language
import unicodedata
from apps.medical.models import Video, ClinicEquipment, SiteSettings, MedicalCheckupApplication, ClinicService
from apps.news.models import News, Comment, Announcement
from apps.members.models import CustomUser, Appointment



class LandingPageV1View(TemplateView):
    """Yangi landing page - root URL da ishlaydi (medic template asosida)"""
    template_name = "v1/index.html"

    PAGE_TRANSLATIONS = {
        "hero_title": {
            "uz": "Har bir davolash bosqichi uchun zamonaviy va ishonchli tibbiy xizmatlar",
            "ru": "Современная и надежная медицинская помощь на каждом этапе лечения",
            "en": "Comprehensive medical care for every stage of treatment",
            "de": "Moderne und zuverlassige medizinische Versorgung fur jede Behandlungsphase",
            "tr": "Tedavinin her asamasi icin modern ve guvenilir tibbi hizmetler",
        },
        "hero_intro": {
            "uz": "Doctor A Med Clinic diagnostika, mutaxassis qabul, instrumental tekshiruv va tezkor yonaltirish xizmatlarini bir joyda taqdim etadi.",
            "ru": "Doctor A Med Clinic объединяет диагностику, прием специалистов, инструментальные обследования и быстрые маршруты лечения в одном месте.",
            "en": "Doctor A Med Clinic brings diagnostics, specialist consultations, instrumental examinations, and fast treatment routing together in one place.",
            "de": "Doctor A Med Clinic vereint Diagnostik, Facharzttermine, instrumentelle Untersuchungen und schnelle Behandlungswege an einem Ort.",
            "tr": "Doctor A Med Clinic tashxis, mutaxassis qabuli, instrumental tekshiruv va tezkor davolash yonaltirishini bir joyda birlashtiradi.",
        },
        "services_top_title": {
            "uz": "Xizmatlarimiz",
            "ru": "Наши услуги",
            "en": "Our Services",
            "de": "Unsere Leistungen",
            "tr": "Hizmetlerimiz",
        },
        "services_heading_lead": {
            "uz": "Bizning tibbiy",
            "ru": "Наши медицинские",
            "en": "Our Healthcare",
            "de": "Unsere medizinischen",
            "tr": "Saglik",
        },
        "services_heading_highlight": {
            "uz": "xizmatlarimiz",
            "ru": "услуги",
            "en": "Services",
            "de": "Leistungen",
            "tr": "Hizmetlerimiz",
        },
        "services_intro": {
            "uz": "Klinikamizda diagnostika, konsultatsiya va davolashning asosiy yonalishlari yagona tizim asosida tashkil qilingan.",
            "ru": "Основные направления диагностики, консультации и лечения в нашей клинике организованы как единая система.",
            "en": "The clinic organizes its core diagnostic, consultation, and treatment directions as one coordinated care system.",
            "de": "Die zentralen Bereiche Diagnose, Beratung und Behandlung sind in unserer Klinik als einheitliches Versorgungssystem organisiert.",
            "tr": "Klinigimizdagi tashxis, konsultatsiya va davolashning asosiy yonalishlari yagona tizim sifatida tashkil etilgan.",
        },
        "services_read_more": {
            "uz": "Batafsil",
            "ru": "Подробнее",
            "en": "Read More",
            "de": "Mehr erfahren",
            "tr": "Detaylar",
        },
        "services_empty_title": {
            "uz": "Xizmatlar hali qoshilmagan",
            "ru": "Услуги пока не добавлены",
            "en": "Services have not been added yet",
            "de": "Es wurden noch keine Leistungen hinzugefugt",
            "tr": "Hizmetler henuz eklenmedi",
        },
        "services_empty_description": {
            "uz": "Bu bolim tez orada malumotlar bilan toldiriladi.",
            "ru": "Этот раздел будет заполнен в ближайшее время.",
            "en": "This section will be filled with content shortly.",
            "de": "Dieser Bereich wird in Kurze mit Inhalten gefullt.",
            "tr": "Bu bolum yakinda malumot bilan toldiriladi.",
        },
        "counter_staff": {
            "uz": "Xodimlar",
            "ru": "Сотрудники",
            "en": "Staff",
            "de": "Mitarbeiter",
            "tr": "Xodimlar",
        },
        "counter_doctors": {
            "uz": "Shifokorlar",
            "ru": "Врачи",
            "en": "Doctors",
            "de": "Arzte",
            "tr": "Doktorlar",
        },
        "counter_surgeons": {
            "uz": "Jarrohlar",
            "ru": "Хирурги",
            "en": "Surgeons",
            "de": "Chirurgen",
            "tr": "Cerrahlar",
        },
        "counter_patients": {
            "uz": "Bemorlar",
            "ru": "Пациенты",
            "en": "Patients",
            "de": "Patienten",
            "tr": "Hastalar",
        },
        "doctors_top_title": {
            "uz": "Shifokorlar",
            "ru": "Наши врачи",
            "en": "Our Doctors",
            "de": "Unsere Arzte",
            "tr": "Doktorlarimiz",
        },
        "doctors_heading": {
            "uz": "Tajribali mutaxassislar",
            "ru": "Опытные специалисты",
            "en": "Experienced Specialists",
            "de": "Erfahrene Spezialisten",
            "tr": "Deneyimli uzmanlar",
        },
        "doctors_intro": {
            "uz": "Bemorlarga individual yondashuv, aniq tashxis va izchil kuzatuv olib boradigan mutaxassislar jamoasi.",
            "ru": "Команда специалистов, которая обеспечивает индивидуальный подход, точную диагностику и последовательное сопровождение пациента.",
            "en": "A team of specialists delivering individual care, accurate diagnostics, and consistent patient follow-up.",
            "de": "Ein Team von Spezialisten mit individueller Betreuung, genauer Diagnostik und konsequenter Nachverfolgung.",
            "tr": "Bemorlarga individual yondashuv, aniq tashxis va muntazam kuzatuv olib boradigan mutaxassislar jamoasi.",
        },
        "doctor_fallback_specialty": {
            "uz": "Shifokor",
            "ru": "Врач",
            "en": "Doctor",
            "de": "Arzt",
            "tr": "Doktor",
        },
        "doctors_empty_title": {
            "uz": "Hozircha shifokorlar malumotlari mavjud emas",
            "ru": "Пока нет данных о врачах",
            "en": "Doctor profiles are not available yet",
            "de": "Arzteprofile sind noch nicht verfugbar",
            "tr": "Henuz doktor malumotlari mavjud emas",
        },
        "doctors_empty_description": {
            "uz": "Tez orada bu bolimda shifokorlar malumotlari joylashtiriladi.",
            "ru": "В этом разделе скоро появится информация о врачах.",
            "en": "Doctor information will appear in this section soon.",
            "de": "In diesem Bereich werden bald Arztinformationen angezeigt.",
            "tr": "Bu bolumda yaqinda doktorlar malumotlari joylashtiriladi.",
        },
        "doctors_view_all": {
            "uz": "Barchasini ko'rish",
            "ru": "Все врачи",
            "en": "View All Doctors",
            "de": "Alle Arzte",
            "tr": "Tum doktorlar",
        },
        "news_top_title": {
            "uz": "Yangiliklar",
            "ru": "Новости",
            "en": "News",
            "de": "Nachrichten",
            "tr": "Haberler",
        },
        "news_heading": {
            "uz": "Songgi yangiliklar",
            "ru": "Последние новости",
            "en": "Latest News",
            "de": "Aktuelle Nachrichten",
            "tr": "Son haberler",
        },
        "news_intro": {
            "uz": "Klinikamizdagi songgi yangiliklar, xizmatlar yangilanishi va muhim malumotlar shu bolimda joylashtiriladi.",
            "ru": "Последние новости клиники, обновления услуг и важные объявления публикуются в этом разделе.",
            "en": "The latest clinic news, service updates, and important announcements are published in this section.",
            "de": "Neuigkeiten der Klinik, Leistungsupdates und wichtige Mitteilungen werden in diesem Bereich veroffentlicht.",
            "tr": "Klinigimizdagi songgi yangiliklar, xizmat yangilanishlari va muhim malumotlar shu bolumda beriladi.",
        },
        "news_author_fallback": {
            "uz": "Admin",
            "ru": "Админ",
            "en": "Admin",
            "de": "Admin",
            "tr": "Admin",
        },
        "news_read_more": {
            "uz": "Batafsil",
            "ru": "Подробнее",
            "en": "Read More",
            "de": "Mehr erfahren",
            "tr": "Detaylar",
        },
        "news_empty_title": {
            "uz": "Hozircha yangiliklar mavjud emas",
            "ru": "Пока нет новостей",
            "en": "There are no news items yet",
            "de": "Es gibt noch keine Nachrichten",
            "tr": "Henuz yangiliklar mavjud emas",
        },
        "news_empty_description": {
            "uz": "Tez orada bu bolimda songgi yangiliklar joylashtiriladi.",
            "ru": "В этом разделе скоро появятся последние новости.",
            "en": "The latest updates will be added to this section soon.",
            "de": "Die neuesten Meldungen werden bald in diesem Bereich erscheinen.",
            "tr": "Bu bolumda yaqinda songgi yangiliklar joylashtiriladi.",
        },
        "subscribe_title": {
            "uz": "Yangiliklarga obuna boling",
            "ru": "Подпишитесь на обновления",
            "en": "Subscribe for Updates",
            "de": "Updates abonnieren",
            "tr": "Guncellemelere abone olun",
        },
        "subscribe_intro": {
            "uz": "Klinika yangiliklari va xizmatlar boyicha songgi malumotlarni muntazam oling.",
            "ru": "Регулярно получайте последние новости клиники и обновления услуг.",
            "en": "Receive the latest clinic news and service updates on a regular basis.",
            "de": "Erhalten Sie regelmassig die neuesten Klinikmeldungen und Service-Updates.",
            "tr": "Klinika yangiliklari va xizmatlar boyicha songgi malumotlarni muntazam oling.",
        },
        "subscribe_placeholder": {
            "uz": "Email manzilingizni kiriting",
            "ru": "Введите ваш email",
            "en": "Enter your email",
            "de": "E-Mail eingeben",
            "tr": "E-posta adresinizi girin",
        },
        "subscribe_button": {
            "uz": "Obuna bolish",
            "ru": "Подписаться",
            "en": "Subscribe",
            "de": "Abonnieren",
            "tr": "Abone ol",
        },
        "partners_top_title": {
            "uz": "Hamkorlar",
            "ru": "Партнеры",
            "en": "Partners",
            "de": "Partner",
            "tr": "Partnerler",
        },
        "partners_heading": {
            "uz": "Bizning ishonchli hamkorlarimiz",
            "ru": "Наши надежные партнеры",
            "en": "Our Trusted Partners",
            "de": "Unsere zuverlassigen Partner",
            "tr": "Guvenilir partnerlerimiz",
        },
        "partners_intro": {
            "uz": "DOCTOR A MED CLINIC sifatli tibbiy xizmat korsatishda ishonchli tashkilotlar va brendlar bilan hamkorlik qiladi. Hozirda bizning ekotizimimizda {count} ta faol hamkor mavjud.",
            "ru": "DOCTOR A MED CLINIC сотрудничает с надежными организациями и брендами для качественного оказания медицинских услуг. Сейчас в нашей экосистеме {count} активных партнеров.",
            "en": "DOCTOR A MED CLINIC works with trusted organizations and brands to deliver quality medical care. Our ecosystem currently includes {count} active partners.",
            "de": "DOCTOR A MED CLINIC arbeitet mit zuverlassigen Organisationen und Marken zusammen, um hochwertige medizinische Leistungen zu bieten. Unser Okosystem umfasst derzeit {count} aktive Partner.",
            "tr": "DOCTOR A MED CLINIC sifatli tibbi xizmat korsatish uchun ishonchli tashkilot va brendlar bilan hamkorlik qiladi. Hozir ekotizimimizda {count} ta faol hamkor mavjud.",
        },
        "partners_cta": {
            "uz": "Hamkorlik uchun aloqa",
            "ru": "Связаться для партнерства",
            "en": "Contact for Partnership",
            "de": "Kontakt fur Partnerschaft",
            "tr": "Hamkorlik uchun aloqa",
        },
        "partners_site_link": {
            "uz": "Saytga otish",
            "ru": "Перейти на сайт",
            "en": "Visit Website",
            "de": "Zur Website",
            "tr": "Siteye git",
        },
        "partners_empty_title": {
            "uz": "Hamkorlar qoshilmoqda",
            "ru": "Партнеры добавляются",
            "en": "Partners are being added",
            "de": "Partner werden hinzugefugt",
            "tr": "Partnerlar qoshilmoqda",
        },
        "partners_empty_description": {
            "uz": "Bu bolimda yaqinda klinikaning rasmiy hamkorlari logotiplari va qisqa malumotlari joylashtiriladi.",
            "ru": "В этом разделе скоро появятся логотипы и краткая информация об официальных партнерах клиники.",
            "en": "Official partner logos and short profiles will be added to this section soon.",
            "de": "Offizielle Partnerlogos und kurze Informationen werden bald in diesem Bereich erscheinen.",
            "tr": "Bu bolumda yaqinda klinikaning rasmiy partnerlari logotiplari va qisqa malumotlari joylashtiriladi.",
        },
        "partner_bullets": {
            "uz": [
                "Uzoq muddatli va barqaror professional hamkorlik",
                "Sifatli tibbiy xizmatlarni kengaytiruvchi sheriklik",
                "Zamonaviy diagnostika va xizmat ekotizimi",
                "Bemorlar uchun qulay va ishonchli yonaltirish",
            ],
            "ru": [
                "Долгосрочное и стабильное профессиональное сотрудничество",
                "Партнерство, расширяющее качественные медицинские услуги",
                "Современная экосистема диагностики и сервиса",
                "Удобное и надежное направление пациентов",
            ],
            "en": [
                "Long-term and stable professional partnerships",
                "Alliances that expand quality medical services",
                "A modern diagnostics and service ecosystem",
                "Convenient and reliable patient referral routes",
            ],
            "de": [
                "Langfristige und stabile professionelle Partnerschaften",
                "Kooperationen zur Erweiterung hochwertiger medizinischer Leistungen",
                "Modernes Okosystem fur Diagnostik und Service",
                "Bequeme und verlassliche Patientenweiterleitung",
            ],
            "tr": [
                "Uzoq muddatli va barqaror professional hamkorlik",
                "Sifatli tibbi xizmatlarni kengaytiruvchi sheriklik",
                "Zamonaviy diagnostika va xizmat ekotizimi",
                "Bemorlar uchun qulay va ishonchli yonaltirish",
            ],
        },
    }

    def translate_homepage_value(self, value, language_code):
        if isinstance(value, dict):
            return value.get(language_code) or value.get("uz") or value.get("en") or ""
        return value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_lang = (get_language() or "uz").split("-")[0].lower()

        site_settings = SiteSettings.objects.first()
        context["site_settings"] = site_settings
        context["current_lang"] = current_lang

        doctors = CustomUser.objects.filter(
            is_active_employee=True,
            medical_specialty__isnull=False,
        ).exclude(
            profile_picture="",
        )[:3]
        context["doctors"] = doctors

        from apps.medical.models import Partner
        active_partners = Partner.objects.filter(is_active=True)
        context["active_partners"] = active_partners

        from apps.news.models import News
        latest_news = News.objects.filter(is_published=True).order_by("-published_date")[:3]
        context["latest_news"] = latest_news
        context["homepage_services"] = ClinicService.objects.filter(is_active=True).order_by("sort_order", "id")[:6]

        home_page = {
            key: self.translate_homepage_value(value, current_lang)
            for key, value in self.PAGE_TRANSLATIONS.items()
            if key != "partner_bullets"
        }
        home_page["partner_bullets"] = self.PAGE_TRANSLATIONS["partner_bullets"].get(
            current_lang,
            self.PAGE_TRANSLATIONS["partner_bullets"]["uz"],
        )
        home_page["partners_intro"] = home_page["partners_intro"].format(count=active_partners.count())
        context["home_page"] = home_page

        return context


class AboutStyleTwoView(TemplateView):
    template_name = "v1/about-style-two.html"

    PAGE_TRANSLATIONS = {
        "page_title": {
            "uz": "Biz haqimizda",
            "ru": "О нас",
            "en": "About Us",
            "de": "Über uns",
            "tr": "Hakkımızda",
        },
        "home_label": {
            "uz": "Bosh sahifa",
            "ru": "Главная",
            "en": "Home",
            "de": "Startseite",
            "tr": "Ana Sayfa",
        },
        "top_title": {
            "uz": "Biz haqimizda",
            "ru": "О нас",
            "en": "About Us",
            "de": "Über uns",
            "tr": "Hakkımızda",
        },
        "clinic_name": {
            "uz": "Doctor A MED CLINIC",
            "ru": "Doctor A MED CLINIC",
            "en": "Doctor A MED CLINIC",
            "de": "Doctor A MED CLINIC",
            "tr": "Doctor A MED CLINIC",
        },
        "cta_label": {
            "uz": "Aloqa",
            "ru": "Связаться",
            "en": "Contact",
            "de": "Kontakt",
            "tr": "Iletisim",
        },
        "video_title": {
            "uz": "Klinika videolari",
            "ru": "Видео клиники",
            "en": "Clinic Videos",
            "de": "Klinikvideos",
            "tr": "Klinik Videolari",
        },
    }

    SECTION_TRANSLATIONS = [
        {
            "title": {
                "uz": "Klinika haqida umumiy ma'lumot",
                "ru": "Общая информация о клинике",
                "en": "General Clinic Information",
                "de": "Allgemeine Informationen zur Klinik",
                "tr": "Klinik Hakkinda Genel Bilgi",
            },
            "intro": {
                "uz": "\"Doctor A\" — zamonaviy diagnostika va davolash uskunalari bilan jihozlangan, ko‘p tarmoqli xususiy tibbiyot markazi hisoblanadi. Klinikaning asosiy maqsadi laboratoriya va instrumental diagnostika sifatini yuqori darajaga ko‘tarishdir.",
                "ru": "\"Doctor A\" — это многопрофильный частный медицинский центр, оснащенный современным диагностическим и лечебным оборудованием. Основная цель клиники — вывести качество лабораторной и инструментальной диагностики на высокий уровень.",
                "en": "\"Doctor A\" is a multidisciplinary private medical center equipped with modern diagnostic and treatment technologies. The clinic's main goal is to elevate the quality of laboratory and instrumental diagnostics to a high standard.",
                "de": "\"Doctor A\" ist ein multidisziplinäres privates medizinisches Zentrum mit moderner Diagnostik- und Behandlungstechnik. Das Hauptziel der Klinik besteht darin, die Qualität der Labor- und instrumentellen Diagnostik auf ein hohes Niveau zu bringen.",
                "tr": "\"Doctor A\", modern tani ve tedavi ekipmanlari ile donatilmis cok yonlu bir ozel tip merkezidir. Klinigin temel amaci laboratuvar ve enstrumantal tani kalitesini yuksek seviyeye tasimaktir.",
            },
            "items": [],
        },
        {
            "title": {
                "uz": "Shifokorlar va mutaxassisliklar",
                "ru": "Врачи и специализации",
                "en": "Doctors and Specialties",
                "de": "Arzte und Fachrichtungen",
                "tr": "Doktorlar ve Uzmanliklar",
            },
            "intro": {
                "uz": "Klinikada quyidagi yo‘nalishlar bo‘yicha tajribali mutaxassislar faoliyat yuritadi:",
                "ru": "В клинике работают опытные специалисты по следующим направлениям:",
                "en": "The clinic is staffed by experienced specialists in the following areas:",
                "de": "In der Klinik arbeiten erfahrene Facharzte in folgenden Bereichen:",
                "tr": "Klinikte asagidaki alanlarda deneyimli uzmanlar faaliyet gostermektedir:",
            },
            "items": [
                {
                    "text": {
                        "uz": "Terapevt va Kardiolog",
                        "ru": "Терапевт и кардиолог",
                        "en": "Therapist and Cardiologist",
                        "de": "Therapeut und Kardiologe",
                        "tr": "Terapist ve Kardiyolog",
                    }
                },
                {
                    "text": {
                        "uz": "Nevrolog va Endokrinolog",
                        "ru": "Невролог и эндокринолог",
                        "en": "Neurologist and Endocrinologist",
                        "de": "Neurologe und Endokrinologe",
                        "tr": "Norolog ve Endokrinolog",
                    }
                },
                {
                    "text": {
                        "uz": "Ginekolog va Urolog",
                        "ru": "Гинеколог и уролог",
                        "en": "Gynecologist and Urologist",
                        "de": "Gynakologe und Urologe",
                        "tr": "Jinekolog ve Urolog",
                    }
                },
                {
                    "text": {
                        "uz": "Dermatolog va Gastroenterolog",
                        "ru": "Дерматолог и гастроэнтеролог",
                        "en": "Dermatologist and Gastroenterologist",
                        "de": "Dermatologe und Gastroenterologe",
                        "tr": "Dermatolog ve Gastroenterolog",
                    }
                },
                {
                    "text": {
                        "uz": "LOR (Otolaringolog)",
                        "ru": "ЛОР (оториноларинголог)",
                        "en": "ENT (Otolaryngologist)",
                        "de": "HNO-Arzt (Otolaryngologe)",
                        "tr": "KBB (Otorinolaringolog)",
                    }
                },
                {
                    "text": {
                        "uz": "Jarroh va Travmatolog",
                        "ru": "Хирург и травматолог",
                        "en": "Surgeon and Traumatologist",
                        "de": "Chirurg und Traumatologe",
                        "tr": "Cerrah ve Travmatolog",
                    }
                },
            ],
        },
        {
            "title": {
                "uz": "Ko'rsatiladigan xizmatlar",
                "ru": "Предоставляемые услуги",
                "en": "Services Provided",
                "de": "Angebotene Leistungen",
                "tr": "Sunulan Hizmetler",
            },
            "intro": {
                "uz": "Klinika keng qamrovli diagnostika imkoniyatlariga ega:",
                "ru": "Клиника располагает широкими возможностями диагностики:",
                "en": "The clinic offers broad diagnostic capabilities:",
                "de": "Die Klinik verfugt uber umfassende diagnostische Moglichkeiten:",
                "tr": "Klinik genis kapsamli tani imkanlarina sahiptir:",
            },
            "items": [
                {
                    "text": {
                        "uz": "MRT (Magnit-rezonans tomografiya) – 24/7 rejimida ishlaydi.",
                        "ru": "МРТ (магнитно-резонансная томография) работает в режиме 24/7.",
                        "en": "MRI (Magnetic Resonance Imaging) operates 24/7.",
                        "de": "MRT (Magnetresonanztomographie) arbeitet im 24/7-Modus.",
                        "tr": "MRG (Manyetik Rezonans Goruntuleme) 7/24 hizmet verir.",
                    }
                },
                {
                    "text": {
                        "uz": "MSKT (Multispiral kompyuter tomografiyasi) – 24/7 rejimida ishlaydi.",
                        "ru": "МСКТ (мультиспиральная компьютерная томография) работает в режиме 24/7.",
                        "en": "MSCT (Multislice Computed Tomography) operates 24/7.",
                        "de": "MSKT (Mehrschicht-Computertomographie) arbeitet im 24/7-Modus.",
                        "tr": "MSCT (Cok Kesitli Bilgisayarli Tomografi) 7/24 hizmet verir.",
                    }
                },
                {
                    "text": {
                        "uz": "UZI (Ultratovush tekshiruvi).",
                        "ru": "УЗИ (ультразвуковое исследование).",
                        "en": "Ultrasound diagnostics.",
                        "de": "Ultraschalluntersuchung.",
                        "tr": "Ultrasonografi.",
                    }
                },
                {
                    "text": {
                        "uz": "Rentgen va laborator tahlillar.",
                        "ru": "Рентген и лабораторные анализы.",
                        "en": "X-ray and laboratory analyses.",
                        "de": "Rontgen und Laboranalysen.",
                        "tr": "Rontgen ve laboratuvar tahlilleri.",
                    }
                },
                {
                    "text": {
                        "uz": "Endoskopik tekshiruvlar (FGDS va boshqalar).",
                        "ru": "Эндоскопические исследования (ФГДС и другие).",
                        "en": "Endoscopic examinations (FGDS and others).",
                        "de": "Endoskopische Untersuchungen (FGDS und weitere).",
                        "tr": "Endoskopik tetkikler (FGDS ve digerleri).",
                    }
                },
                {
                    "text": {
                        "uz": "Ambulator va jarrohlik davolash.",
                        "ru": "Амбулаторное и хирургическое лечение.",
                        "en": "Outpatient and surgical treatment.",
                        "de": "Ambulante und chirurgische Behandlung.",
                        "tr": "Ayakta ve cerrahi tedavi.",
                    }
                },
            ],
        },
        {
            "title": {
                "uz": "Manzil va mo'ljal",
                "ru": "Адрес и ориентир",
                "en": "Address and Landmark",
                "de": "Adresse und Orientierungspunkt",
                "tr": "Adres ve Konum Tarifi",
            },
            "intro": None,
            "items": [
                {
                    "label": {
                        "uz": "Manzil",
                        "ru": "Адрес",
                        "en": "Address",
                        "de": "Adresse",
                        "tr": "Adres",
                    },
                    "value": {
                        "uz": "Namangan shahri, Boburshoh ko‘chasi, 2-uy.",
                        "ru": "г. Наманган, улица Бобуршох, дом 2.",
                        "en": "2 Boburshoh Street, Namangan city.",
                        "de": "Boburshoh-Strasse 2, Namangan.",
                        "tr": "Namangan sehri, Boburshoh Caddesi 2 numara.",
                    },
                },
                {
                    "label": {
                        "uz": "Mo‘ljal",
                        "ru": "Ориентир",
                        "en": "Landmark",
                        "de": "Orientierungspunkt",
                        "tr": "Referans nokta",
                    },
                    "value": {
                        "uz": "Jahon (Lola) bozori, NamDU qoshidagi akademik litsey.",
                        "ru": "рынок «Jahon (Lola)», академический лицей при NamDU.",
                        "en": "Jahon (Lola) market, the academic lyceum near NamDU.",
                        "de": "Jahon-(Lola)-Markt, akademisches Lyzeum bei NamDU.",
                        "tr": "Jahon (Lola) pazari, NamDU yanindaki akademik lise.",
                    },
                },
                {
                    "label": {
                        "uz": "Qo‘shimcha manzil",
                        "ru": "Дополнительный адрес",
                        "en": "Additional address",
                        "de": "Zusatzliche Adresse",
                        "tr": "Ek adres",
                    },
                    "value": {
                        "uz": "Irvadon MFY, Namangan ko'chasi, 2-uy.",
                        "ru": "Ирвадон МФЙ, улица Наманган, дом 2.",
                        "en": "Irvadon neighborhood, 2 Namangan Street.",
                        "de": "MFY Irvadon, Namangan-Strasse 2.",
                        "tr": "Irvadon mahallesi, Namangan Caddesi 2 numara.",
                    },
                },
            ],
        },
        {
            "title": {
                "uz": "Aloqa ma'lumotlari",
                "ru": "Контактная информация",
                "en": "Contact Information",
                "de": "Kontaktinformationen",
                "tr": "Iletisim Bilgileri",
            },
            "intro": None,
            "items": [
                {
                    "label": {
                        "uz": "Telefon",
                        "ru": "Телефон",
                        "en": "Phone",
                        "de": "Telefon",
                        "tr": "Telefon",
                    },
                    "value": {
                        "uz": "+998-78-777-41-25 yoki +998-69-226-00-00",
                        "ru": "+998-78-777-41-25 или +998-69-226-00-00",
                        "en": "+998-78-777-41-25 or +998-69-226-00-00",
                        "de": "+998-78-777-41-25 oder +998-69-226-00-00",
                        "tr": "+998-78-777-41-25 veya +998-69-226-00-00",
                    },
                },
                {
                    "label": {
                        "uz": "Ish vaqti",
                        "ru": "Режим работы",
                        "en": "Working hours",
                        "de": "Arbeitszeiten",
                        "tr": "Calisma saatleri",
                    },
                    "value": {
                        "uz": "Dushanba – Shanba (08:00 dan 16:00/18:00 gacha).",
                        "ru": "Понедельник – суббота (с 08:00 до 16:00/18:00).",
                        "en": "Monday to Saturday (08:00 to 16:00/18:00).",
                        "de": "Montag bis Samstag (08:00 bis 16:00/18:00).",
                        "tr": "Pazartesi - Cumartesi (08:00 - 16:00/18:00).",
                    },
                },
                {
                    "label": {
                        "uz": "MRT/MSKT/Rentgen",
                        "ru": "МРТ/МСКТ/Рентген",
                        "en": "MRI/MSCT/X-ray",
                        "de": "MRT/MSKT/Rontgen",
                        "tr": "MRG/MSCT/Rontgen",
                    },
                    "value": {
                        "uz": "24/7 (Kechayu-kunduz).",
                        "ru": "24/7 (круглосуточно).",
                        "en": "24/7 (around the clock).",
                        "de": "24/7 (rund um die Uhr).",
                        "tr": "7/24 (gece gunduz).",
                    },
                },
            ],
        },
    ]

    @staticmethod
    def _translate(value, language_code):
        if not isinstance(value, dict):
            return value
        return (
                value.get(language_code)
                or value.get(language_code.split("-")[0])
                or value.get("uz")
                or next(iter(value.values()), "")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = (get_language() or "uz").split("-")[0].lower()

        sections = []
        for section in self.SECTION_TRANSLATIONS:
            localized_items = []
            for item in section.get("items", []):
                localized_items.append({
                    "text": self._translate(item.get("text"), language_code) if item.get("text") else "",
                    "label": self._translate(item.get("label"), language_code) if item.get("label") else "",
                    "value": self._translate(item.get("value"), language_code) if item.get("value") else "",
                })

            sections.append({
                "title": self._translate(section.get("title"), language_code),
                "intro": self._translate(section.get("intro"), language_code),
                "items": localized_items,
            })

        context["about_page"] = {
            "page_title": self._translate(self.PAGE_TRANSLATIONS["page_title"], language_code),
            "home_label": self._translate(self.PAGE_TRANSLATIONS["home_label"], language_code),
            "top_title": self._translate(self.PAGE_TRANSLATIONS["top_title"], language_code),
            "clinic_name": self._translate(self.PAGE_TRANSLATIONS["clinic_name"], language_code),
            "cta_label": self._translate(self.PAGE_TRANSLATIONS["cta_label"], language_code),
            "video_title": self._translate(self.PAGE_TRANSLATIONS["video_title"], language_code),
            "sections": sections,
        }
        return context


class ServicesOverviewView(TemplateView):
    template_name = "v1/services-overview.html"
    PAGE_TRANSLATIONS = {
        "page_title": {
            "uz": "Xizmatlar",
            "ru": "Услуги",
            "en": "Services",
            "de": "Leistungen",
            "tr": "Hizmetler",
        },
        "section_top_title": {
            "uz": "Bizning xizmatlar",
            "ru": "Наши услуги",
            "en": "Our Services",
            "de": "Unsere Leistungen",
            "tr": "Hizmetlerimiz",
        },
        "section_heading_lead": {
            "uz": "Bizning tibbiy",
            "ru": "Наши медицинские",
            "en": "Our Healthcare",
            "de": "Unsere medizinischen",
            "tr": "Tibbi",
        },
        "section_heading_highlight": {
            "uz": "xizmatlarimiz",
            "ru": "услуги",
            "en": "Services",
            "de": "Leistungen",
            "tr": "hizmetlerimiz",
        },
        "section_intro": {
            "uz": "Klinikamiz xizmatlari konsultatsiya, diagnostika, davolash rejalashtirish va keyingi nazorat bosqichlarini yagona oqimda birlashtiradi. Har bir yo'nalish bemorga aniq yo'l-yo'riq, o'z vaqtida mutaxassis ko'rigi va tiklanishgacha zarur tibbiy yordamni taqdim etish uchun tashkil etilgan.",
            "ru": "Услуги нашей клиники объединяют консультацию, диагностику, планирование лечения и последующее наблюдение в едином процессе. Каждое направление организовано так, чтобы пациент получал понятный маршрут, своевременный доступ к специалисту и необходимую медицинскую поддержку до полного восстановления.",
            "en": "Our healthcare services bring consultation, diagnostics, treatment planning, and follow-up into one coordinated care flow. Each department is designed to give patients clear direction, timely specialist access, and the clinical support needed from first visit to recovery.",
            "de": "Unsere Leistungen verbinden Beratung, Diagnostik, Behandlungsplanung und Nachsorge in einem koordinierten Ablauf. Jede Fachrichtung ist so aufgebaut, dass Patienten klare Orientierung, schnellen Zugang zu Spezialisten und die notwendige medizinische Begleitung bis zur Genesung erhalten.",
            "tr": "Klinik hizmetlerimiz muayene, tani, tedavi planlamasi ve takip surecini tek bir duzenli akista birlestirir. Her bolum hastaya acik yonlendirme, zamaninda uzman destegi ve iyilesmeye kadar gerekli tibbi yardimi sunacak sekilde yapilanmistir.",
        },
        "empty_title": {
            "uz": "Xizmatlar hali qo'shilmagan",
            "ru": "Услуги пока не добавлены",
            "en": "Services have not been added yet",
            "de": "Es wurden noch keine Leistungen hinzugefugt",
            "tr": "Hizmetler henuz eklenmedi",
        },
        "empty_description": {
            "uz": "Bu bo'limdagi ma'lumotlar tez orada yangilanadi.",
            "ru": "Информация в этом разделе будет обновлена в ближайшее время.",
            "en": "This section will be updated with service information soon.",
            "de": "Dieser Bereich wird in Kurze mit Leistungsinformationen aktualisiert.",
            "tr": "Bu bolum yakinda hizmet bilgileri ile guncellenecektir.",
        },
    }
    service_features = [
        {
            "icon": "flaticon-doctor",
            "title": "Specialist-Led Care",
            "summary": "Each service line is guided by qualified clinicians with defined referral and review steps.",
            "link_name": "landing-v1-doctors",
            "link_label": "Meet Doctors",
        },
        {
            "icon": "flaticon-personal-information",
            "title": "Structured Service Flow",
            "summary": "Consultation, diagnostics, treatment, and follow-up are organized to reduce patient confusion.",
            "link_name": "landing-v1-announcements",
            "link_label": "View Updates",
        },
        {
            "icon": "flaticon-rate",
            "title": "Continuous Quality Review",
            "summary": "Services are refined through ongoing operational review, patient feedback, and internal control.",
            "link_name": "landing-v1-blog",
            "link_label": "Read Blog",
        },
        {
            "icon": "flaticon-first-aid-kit",
            "title": "Diagnostic Support",
            "summary": "Modern clinical equipment supports faster screening, better monitoring, and clearer treatment decisions.",
            "link_name": "landing-v1-equipment",
            "link_label": "See Equipment",
        },
    ]
    service_points = [
        "Initial consultation and triage based on the patient’s condition",
        "Diagnostic review with appropriate specialist coordination",
        "Treatment planning with clear follow-up recommendations",
        "Ongoing observation for recovery, prevention, and long-term care",
    ]

    @staticmethod
    def _translate(value, language_code):
        if not isinstance(value, dict):
            return value
        return (
            value.get(language_code)
            or value.get(language_code.split("-")[0])
            or value.get("uz")
            or next(iter(value.values()), "")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_lang = (get_language() or "uz").split("-")[0].lower()
        context.update({
            "current_lang": current_lang,
            "service_cards": ClinicService.objects.filter(is_active=True).order_by("sort_order", "id"),
            "services_page": {
                key: self._translate(value, current_lang)
                for key, value in self.PAGE_TRANSLATIONS.items()
            },
            "service_features": self.service_features,
            "service_points": self.service_points,
        })
        return context


class VideosLandingView(TemplateView):
    template_name = "v1/videos.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("q", "").strip()
        language_code = (get_language() or "uz").split("-")[0].lower()

        videos = list(Video.objects.filter(is_active=True).order_by("-created_at"))

        if search_query:
            search_term = search_query.lower()
            videos = [
                video for video in videos
                if search_term in video.get_title(language_code).lower()
                   or search_term in video.embed_url.lower()
            ]

        paginator = Paginator(videos, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        translations = {
            "page_title": {
                "uz": "Videolar",
                "en": "Videos",
                "ru": "Видео",
            },
            "home_label": {
                "uz": "Bosh sahifa",
                "en": "Home",
                "ru": "Главная",
            },
            "section_top_title": {
                "uz": "Media kutubxona",
                "en": "Media Library",
                "ru": "Медиатека",
            },
            "section_heading": {
                "uz": "Klinika videolari",
                "en": "Clinic Videos",
                "ru": "Видео клиники",
            },
            "section_description": {
                "uz": "Doctor A klinikasiga oid videolar, intervyular va foydali tibbiy lavhalarni bir joyda ko'ring.",
                "en": "Explore clinic videos, interviews, and useful medical content in one curated library.",
                "ru": "Смотрите видео клиники, интервью и полезные медицинские материалы в одной медиатеке.",
            },
            "search_placeholder": {
                "uz": "Videolardan qidiring...",
                "en": "Search videos...",
                "ru": "Поиск видео...",
            },
            "video_label": {
                "uz": "Video",
                "en": "Video",
                "ru": "Видео",
            },
            "play_now": {
                "uz": "Ko'rish",
                "en": "Play",
                "ru": "Смотреть",
            },
            "watch_youtube": {
                "uz": "YouTube'da ochish",
                "en": "Open on YouTube",
                "ru": "Открыть на YouTube",
            },
            "empty_title": {
                "uz": "Videolar topilmadi",
                "en": "No videos found",
                "ru": "Видео не найдены",
            },
            "empty_description": {
                "uz": "Hozircha bu qidiruv bo'yicha faol video mavjud emas.",
                "en": "There are no active videos for this search at the moment.",
                "ru": "По этому запросу пока нет активных видео.",
            },
            "modal_close": {
                "uz": "Yopish",
                "en": "Close",
                "ru": "Закрыть",
            },
        }

        context.update({
            "videos": page_obj.object_list,
            "page_obj": page_obj,
            "search_query": search_query,
            "videos_page": {key: value.get(language_code, value.get("en")) for key, value in translations.items()},
        })
        return context


class NewsLandingMixin:
    PAGE_TRANSLATIONS = {
        "page_title": {
            "uz": "Yangiliklar",
            "ru": "Новости",
            "en": "News",
            "de": "Nachrichten",
            "tr": "Haberler",
        },
        "home_label": {
            "uz": "Bosh sahifa",
            "ru": "Главная",
            "en": "Home",
            "de": "Startseite",
            "tr": "Ana Sayfa",
        },
        "section_top_title": {
            "uz": "Yangiliklar",
            "ru": "Новости",
            "en": "News",
            "de": "Nachrichten",
            "tr": "Haberler",
        },
        "section_heading": {
            "uz": "So'nggi yangiliklar",
            "ru": "Последние новости",
            "en": "Latest News",
            "de": "Aktuelle Nachrichten",
            "tr": "Son Haberler",
        },
        "section_description": {
            "uz": "Klinikamizdagi so'nggi yangiliklar, xizmatlar yangilanishi va muhim ma'lumotlar shu bo'limda joylashtiriladi.",
            "ru": "В этом разделе публикуются последние новости клиники, обновления услуг и важная информация.",
            "en": "This section publishes the latest clinic news, service updates, and important information.",
            "de": "In diesem Bereich werden aktuelle Kliniknachrichten, Service-Updates und wichtige Informationen veröffentlicht.",
            "tr": "Bu bölümde kliniğin son haberleri, hizmet güncellemeleri ve önemli bilgiler yayımlanır.",
        },
        "search_placeholder": {
            "uz": "Yangiliklardan qidiring...",
            "ru": "Поиск по новостям...",
            "en": "Search news...",
            "de": "Nachrichten durchsuchen...",
            "tr": "Haberlerde ara...",
        },
        "recent_posts_title": {
            "uz": "So'nggi yangiliklar",
            "ru": "Последние новости",
            "en": "Recent News",
            "de": "Neueste Nachrichten",
            "tr": "Son Haberler",
        },
        "archives_title": {
            "uz": "Arxiv",
            "ru": "Архив",
            "en": "Archive",
            "de": "Archiv",
            "tr": "Arşiv",
        },
        "topics_title": {
            "uz": "Mavzular",
            "ru": "Темы",
            "en": "Topics",
            "de": "Themen",
            "tr": "Konular",
        },
        "read_more": {
            "uz": "Batafsil",
            "ru": "Подробнее",
            "en": "Read More",
            "de": "Mehr erfahren",
            "tr": "Detaylar",
        },
        "empty_title": {
            "uz": "Hozircha yangilik topilmadi",
            "ru": "Новости пока не найдены",
            "en": "No news found yet",
            "de": "Noch keine Nachrichten gefunden",
            "tr": "Henüz haber bulunamadı",
        },
        "empty_description": {
            "uz": "Boshqa qidiruv so'zini sinab ko'ring yoki tanlangan filtrlarni tozalang.",
            "ru": "Попробуйте другой поисковый запрос или очистите выбранные фильтры.",
            "en": "Try another search term or clear the selected filters.",
            "de": "Versuchen Sie einen anderen Suchbegriff oder löschen Sie die gewählten Filter.",
            "tr": "Başka bir arama ifadesi deneyin veya seçili filtreleri temizleyin.",
        },
        "author_fallback": {
            "uz": "Doctor A",
            "ru": "Doctor A",
            "en": "Doctor A",
            "de": "Doctor A",
            "tr": "Doctor A",
        },
        "published_label": {
            "uz": "Sana",
            "ru": "Дата",
            "en": "Date",
            "de": "Datum",
            "tr": "Tarih",
        },
        "views_label": {
            "uz": "Ko'rishlar",
            "ru": "Просмотры",
            "en": "Views",
            "de": "Aufrufe",
            "tr": "Görüntülenme",
        },
        "back_to_news": {
            "uz": "Barcha yangiliklar",
            "ru": "Все новости",
            "en": "All News",
            "de": "Alle Nachrichten",
            "tr": "Tüm Haberler",
        },
        "comments_title": {
            "uz": "Izohlar",
            "ru": "Комментарии",
            "en": "Comments",
            "de": "Kommentare",
            "tr": "Yorumlar",
        },
        "leave_comment_title": {
            "uz": "Izoh qoldirish",
            "ru": "Оставить комментарий",
            "en": "Leave a Comment",
            "de": "Kommentar hinterlassen",
            "tr": "Yorum Bırakın",
        },
        "no_comments": {
            "uz": "Hozircha izohlar yo'q. Birinchi bo'lib izoh qoldiring.",
            "ru": "Комментариев пока нет. Оставьте первый комментарий.",
            "en": "No comments yet. Be the first to leave one.",
            "de": "Noch keine Kommentare. Hinterlassen Sie den ersten Kommentar.",
            "tr": "Henüz yorum yok. İlk yorumu siz bırakın.",
        },
        "comment_success": {
            "uz": "Izoh muvaffaqiyatli qo'shildi.",
            "ru": "Комментарий успешно добавлен.",
            "en": "Your comment was added successfully.",
            "de": "Ihr Kommentar wurde erfolgreich hinzugefügt.",
            "tr": "Yorumunuz başarıyla eklendi.",
        },
        "comment_error": {
            "uz": "Iltimos, barcha maydonlarni to'ldiring.",
            "ru": "Пожалуйста, заполните все поля.",
            "en": "Please fill in all fields.",
            "de": "Bitte füllen Sie alle Felder aus.",
            "tr": "Lütfen tüm alanları doldurun.",
        },
        "name_placeholder": {
            "uz": "To'liq ism",
            "ru": "Полное имя",
            "en": "Full name",
            "de": "Vollständiger Name",
            "tr": "Ad Soyad",
        },
        "phone_placeholder": {
            "uz": "Telefon raqam",
            "ru": "Номер телефона",
            "en": "Phone number",
            "de": "Telefonnummer",
            "tr": "Telefon numarası",
        },
        "message_placeholder": {
            "uz": "Izohingizni yozing",
            "ru": "Напишите ваш комментарий",
            "en": "Write your comment",
            "de": "Schreiben Sie Ihren Kommentar",
            "tr": "Yorumunuzu yazın",
        },
        "submit_comment": {
            "uz": "Yuborish",
            "ru": "Отправить",
            "en": "Submit",
            "de": "Senden",
            "tr": "Gönder",
        },
    }
    TOPIC_TRANSLATIONS = {
        "uz": ["Klinika", "Diagnostika", "Laboratoriya", "Shifokorlar", "Yangilanishlar"],
        "ru": ["Клиника", "Диагностика", "Лаборатория", "Врачи", "Обновления"],
        "en": ["Clinic", "Diagnostics", "Laboratory", "Doctors", "Updates"],
        "de": ["Klinik", "Diagnostik", "Labor", "Ärzte", "Updates"],
        "tr": ["Klinik", "Tanı", "Laboratuvar", "Doktorlar", "Güncellemeler"],
    }
    MONTH_TRANSLATIONS = {
        "uz": {
            1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
            7: "Iyul", 8: "Avgust", 9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr",
        },
        "ru": {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
            7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
        },
        "en": {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
        },
        "de": {
            1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
            7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
        },
        "tr": {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
            7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
        },
    }

    def get_language_code(self):
        return (get_language() or "uz").split("-")[0].lower()

    def get_translated_text(self, key, language_code):
        values = self.PAGE_TRANSLATIONS.get(key, {})
        return values.get(language_code) or values.get("uz") or key

    def get_page_copy(self, language_code):
        return {
            key: self.get_translated_text(key, language_code)
            for key in self.PAGE_TRANSLATIONS
        }

    def get_topic_tags(self, language_code):
        return self.TOPIC_TRANSLATIONS.get(language_code) or self.TOPIC_TRANSLATIONS["uz"]

    def get_news_queryset(self):
        return News.objects.filter(is_published=True).select_related("author").order_by("-published_date")

    def apply_search_filters(self, queryset, search_query, month_query):
        filtered_queryset = queryset
        language_code = self.get_language_code()

        if search_query:
            filtered_queryset = filtered_queryset.filter(
                Q(**{f"title__{language_code}__icontains": search_query})
                | Q(**{f"content__{language_code}__icontains": search_query})
                | Q(author__full_name__icontains=search_query)
                | Q(author__username__icontains=search_query)
            )

        if month_query:
            try:
                year_value, month_value = month_query.split("-", 1)
                filtered_queryset = filtered_queryset.filter(
                    published_date__year=int(year_value),
                    published_date__month=int(month_value),
                )
            except (TypeError, ValueError):
                pass

        return filtered_queryset

    def get_archive_items(self, queryset, language_code):
        archive_counts = (
            queryset.values("published_date__year", "published_date__month")
            .annotate(count=Count("id"))
            .order_by("-published_date__year", "-published_date__month")
        )

        month_labels = self.MONTH_TRANSLATIONS.get(language_code) or self.MONTH_TRANSLATIONS["uz"]
        archives = []
        for item in archive_counts:
            month_number = item["published_date__month"]
            year_number = item["published_date__year"]
            archives.append({
                "value": f"{year_number:04d}-{month_number:02d}",
                "label": f"{month_labels.get(month_number, month_number)} {year_number}",
                "count": item["count"],
            })
        return archives


class BlogRightSidebarView(NewsLandingMixin, TemplateView):
    template_name = "v1/blog-right-sidebar.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = self.get_language_code()
        search_query = self.request.GET.get("q", "").strip()
        month_query = self.request.GET.get("month", "").strip()

        all_news = self.get_news_queryset()
        filtered_news = self.apply_search_filters(all_news, search_query, month_query)
        page_obj = Paginator(filtered_news, self.paginate_by).get_page(self.request.GET.get("page", 1))

        context.update({
            "news_page": self.get_page_copy(language_code),
            "search_query": search_query,
            "month_query": month_query,
            "page_obj": page_obj,
            "news_items": page_obj.object_list,
            "recent_news": all_news[:4],
            "news_archives": self.get_archive_items(all_news, language_code),
        })
        return context


class NewsLandingDetailView(NewsLandingMixin, DetailView):
    template_name = "v1/news-details.html"
    context_object_name = "news_item"
    model = News

    def get_queryset(self):
        return self.get_news_queryset()

    def _get_news_for_post(self):
        return self.get_queryset().get(pk=self.kwargs["pk"])

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count = models.F("views_count") + 1
        obj.save(update_fields=["views_count"])
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = self.get_language_code()
        all_news = self.get_news_queryset()
        comments = self.object.comments.all().order_by("-created_at")

        context.update({
            "news_page": self.get_page_copy(language_code),
            "recent_news": all_news.exclude(pk=self.object.pk)[:4],
            "news_archives": self.get_archive_items(all_news, language_code),
            "comments": comments,
            "comments_count": comments.count(),
            "comment_success": self.request.GET.get("comment") == "success",
            "comment_error": kwargs.get("comment_error"),
            "comment_form_data": kwargs.get("comment_form_data", {}),
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self._get_news_for_post()
        language_code = self.get_language_code()
        author = request.POST.get("author", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        comment_text = request.POST.get("comment", "").strip()

        if author and phone_number and comment_text:
            Comment.objects.create(
                news=self.object,
                full_name=author,
                phone_number=phone_number,
                text=comment_text,
            )
            return redirect(f"{request.path}?comment=success#comments")

        context = self.get_context_data(
            comment_error=self.get_translated_text("comment_error", language_code),
            comment_form_data={
                "author": author,
                "phone_number": phone_number,
                "comment": comment_text,
            },
        )
        return self.render_to_response(context)


class AnnouncementLandingMixin(NewsLandingMixin):
    PAGE_TRANSLATIONS = {
        **NewsLandingMixin.PAGE_TRANSLATIONS,
        "page_title": {
            "uz": "E'lonlar",
            "ru": "Объявления",
            "en": "Announcements",
            "de": "Ankündigungen",
            "tr": "Duyurular",
        },
        "section_top_title": {
            "uz": "E'lonlar",
            "ru": "Объявления",
            "en": "Announcements",
            "de": "Ankündigungen",
            "tr": "Duyurular",
        },
        "section_heading": {
            "uz": "So'nggi e'lonlar",
            "ru": "Последние объявления",
            "en": "Latest Announcements",
            "de": "Aktuelle Ankündigungen",
            "tr": "Son Duyurular",
        },
        "section_description": {
            "uz": "Klinikamizdagi so'nggi e'lonlar, xizmatlar yangilanishi va muhim bildirishnomalar shu bo'limda joylashtiriladi.",
            "ru": "В этом разделе публикуются последние объявления клиники, обновления услуг и важные уведомления.",
            "en": "This section publishes the latest clinic announcements, service updates, and important notifications.",
            "de": "In diesem Bereich werden aktuelle Klinikankündigungen, Service-Updates und wichtige Benachrichtigungen veröffentlicht.",
            "tr": "Bu bölümde kliniğin son duyuruları, hizmet güncellemeleri ve önemli bildirimler yayımlanır.",
        },
        "recent_posts_title": {
            "uz": "Oxirgi e'lonlar",
            "ru": "Последние объявления",
            "en": "Recent Announcements",
            "de": "Aktuelle Ankündigungen",
            "tr": "Son Duyurular",
        },
        "search_placeholder": {
            "uz": "E'lonlarni qidirish...",
            "ru": "Поиск объявлений...",
            "en": "Search announcements...",
            "de": "Ankündigungen suchen...",
            "tr": "Duyuruları ara...",
        },
        "back_to_news": {
            "uz": "Barcha e'lonlar",
            "ru": "Все объявления",
            "en": "All Announcements",
            "de": "Alle Ankündigungen",
            "tr": "Tüm Duyurular",
        },
        "empty_title": {
            "uz": "E'lonlar topilmadi",
            "ru": "Объявления не найдены",
            "en": "No announcements found",
            "de": "Keine Ankündigungen gefunden",
            "tr": "Duyuru bulunamadı",
        },
    }


class AnnouncementRightSidebarView(AnnouncementLandingMixin, TemplateView):
    template_name = "v1/announcements-right-sidebar.html"
    paginate_by = 6
    announcement_image_urls = [
        "https://medic.mhrtheme.com/wp-content/uploads/2021/10/blog-1.jpg",
        "https://medic.mhrtheme.com/wp-content/uploads/2021/10/blog-2.jpg",
        "https://medic.mhrtheme.com/wp-content/uploads/2021/10/blog-3.jpg",
        "https://medic.mhrtheme.com/wp-content/uploads/2021/10/blog-4.jpg",
        "https://medic.mhrtheme.com/wp-content/uploads/2021/09/blog-5.jpg",
        "https://medic.mhrtheme.com/wp-content/uploads/2021/08/blog-6.jpg",
    ]
    fallback_announcements = [
        {
            "title": "Clinic Schedule Update",
            "summary": "Revised outpatient reception hours and service windows for the upcoming month.",
            "published_date": date(2026, 4, 12),
            "author_name": "Admin",
        },
        {
            "title": "Laboratory Service Notice",
            "summary": "Morning sample collection capacity has been expanded to reduce patient waiting time.",
            "published_date": date(2026, 4, 8),
            "author_name": "Admin",
        },
        {
            "title": "New Specialist Availability",
            "summary": "Additional consultation slots are now open for cardiology and diagnostic imaging departments.",
            "published_date": date(2026, 4, 3),
            "author_name": "Admin",
        },
    ]

    def _serialize_announcement(self, announcement, index, language_code):
        title = announcement.title.get(language_code) or announcement.title.get("uz") or "Announcement"
        content = announcement.content.get(language_code) or announcement.content.get("uz") or ""
        author_name = "Admin"
        if announcement.author:
            author_name = getattr(announcement.author, "full_name", "") or getattr(announcement.author, "username",
                                                                                   "Admin")

        return {
            "id": announcement.id,
            "title": title,
            "summary": strip_tags(content),
            "published_date": announcement.published_date,
            "author_name": author_name,
            "image_url": self.announcement_image_urls[index % len(self.announcement_image_urls)],
        }

    def _build_announcement_items(self, language_code):
        queryset = Announcement.objects.filter(is_published=True).select_related("author").order_by("-published_date")
        items = [
            self._serialize_announcement(announcement, index, language_code)
            for index, announcement in enumerate(queryset)
        ]

        if items:
            return items

        fallback_items = []
        for index, item in enumerate(self.fallback_announcements):
            fallback_items.append({
                **item,
                "image_url": self.announcement_image_urls[index % len(self.announcement_image_urls)],
            })
        return fallback_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = self.get_language_code()
        search_query = self.request.GET.get("q", "").strip()
        month_query = self.request.GET.get("month", "").strip()

        all_announcements = self._build_announcement_items(language_code)
        filtered_announcements = all_announcements

        if search_query:
            search_term = search_query.lower()
            filtered_announcements = [
                item for item in filtered_announcements
                if search_term in item["title"].lower()
                   or search_term in item["summary"].lower()
                   or search_term in item["author_name"].lower()
            ]

        if month_query:
            filtered_announcements = [
                item for item in filtered_announcements
                if item["published_date"].strftime("%Y-%m") == month_query
            ]

        paginator = Paginator(filtered_announcements, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        archive_counter = Counter(item["published_date"].strftime("%B %Y") for item in all_announcements)
        archives = []
        seen_archives = set()
        for item in all_announcements:
            archive_value = item["published_date"].strftime("%Y-%m")
            archive_label = item["published_date"].strftime("%B %Y")
            if archive_value in seen_archives:
                continue
            seen_archives.add(archive_value)
            archives.append({
                "value": archive_value,
                "label": archive_label,
                "count": archive_counter[archive_label],
            })

        context.update({
            "news_page": self.get_page_copy(language_code),
            "search_query": search_query,
            "month_query": month_query,
            "page_obj": page_obj,
            "announcements": page_obj.object_list,
            "latest_announcements": all_announcements[:4],
            "announcement_archives": archives,
            "announcement_tags": self.get_topic_tags(language_code),
        })
        return context


class AnnouncementLandingDetailView(AnnouncementLandingMixin, DetailView):
    template_name = "v1/announcements-details.html"
    context_object_name = "announcement"
    model = Announcement

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True).select_related("author")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count = models.F("views_count") + 1
        obj.save(update_fields=["views_count"])
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = self.get_language_code()

        # Build sidebar data using same logic as list view
        sidebar_view = AnnouncementRightSidebarView()
        sidebar_view.request = self.request
        all_announcements = sidebar_view._build_announcement_items(language_code)

        archive_counter = Counter(item["published_date"].strftime("%B %Y") for item in all_announcements)
        archives = []
        seen_archives = set()
        for item in all_announcements:
            archive_value = item["published_date"].strftime("%Y-%m")
            archive_label = item["published_date"].strftime("%B %Y")
            if archive_value in seen_archives:
                continue
            seen_archives.add(archive_value)
            archives.append({
                "value": archive_value,
                "label": archive_label,
                "count": archive_counter[archive_label],
            })

        # We also need to get localized title and content for this announcement
        context.update({
            "news_page": self.get_page_copy(language_code),
            "latest_announcements": all_announcements[:4],
            "announcement_archives": archives,
            "announcement_tags": self.get_topic_tags(language_code),
            "language_code": language_code,
            # Pass a serialized version of self for easy templating
            "serialized_announcement": sidebar_view._serialize_announcement(self.object, self.object.id or 0,
                                                                            language_code),
            "announcement_content": self.object.content.get(language_code) or self.object.content.get("uz") or ""
        })
        return context


class DoctorGridView(TemplateView):
    template_name = "v1/doctor-grid.html"
    paginate_by = 9

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language().split('-')[0]

        # Faol shifokorlarni olish (superadminlarni chiqarib tashlash)
        doctors_query = CustomUser.objects.filter(
            is_active_employee=True,
            is_superuser=False,
            medical_specialty__isnull=False
        ).exclude(medical_specialty='').order_by('full_name')

        # Pagination
        paginator = Paginator(doctors_query, self.paginate_by)
        page_number = self.request.GET.get('page')
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)

        # Static translations
        translations = {
            "page_title": {
                "uz": "Shifokorlar",
                "en": "Doctors",
                "ru": "Врачи",
            },
            "home": {
                "uz": "Bosh sahifa",
                "en": "Home",
                "ru": "Главная",
            },
            "doctors_title": {
                "uz": "Bizning tajribali shifokorlarimiz",
                "en": "Our Experienced Doctors",
                "ru": "Наши опытные врачи",
            },
            "doctors_desc": {
                "uz": "Sizning sog'lig'ingiz uchun o'z sohasining mutaxassislari xizmat qiladi.",
                "en": "Experts in their fields are at your service for your health.",
                "ru": "Специалисты в своих областях к вашим услугам для вашего здоровья.",
            },
            "view_profile": {
                "uz": "Profilni ko'rish",
                "en": "View Profile",
                "ru": "Посмотреть профиль",
            },
            "no_doctors": {
                "uz": "Hozircha shifokorlar haqida ma'lumot mavjud emas.",
                "en": "No information about doctors is available at the moment.",
                "ru": "Информация о врачах на данный moment отсутствует.",
            }
        }

        context['t'] = {k: v.get(language_code, v['en']) for k, v in translations.items()}

        # Prepare doctors data with image logic
        default_doctor_img = settings.STATIC_URL + "medic/img/doctors/user.jpeg"
        doctors_data = []
        for doctor in page_obj.object_list:
            image_url = doctor.profile_picture.url if doctor.profile_picture else default_doctor_img
            doctors_data.append({
                "id": doctor.id,
                "full_name": doctor.full_name,
                "medical_specialty": doctor.medical_specialty,
                "image_url": image_url,
                "telegram_username": (doctor.telegram_username or "").lstrip("@"),
                "instagram_username": (doctor.instagram_username or "").lstrip("@"),
                "phone_number": doctor.phone_number or "",
            })

        context['page_obj'] = page_obj
        context['doctors'] = doctors_data
        return context


class DoctorLandingDetailView(DetailView):
    model = CustomUser
    template_name = "v1/doctor-details.html"
    context_object_name = "doctor"

    def get_queryset(self):
        return CustomUser.objects.filter(is_active_employee=True, is_superuser=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language().split('-')[0]
        doctor = self.object
        clean_bio_html = doctor.get_clean_bio()
        clean_bio_text = strip_tags(clean_bio_html).replace("\xa0", " ").strip()
        biography_excerpt = clean_bio_text
        if len(biography_excerpt) > 260:
            biography_excerpt = biography_excerpt[:260].rsplit(" ", 1)[0] + "..."
        telegram_username = (doctor.telegram_username or "").lstrip("@")
        instagram_username = (doctor.instagram_username or "").lstrip("@")

        # Static translations
        translations = {
            "home": {"uz": "Bosh sahifa", "en": "Home", "ru": "Главная"},
            "doctors": {"uz": "Shifokorlar", "en": "Doctors", "ru": "Врачи"},
            "contact_info": {"uz": "Bog'lanish", "en": "Contact Info", "ru": "Контактная информация"},
            "specialty": {"uz": "Mutaxassisligi", "en": "Specialty", "ru": "Специальность"},
            "experience": {"uz": "Tajriba", "en": "Experience", "ru": "Опыт"},
            "education": {"uz": "Ma'lumoti", "en": "Education", "ru": "Образование"},
            "biography": {"uz": "Biografiya", "en": "Biography", "ru": "Биография"},
            "position": {"uz": "Lavozim", "en": "Position", "ru": "Должность"},
            "phone": {"uz": "Telefon", "en": "Phone", "ru": "Телефон"},
            "birth_date": {"uz": "Tug'ilgan sana", "en": "Birth Date", "ru": "Дата рождения"},
            "license": {"uz": "Diplom", "en": "License", "ru": "Диплом"},
            "schedule": {"uz": "Ish jadvali", "en": "Schedule", "ru": "График работы"},
            "telegram": {"uz": "Telegram", "en": "Telegram", "ru": "Telegram"},
            "instagram": {"uz": "Instagram", "en": "Instagram", "ru": "Instagram"},
            "department": {"uz": "Bo'lim", "en": "Department", "ru": "Отдел"},
            "employment_date": {"uz": "Ish boshlagan sana", "en": "Employment Date", "ru": "Дата начала работы"},
            "address": {"uz": "Manzil", "en": "Address", "ru": "Адрес"},
            "email": {"uz": "Elektron pochta", "en": "Email", "ru": "Электронная почта"},
            "employee_id": {"uz": "Xodim ID", "en": "Employee ID", "ru": "ID сотрудника"},
            "activity_history": {"uz": "Faoliyat tarixi", "en": "Activity History", "ru": "История деятельности"},
            "overview": {"uz": "Hodim haqida", "en": "About the Specialist", "ru": "О сотруднике"},
            "social_profiles": {"uz": "Ijtimoiy tarmoqlar", "en": "Social Profiles", "ru": "Социальные сети"},
            "no_bio": {"uz": "Biografiya mavjud emas", "en": "Biography is not available",
                       "ru": "Биография недоступна"},
            "no_activity": {"uz": "Faoliyat tarixi mavjud emas", "en": "No activity history available",
                            "ru": "История деятельности отсутствует"},
            "not_set": {"uz": "Belgilanmagan", "en": "Not specified", "ru": "Не указано"},
            "not_available": {"uz": "Mavjud emas", "en": "Unavailable", "ru": "Недоступно"},
            "none_value": {"uz": "Yo'q", "en": "None", "ru": "Нет"},
            "completed": {"uz": "Yakunlangan", "en": "Completed", "ru": "Завершено"},
            "ongoing": {"uz": "Davom etmoqda", "en": "Ongoing", "ru": "Продолжается"},
            "result": {"uz": "Natija", "en": "Result", "ru": "Результат"},
            "certificate": {"uz": "Sertifikat", "en": "Certificate", "ru": "Сертификат"},
            "attachment": {"uz": "Fayl", "en": "Attachment", "ru": "Файл"},
            "contact_button": {"uz": "Bog'lanish", "en": "Contact", "ru": "Связаться"},
            "back_to_doctors": {"uz": "Shifokorlarga qaytish", "en": "Back to Doctors", "ru": "Назад к врачам"},
            "summary_fallback": {
                "uz": "Mutaxassis haqida asosiy ma'lumotlar, aloqa vositalari va faoliyat tarixi shu sahifada jamlangan.",
                "en": "Key profile information, contact details, and activity history are collected on this page.",
                "ru": "Основная информация, контакты и история деятельности собраны на этой странице.",
            },
        }

        context['t'] = {k: v.get(language_code, v['en']) for k, v in translations.items()}

        # Image logic
        default_doctor_img = settings.STATIC_URL + "medic/img/doctors/user.jpeg"
        context['doctor_image'] = doctor.profile_picture.url if doctor.profile_picture else default_doctor_img

        # Bio data (experience and education)
        context['bio_data'] = doctor.get_bio()
        context['clean_bio_html'] = clean_bio_html
        context['biography_excerpt'] = biography_excerpt or context['t']['summary_fallback']
        context['telegram_username'] = telegram_username
        context['instagram_username'] = instagram_username
        context['activity_history'] = doctor.activity_history.order_by("-start_date", "-id")

        return context


EQUIPMENT_CATEGORY_RULES = [
    {
        "key": "imaging",
        "label": {
            "uz": "Tasvirlash",
            "en": "Imaging",
            "ru": "Визуализация",
            "de": "Bildgebung",
            "tr": "Goruntuleme",
        },
        "capability": {
            "uz": "Tomografiya va yuqori aniqlikdagi tasvirlash",
            "en": "Tomography and high-resolution imaging",
            "ru": "Томография и визуализация высокого разрешения",
            "de": "Tomographie und hochauflosende Bildgebung",
            "tr": "Tomografi ve yuksek cozunurluklu goruntuleme",
        },
        "highlight": {
            "uz": "%(name)s bilan kengaytirilgan tasvirlash",
            "en": "Advanced imaging with %(name)s",
            "ru": "Расширенная визуализация с %(name)s",
            "de": "Erweiterte Bildgebung mit %(name)s",
            "tr": "%(name)s ile gelismis goruntuleme",
        },
        "keywords": [
            "mri", "mrt", "ct", "kt", "mskt", "tomograf", "tomography", "scan",
            "рентген", "rentgen", "x-ray", "xray", "radiology", "radiograf",
            "магнит", "мрт", "мскт", "рентген", "рентгенография",
        ],
    },
    {
        "key": "diagnostics",
        "label": {
            "uz": "Diagnostika",
            "en": "Diagnostics",
            "ru": "Диагностика",
            "de": "Diagnostik",
            "tr": "Diagnostik",
        },
        "capability": {
            "uz": "Skrining va funktsional diagnostika",
            "en": "Screening and functional diagnostics",
            "ru": "Скрининг и функциональная диагностика",
            "de": "Screening und funktionelle Diagnostik",
            "tr": "Tarama ve fonksiyonel diagnostik",
        },
        "highlight": {
            "uz": "%(name)s bilan diagnostik tekshiruv",
            "en": "Diagnostic assessment with %(name)s",
            "ru": "Диагностическое исследование с %(name)s",
            "de": "Diagnostische Untersuchung mit %(name)s",
            "tr": "%(name)s ile diagnostik inceleme",
        },
        "keywords": [
            "uzi", "ultrasound", "ultrason", "doppler", "ekg", "ecg", "eeg", "holter",
            "эндоскоп", "endoscop", "эндоскопия", "ультразвук", "ультразву", "diagnostic",
            "diagnost", "screen", "skrining", "скрининг",
        ],
    },
    {
        "key": "monitoring",
        "label": {
            "uz": "Monitoring",
            "en": "Monitoring",
            "ru": "Мониторинг",
            "de": "Monitoring",
            "tr": "Izleme",
        },
        "capability": {
            "uz": "Real vaqt bemor monitoringi",
            "en": "Real-time patient monitoring",
            "ru": "Мониторинг пациента в реальном времени",
            "de": "Patientenmonitoring in Echtzeit",
            "tr": "Gercek zamanli hasta izleme",
        },
        "highlight": {
            "uz": "%(name)s bilan uzluksiz kuzatuv",
            "en": "Continuous observation with %(name)s",
            "ru": "Непрерывное наблюдение с %(name)s",
            "de": "Kontinuierliche Uberwachung mit %(name)s",
            "tr": "%(name)s ile kesintisiz izleme",
        },
        "keywords": [
            "monitor", "monitoring", "telemetry", "saturation", "pulse ox",
            "пациент монитор", "мониторинг", "bedside", "icu monitor",
        ],
    },
    {
        "key": "critical_care",
        "label": {
            "uz": "Reanimatsiya",
            "en": "Critical Care",
            "ru": "Реанимация",
            "de": "Intensivpflege",
            "tr": "Yogun Bakim",
        },
        "capability": {
            "uz": "Reanimatsiya va hayotni qo'llab-quvvatlash",
            "en": "Critical care and life-support systems",
            "ru": "Реанимация и системы жизнеобеспечения",
            "de": "Intensivpflege und lebenserhaltende Systeme",
            "tr": "Yogun bakim ve yasam destegi sistemleri",
        },
        "highlight": {
            "uz": "%(name)s bilan intensiv yordam",
            "en": "Intensive care support with %(name)s",
            "ru": "Интенсивная поддержка с %(name)s",
            "de": "Intensivunterstutzung mit %(name)s",
            "tr": "%(name)s ile yogun bakim destegi",
        },
        "keywords": [
            "ventilator", "defibrillator", "defib", "infusion pump", "syringe pump",
            "resusc", "reanima", "icu", "respirator", "кислород", "дефибрил",
            "вентилятор", "реанима", "инфуз", "кардиореспиратор",
        ],
    },
    {
        "key": "laboratory",
        "label": {
            "uz": "Laboratoriya",
            "en": "Laboratory",
            "ru": "Лаборатория",
            "de": "Labor",
            "tr": "Laboratuvar",
        },
        "capability": {
            "uz": "Laborator tahlil va tezkor skrining",
            "en": "Laboratory analysis and rapid screening",
            "ru": "Лабораторный анализ и быстрый скрининг",
            "de": "Laboranalyse und schnelles Screening",
            "tr": "Laboratuvar analizi ve hizli tarama",
        },
        "highlight": {
            "uz": "%(name)s bilan laborator tahlil",
            "en": "Laboratory analysis with %(name)s",
            "ru": "Лабораторный анализ с %(name)s",
            "de": "Laboranalyse mit %(name)s",
            "tr": "%(name)s ile laboratuvar analizi",
        },
        "keywords": [
            "analyzer", "analiz", "analysis", "pcr", "lab", "laborator",
            "centrifuge", "microscope", "реагент", "лаборат", "анализатор",
            "микроскоп", "центрифуг",
        ],
    },
    {
        "key": "surgery",
        "label": {
            "uz": "Jarrohlik",
            "en": "Surgery",
            "ru": "Хирургия",
            "de": "Chirurgie",
            "tr": "Cerrahi",
        },
        "capability": {
            "uz": "Operatsion va anesteziya yordamchi tizimlari",
            "en": "Operating room and anesthesia support systems",
            "ru": "Операционные и анестезиологические системы поддержки",
            "de": "OP- und Anasthesie-Unterstutzungssysteme",
            "tr": "Ameliyathane ve anestezi destek sistemleri",
        },
        "highlight": {
            "uz": "%(name)s bilan operatsion yordam",
            "en": "Surgical support with %(name)s",
            "ru": "Хирургическая поддержка с %(name)s",
            "de": "Chirurgische Unterstutzung mit %(name)s",
            "tr": "%(name)s ile cerrahi destek",
        },
        "keywords": [
            "anesthesia", "anaesthesia", "operating", "surgical", "surgery",
            "laparoscope", "эндоскоп", "операцион", "анестез", "хирург",
            "jarroh", "anestezi", "operats", "laparoskop",
        ],
    },
    {
        "key": "therapy",
        "label": {
            "uz": "Davolash",
            "en": "Therapy",
            "ru": "Терапия",
            "de": "Therapie",
            "tr": "Tedavi",
        },
        "capability": {
            "uz": "Davolash va reabilitatsiya uskunalari",
            "en": "Therapy and rehabilitation equipment",
            "ru": "Оборудование для терапии и реабилитации",
            "de": "Therapie- und Rehabilitationsgerate",
            "tr": "Tedavi ve rehabilitasyon ekipmanlari",
        },
        "highlight": {
            "uz": "%(name)s bilan davolash jarayoni",
            "en": "Treatment workflow with %(name)s",
            "ru": "Лечебный процесс с %(name)s",
            "de": "Behandlungsablauf mit %(name)s",
            "tr": "%(name)s ile tedavi sureci",
        },
        "keywords": [
            "laser", "therapy", "rehab", "rehabil", "dialysis", "physio",
            "физио", "реабил", "лазер", "диализ", "davolash", "reabilitats",
        ],
    },
    {
        "key": "general",
        "label": {
            "uz": "Ko'p maqsadli",
            "en": "Multidisciplinary",
            "ru": "Универсальное",
            "de": "Universell",
            "tr": "Cok Amacli",
        },
        "capability": {
            "uz": "Ko'p maqsadli klinik uskunalar",
            "en": "Multidisciplinary clinical equipment",
            "ru": "Универсальное клиническое оборудование",
            "de": "Universelle klinische Gerate",
            "tr": "Cok amacli klinik ekipmanlar",
        },
        "highlight": {
            "uz": "%(name)s bilan klinik qo'llanma",
            "en": "Clinical workflow with %(name)s",
            "ru": "Клинический рабочий процесс с %(name)s",
            "de": "Klinischer Ablauf mit %(name)s",
            "tr": "%(name)s ile klinik is akisi",
        },
        "keywords": [],
    },
]
EQUIPMENT_CATEGORY_MAP = {rule["key"]: rule for rule in EQUIPMENT_CATEGORY_RULES}


def _translate_equipment_copy(value, language_code):
    if not isinstance(value, dict):
        return value
    normalized_language = (language_code or "en").split("-")[0].lower()
    return (
        value.get(normalized_language)
        or value.get("uz")
        or value.get("en")
        or next(iter(value.values()), "")
    )


def _normalize_equipment_text(value):
    text = strip_tags(value or "")
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized.lower() if not unicodedata.combining(ch))
    return " ".join(normalized.split())


def _detect_equipment_category_key(name, description):
    haystack = _normalize_equipment_text(f"{name} {description}")
    priority_keys = (
        "critical_care",
        "imaging",
        "diagnostics",
        "monitoring",
        "laboratory",
        "surgery",
        "therapy",
    )
    for category_key in priority_keys:
        rule = EQUIPMENT_CATEGORY_MAP[category_key]
        if any(keyword in haystack for keyword in rule["keywords"]):
            return category_key
    return "general"


def _format_equipment_count_label(label, count, language_code):
    normalized_language = (language_code or "en").split("-")[0].lower()
    if normalized_language == "uz":
        return f"{label} ({count} ta uskuna)"
    if normalized_language == "ru":
        return f"{label} ({count} ед.)"
    if normalized_language == "de":
        return f"{label} ({count} Gerate)"
    if normalized_language == "tr":
        return f"{label} ({count} ekipman)"
    return f"{label} ({count} devices)"


def _format_equipment_total_label(total, language_code):
    variants = {
        "uz": "Faol katalogda %(count)s ta uskuna mavjud",
        "en": "%(count)s active devices are available in the catalog",
        "ru": "В каталоге доступно %(count)s единиц активного оборудования",
        "de": "Im Katalog sind %(count)s aktive Gerate verfugbar",
        "tr": "Katalogda %(count)s aktif ekipman bulunuyor",
    }
    template = _translate_equipment_copy(variants, language_code)
    return template % {"count": total}


def _build_equipment_highlight(item, language_code):
    if item["category_key"] == "general" or not item["name"]:
        return ""

    rule = EQUIPMENT_CATEGORY_MAP[item["category_key"]]
    name_matches_category = any(
        keyword in _normalize_equipment_text(item["name"])
        for keyword in rule["keywords"]
    )
    if not name_matches_category:
        return ""
    return _translate_equipment_copy(rule["highlight"], language_code) % {"name": item["name"]}


def _build_equipment_capabilities(catalog, language_code):
    if not catalog:
        return []

    category_counts = Counter(item["category_key"] for item in catalog)
    capabilities = []

    for category_key, count in category_counts.most_common():
        if category_key == "general" and len(category_counts) > 1:
            continue
        capability_label = _translate_equipment_copy(
            EQUIPMENT_CATEGORY_MAP[category_key]["capability"],
            language_code,
        )
        capabilities.append(_format_equipment_count_label(capability_label, count, language_code))

    for item in catalog:
        if len(capabilities) >= 8:
            break
        highlight = _build_equipment_highlight(item, language_code)
        if highlight and highlight not in capabilities:
            capabilities.append(highlight)

    if not capabilities:
        capabilities.append(_format_equipment_total_label(len(catalog), language_code))

    return capabilities[:8]


class EquipmentLandingDetailView(DetailView):
    model = ClinicEquipment
    template_name = "v1/equipment-details.html"
    context_object_name = "equipment"

    def get_queryset(self):
        return ClinicEquipment.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language().split('-')[0]
        name = self.object.name.get(language_code, self.object.name.get('uz', ''))
        description = self.object.description.get(language_code, self.object.description.get('uz', ''))
        category_key = _detect_equipment_category_key(name, description)

        # Static translations
        translations = {
            "home": {"uz": "Bosh sahifa", "en": "Home", "ru": "Главная"},
            "equipment": {"uz": "Uskunalar", "en": "Equipment", "ru": "Оборудование"},
            "details": {"uz": "Batafsil ma'lumot", "en": "Details", "ru": "Подробности"},
            "description": {"uz": "Tavsif", "en": "Description", "ru": "Описание"},
            "specs": {"uz": "Texnik xususiyatlari", "en": "Technical Specifications",
                      "ru": "Технические характеристики"},
        }

        context['t'] = {k: v.get(language_code, v['en']) for k, v in translations.items()}

        # Image logic
        default_equipment_img = settings.STATIC_URL + "medic/img/equipment/equipment.jpeg"
        context['equipment_image'] = self.object.image.url if self.object.image else default_equipment_img

        # Multi-language content
        context['name'] = name
        context['description'] = description
        context['equipment_category'] = _translate_equipment_copy(
            EQUIPMENT_CATEGORY_MAP[category_key]["label"],
            language_code,
        )

        return context


class ContactStyleTwoView(TemplateView):
    template_name = "v1/contact-style-two.html"

    @staticmethod
    def normalize_uzbek_phone(value):
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if digits.startswith("998"):
            digits = digits[3:]
        digits = digits[:9]
        if not digits:
            return ""
        return f"+998{digits}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language().split('-')[0]

        # Static translations
        translations = {
            "page_title": {"uz": "Bog'lanish", "en": "Contact", "ru": "Контакт"},
            "home": {"uz": "Bosh sahifa", "en": "Home", "ru": "Главная"},
            "get_in_touch": {"uz": "Biz bilan bog'laning", "en": "Get In Touch", "ru": "Связаться с нами"},
            "contact_desc": {
                "uz": "Sizni qiziqtirgan savollar bo'yicha bizga murojaat qiling. Bizning mutaxassislarimiz sizga yordam berishga tayyor.",
                "en": "Contact us for any questions you may have. Our experts are ready to help you.",
                "ru": "Свяжитесь с нами по любым вопросам. Наши специалисты готовы помочь вам."
            },
            "contact_us": {"uz": "Aloqa ma'lumotlari", "en": "Contact Info", "ru": "Контактная информация"},
            "address": {"uz": "Manzil", "en": "Address", "ru": "Адрес"},
            "email": {"uz": "Email", "en": "Email", "ru": "Электронная почта"},
            "phone": {"uz": "Telefon", "en": "Phone", "ru": "Телефон"},
            "drop_message": {"uz": "Xabar qoldiring", "en": "Drop Us A Message", "ru": "Оставьте сообщение"},
            "message_desc": {
                "uz": "Savolingiz yoki murojaatingizni yozib qoldiring. Operatorlarimiz siz bilan bog'lanadi.",
                "en": "Leave your question or request and our team will contact you shortly.",
                "ru": "Оставьте ваш вопрос или обращение, и наша команда свяжется с вами.",
            },
            "appointment_title": {"uz": "Qabulga yozilish", "en": "Book an Appointment", "ru": "Запись на прием"},
            "appointment_desc": {
                "uz": "Faol shifokorlardan birini tanlab, qabul uchun so'rov yuboring.",
                "en": "Choose one of our active specialists and send an appointment request.",
                "ru": "Выберите одного из наших активных специалистов и отправьте заявку на прием.",
            },
            "employee_label": {"uz": "Shifokorni tanlang", "en": "Choose a Doctor", "ru": "Выберите врача"},
            "employee_placeholder": {"uz": "Shifokorni tanlang", "en": "Select a doctor", "ru": "Выберите врача"},
            "contact_form_title": {"uz": "Tezkor murojaat", "en": "Quick Request", "ru": "Быстрое обращение"},
            "forms_heading": {"uz": "So'rov va qabul formasi", "en": "Request and Appointment Forms",
                              "ru": "Формы обращения и записи"},
            "forms_desc": {
                "uz": "Pastdagi katta kartada tezkor murojaat yuborish yoki aniq shifokor qabuliga yozilish mumkin.",
                "en": "Use the large card below either to send a quick request or to book an appointment with a specific doctor.",
                "ru": "В большой карточке ниже можно отправить быстрое обращение или записаться на прием к конкретному врачу.",
            },
            "appointment_button": {"uz": "Qabulga yozilish", "en": "Book Appointment", "ru": "Записаться"},
            "name_label": {"uz": "To'liq ismingiz", "en": "Your Name", "ru": "Ваше полное имя"},
            "phone_label": {"uz": "Telefon raqamingiz", "en": "Your Phone", "ru": "Ваш номер телефона"},
            "message_label": {"uz": "Xabaringiz", "en": "Your Message", "ru": "Ваше сообщение"},
            "send_btn": {"uz": "Xabarni yuborish", "en": "Send Message", "ru": "Отправить сообщение"},
            "success_msg": {
                "uz": "Xabaringiz muvaffaqiyatli yuborildi! Tez orada siz bilan bog'lanamiz.",
                "en": "Your message has been sent successfully! We will contact you soon.",
                "ru": "Ваше сообщение успешно отправлено! Мы свяжемся с вами в ближайшее время."
            },
            "error_msg": {
                "uz": "Xabar yuborishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
                "en": "An error occurred while sending the message. Please try again.",
                "ru": "Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте еще раз."
            },
            "appointment_success_msg": {
                "uz": "Qabul so'rovingiz qabul qilindi. Administrator tez orada siz bilan bog'lanadi.",
                "en": "Your appointment request has been received. An administrator will contact you soon.",
                "ru": "Ваша заявка на прием принята. Администратор свяжется с вами в ближайшее время.",
            },
            "appointment_error_msg": {
                "uz": "Qabul so'rovini yuborishda xatolik yuz berdi. Maydonlarni tekshirib qaytadan urinib ko'ring.",
                "en": "There was an error submitting the appointment request. Please check the fields and try again.",
                "ru": "Произошла ошибка при отправке заявки на прием. Проверьте поля и попробуйте снова.",
            }
        }

        context['t'] = {k: v.get(language_code, v['en']) for k, v in translations.items()}
        context['site_settings'] = SiteSettings.objects.first()
        context['employees'] = CustomUser.objects.filter(
            is_active_employee=True,
            is_superuser=False,
        ).order_by('full_name')
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type", "contact")

        if form_type == "appointment":
            full_name = request.POST.get("appointment_name", "").strip()
            phone_number = self.normalize_uzbek_phone(request.POST.get("appointment_phone"))
            message = request.POST.get("appointment_message", "").strip()
            employee_id = request.POST.get("employee_id")

            if not (full_name and phone_number and message and employee_id):
                return JsonResponse({"status": "error", "message": "missing_appointment_fields"}, status=400)

            employee = CustomUser.objects.filter(
                pk=employee_id,
                is_active_employee=True,
                is_superuser=False,
            ).first()
            if not employee:
                return JsonResponse({"status": "error", "message": "invalid_employee"}, status=400)

            Appointment.objects.create(
                full_name=full_name,
                phone_number=phone_number,
                message=message,
                employee=employee,
            )
            return JsonResponse({"status": "success", "form": "appointment"})

        full_name = request.POST.get('name', "").strip()
        phone_number = self.normalize_uzbek_phone(request.POST.get('phone'))
        message = request.POST.get('message', "").strip()

        if full_name and phone_number:
            MedicalCheckupApplication.objects.create(
                full_name=full_name,
                phone_number=phone_number,
                message=message
            )
            return JsonResponse({"status": "success", "form": "contact"})
        return JsonResponse({"status": "error", "message": "missing_contact_fields"}, status=400)


class EquipmentLeftSidebarView(TemplateView):
    template_name = "v1/equipment-left-sidebar.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language().split('-')[0]
        search_query = self.request.GET.get("q", "").strip()
        normalized_search_query = _normalize_equipment_text(search_query)

        # Static translations
        translations = {
            "page_title": {
                "uz": "Uskunalar",
                "en": "Equipment",
                "ru": "Оборудование",
            },
            "home": {
                "uz": "Bosh sahifa",
                "en": "Home",
                "ru": "Главная",
            },
            "tech": {
                "uz": "Texnologiyalar",
                "en": "Technologies",
                "ru": "Технологии",
            },
            "our_equipment": {
                "uz": "Bizning tibbiy uskunalarimiz",
                "en": "Our Medical Equipment",
                "ru": "Наше медицинское оборудование",
            },
            "description": {
                "uz": "Klinikamizda ishlatiladigan asosiy vizualizatsiya, diagnostika, jarrohlik, monitoring va reanimatsiya qurilmalari bilan tanishing.",
                "en": "Explore the core devices used across imaging, diagnostics, surgery, monitoring, and critical care.",
                "ru": "Ознакомьтесь с основными устройствами, используемыми в визуализации, диагностике, хирургии, мониторинге и интенсивной терапии.",
            },
            "view_equipment": {
                "uz": "Uskunani ko'rish",
                "en": "View Equipment",
                "ru": "Просмотреть оборудование",
            },
            "search_placeholder": {
                "uz": "Uskunalardan qidiring...",
                "en": "Search equipment...",
                "ru": "Поиск оборудования...",
            },
            "capabilities_title": {
                "uz": "Asosiy imkoniyatlar",
                "en": "Key Capabilities",
                "ru": "Ключевые возможности",
            },
            "categories_title": {
                "uz": "Uskuna toifalari",
                "en": "Equipment Categories",
                "ru": "Категории оборудования",
            },
            "no_match": {
                "uz": "Sizning qidiruvingizga mos uskuna topilmadi.",
                "en": "No equipment matched your search.",
                "ru": "Оборудование не найдено.",
            },
            "try_another": {
                "uz": "Boshqa uskuna nomi yoki toifasini sinab ko'ring.",
                "en": "Try another equipment name or category.",
                "ru": "Попробуйте другое название или категорию.",
            }
        }

        context['t'] = {k: v.get(language_code, v['en']) for k, v in translations.items()}

        # Database dan qurilmalarni olish
        db_equipments = ClinicEquipment.objects.filter(is_active=True).order_by('-created_at')

        default_equipment_img = settings.STATIC_URL + "medic/img/equipment/equipment.jpeg"

        # Translate and prepare data
        catalog = []
        for eq in db_equipments:
            name = eq.name.get(language_code, eq.name.get('uz', ''))
            summary = eq.description.get(language_code, eq.description.get('uz', ''))
            image_url = eq.image.url if eq.image else default_equipment_img
            category_key = _detect_equipment_category_key(name, summary)
            category_label = _translate_equipment_copy(
                EQUIPMENT_CATEGORY_MAP[category_key]["label"],
                language_code,
            )

            catalog.append({
                "id": eq.id,
                "name": name,
                "category_key": category_key,
                "category": category_label,
                "published_date": eq.created_at,
                "summary": summary,
                "image_url": image_url,
                "search_index": _normalize_equipment_text(f"{name} {category_label} {summary}"),
            })

        if normalized_search_query:
            filtered_catalog = [
                item for item in catalog
                if normalized_search_query in item["search_index"]
            ]
        else:
            filtered_catalog = catalog

        paginator = Paginator(filtered_catalog, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        sidebar_source = filtered_catalog if normalized_search_query else catalog
        category_counts = Counter(item["category_key"] for item in sidebar_source)
        equipment_categories = []
        for category_key, count in category_counts.most_common():
            if category_key == "general" and len(category_counts) > 1:
                continue
            equipment_categories.append({
                "name": _translate_equipment_copy(
                    EQUIPMENT_CATEGORY_MAP[category_key]["label"],
                    language_code,
                ),
                "count": count,
            })

        # Capabilities translations
        capabilities_list = {
            "en": [
                "High-resolution imaging", "Real-time bedside monitoring", "Critical care life support",
                "Emergency resuscitation", "Precision drug delivery", "Rapid diagnostic screening",
                "Emergency cardiac response", "Operating room anesthesia support",
            ],
            "uz": [
                "Yuqori aniqlikdagi vizualizatsiya", "Real vaqtda yotoq yonida monitoring",
                "Reanimatsiya hayotni qo'llab-quvvatlash",
                "Favqulodda reanimatsiya", "Aniq dori yetkazib berish", "Tezkor diagnostik skrining",
                "Favqulodda yurak javobi", "Operatsiya xonasida anesteziya yordami",
            ],
            "ru": [
                "Визуализация высокого разрешения", "Прикроватный мониторинг в реальном времени",
                "Жизнеобеспечение в интенсивной терапии",
                "Экстренная реанимация", "Точная доставка лекарств", "Быстрый диагностический скрининг",
                "Экстренное реагирование сердца", "Анестезиологическая поддержка в операционной",
            ]
        }

        context.update({
            "search_query": search_query,
            "page_obj": page_obj,
            "equipments": page_obj.object_list,
            "equipment_categories": equipment_categories,
            "capabilities": _build_equipment_capabilities(sidebar_source, language_code),
        })
        return context
