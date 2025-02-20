import requests

# 🔹 Telegram bot tokeni va kanal ID (yoki username)
BOT_TOKEN = "7645955490:AAH6YjpAFL8hEs48rxlqrSxFrK4fBJXMzc8"
CHANNEL_ID = "@Doctor_a_HOSPITAL"  # Kanal username yoki ID


def send_message(text):
    """
    📢 Ushbu funksiya bot orqali berilgan `text`ni Telegram kanalga yuboradi.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"  # HTML formatda xabar yuborish uchun
    }

    response = requests.post(url, data=data)

    # ✅ Xatolik bo‘lsa terminalga chiqarish
    if response.status_code != 200:
        print(f"❌ Telegramga yuborishda xatolik: {response.text}")

    return response.json()
