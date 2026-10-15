# АРМ Дніпро — Сектор МАСЦО

Автоматизоване робоче місце чергового сектору МАСЦО КП «Муніципальна варта» Дніпровської міської ради.

Додана можливість відправки повідомлень у Telegram, включно з GIF-анімаціями (метод `sendAnimation`).

## Запуск на arm.municipalnavarta.online :8999

### 1. DNS
У панелі DNS домену municipalnavarta.online створіть A-запис:
- Name: `arm`
- Type: A
- Value: IP вашого сервера
- TTL: 300–3600

Після пропагації перевіряйте: `dig arm.municipalnavarta.online` або `nslookup arm.municipalnavarta.online`

### 2. На сервері
```bash
# Скопіюйте папку arm-dnipro на сервер, наприклад у /opt/arm-dnipro
cd /opt/arm-dnipro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Відредагуйте .env — BOT_TOKEN, DEFAULT_CHAT_ID, FLASK_SECRET_KEY
```

### 3. Systemd-сервіс (рекомендовано)
Створіть `/etc/systemd/system/arm-dnipro.service`:
```ini
[Unit]
Description=ARM Dnipro MASCO
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/arm-dnipro
Environment="PORT=8999"
ExecStart=/opt/arm-dnipro/.venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now arm-dnipro
sudo systemctl status arm-dnipro
```

### 4. Файрвол
```bash
sudo ufw allow 8999/tcp
# або iptables / firewalld аналогічно
```

### 5. Доступ
- Прямий: http://arm.municipalnavarta.online:8999
- Для HTTPS обов’язково використовуйте reverse proxy (nginx/Caddy) на 80/443 з проксуванням на 127.0.0.1:8999 і сертифікатом Let's Encrypt.

Приклад nginx:
```nginx
server {
    listen 80;
    server_name arm.municipalnavarta.online;
    location / {
        proxy_pass http://127.0.0.1:8999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Потім `certbot --nginx -d arm.municipalnavarta.online`.

### Перенаправлення з preview
У `static/js/main.js` вже додано redirect на `https://arm.municipalnavarta.online/` (не спрацьовує на localhost).

Canonical встановлено на `https://arm.municipalnavarta.online/`.

## Локальний запуск
```bash
cd arm-dnipro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PORT=8999 python app.py
```
Відкрийте http://localhost:8999

## Відправка GIF
- URL GIF/MP4 без звуку або файл.
- Текст = caption.
- Ліміт Telegram: 50 МБ.

Токен бота тільки в `.env`. Не публікуйте.
