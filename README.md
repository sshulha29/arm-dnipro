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

### 2. На сервері
```bash
cd /opt/arm-dnipro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Systemd
Сервіс `/etc/systemd/system/arm-dnipro.service` з `Environment="PORT=8999"` та `ExecStart=/opt/arm-dnipro/.venv/bin/python app.py`.

### 4. Файрвол
`sudo ufw allow 8999/tcp`

Доступ: http://arm.municipalnavarta.online:8999

Токен бота тільки в `.env`. Не публікуйте.
