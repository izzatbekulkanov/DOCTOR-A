# Ubuntu deploy

1. Repo'ni serverga joylang.
2. `.env.example` ni `.env` qilib to'ldiring.
3. Root yoki sudo bilan ishga tushiring:

```bash
bash deploy/install_ubuntu.sh example.com
```

Natija:
- `.venv` yaratiladi
- `requirements.txt` o'rnatiladi
- `migrate` va `collectstatic` ishlaydi
- `doctor-a-web.service` va `doctor-a-bot.service` yoziladi
- `nginx` konfiguratsiyasi ulanadi
- servislar auto-start holatiga o'tadi
