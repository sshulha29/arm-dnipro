import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_GIF = os.path.join(BASE_DIR, "static", "default", "alert.gif")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DEFAULT_GIF), exist_ok=True)


def ensure_default_gif():
    if os.path.isfile(DEFAULT_GIF) and os.path.getsize(DEFAULT_GIF) > 0:
        return
    b64_path = DEFAULT_GIF + ".b64"
    if not os.path.isfile(b64_path):
        return
    import base64
    with open(b64_path, "r", encoding="ascii") as handle:
        raw = base64.b64decode(handle.read())
    with open(DEFAULT_GIF, "wb") as handle:
        handle.write(raw)


ensure_default_gif()

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def now_kyiv():
    try:
        return datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d.%m.%Y %H:%M")


def saved_animation():
    for name in ("alert.gif", "alert.mp4"):
        path = os.path.join(DATA_DIR, name)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def alert_gif_path():
    saved = saved_animation()
    if saved:
        return saved
    if os.path.isfile(DEFAULT_GIF):
        return DEFAULT_GIF
    return None


def send_telegram(token, method, data, files=None):
    url = TELEGRAM_API.format(token=token, method=method)
    try:
        if files:
            resp = requests.post(url, data=data, files=files, timeout=60)
        else:
            resp = requests.post(url, data=data, timeout=60)
        return resp.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def credentials():
    token = (request.form.get("bot_token") or os.getenv("BOT_TOKEN") or "").strip()
    chat_id = (request.form.get("chat_id") or os.getenv("DEFAULT_CHAT_ID") or "").strip()
    return token, chat_id


def alarm_caption(kind):
    when = now_kyiv()
    if kind == "start":
        text = os.getenv(
            "ALERT_TEXT",
            "УВАГА! Повітряна тривога. Негайно пройдіть в укриття.",
        ).strip()
        return f"{text}\n\nРучний режим АРМ МАСЦО · {when}"
    text = os.getenv("CLEAR_TEXT", "Відбій повітряної тривоги.").strip()
    return f"{text}\n\nРучний режим АРМ МАСЦО · {when}"


def send_animation_file(token, chat_id, path, caption):
    name = "alert.gif" if path.lower().endswith(".gif") else os.path.basename(path)
    mime = "image/gif" if name.endswith(".gif") else "video/mp4"
    with open(path, "rb") as handle:
        files = {"animation": (name, handle, mime)}
        data = {"chat_id": chat_id, "caption": caption}
        return send_telegram(token, "sendAnimation", data, files)


def send_animation_url(token, chat_id, url, caption):
    data = {"chat_id": chat_id, "animation": url, "caption": caption}
    return send_telegram(token, "sendAnimation", data)


@app.route("/")
def index():
    return render_template(
        "index.html",
        has_gif=alert_gif_path() is not None,
        gif_is_custom=saved_animation() is not None,
    )


@app.route("/alert-gif")
def alert_gif():
    path = alert_gif_path()
    if not path:
        return jsonify({"ok": False, "error": "GIF не задано"}), 404
    mime = "video/mp4" if path.endswith(".mp4") else "image/gif"
    return send_file(path, mimetype=mime, max_age=0)


@app.route("/alarm", methods=["POST"])
def alarm():
    token, chat_id = credentials()
    kind = (request.form.get("action") or "").strip()
    if kind not in ("start", "clear"):
        return jsonify({"ok": False, "error": "Невідома дія"}), 400
    if not token or not chat_id:
        return jsonify({"ok": False, "error": "Потрібні BOT_TOKEN та CHAT_ID у .env"}), 400

    caption = alarm_caption(kind)
    if kind == "clear":
        result = send_telegram(token, "sendMessage", {"chat_id": chat_id, "text": caption})
    else:
        # Ручна тривога завжди йде як sendAnimation, не як голий текст.
        gif_url = (os.getenv("ALERT_GIF_URL") or "").strip()
        saved = saved_animation()
        if saved:
            result = send_animation_file(token, chat_id, saved, caption)
        elif gif_url:
            result = send_animation_url(token, chat_id, gif_url, caption)
        elif alert_gif_path():
            result = send_animation_file(token, chat_id, alert_gif_path(), caption)
        else:
            return jsonify({"ok": False, "error": "Немає GIF для тривоги"}), 400

    if not result.get("ok"):
        return jsonify({
            "ok": False,
            "error": result.get("description") or "Telegram відхилив відправку",
        }), 502
    return jsonify({"ok": True, "action": kind, "animation": kind == "start"})


@app.route("/gif", methods=["POST"])
def save_gif():
    gif_file = request.files.get("gif_file")
    if not gif_file or not gif_file.filename:
        return jsonify({"ok": False, "error": "Оберіть файл GIF або MP4 без звуку"}), 400
    ext = os.path.splitext(gif_file.filename)[1].lower()
    if ext not in (".gif", ".mp4"):
        return jsonify({"ok": False, "error": "Дозволено лише .gif або .mp4"}), 400
    for old in (os.path.join(DATA_DIR, "alert.gif"), os.path.join(DATA_DIR, "alert.mp4")):
        if os.path.isfile(old):
            os.remove(old)
    target = os.path.join(DATA_DIR, "alert.gif" if ext == ".gif" else "alert.mp4")
    gif_file.save(target)
    return jsonify({"ok": True})


@app.route("/send", methods=["POST"])
def send():
    token, chat_id = credentials()
    text = request.form.get("text", "").strip()
    gif_url = request.form.get("gif_url", "").strip()
    gif_file = request.files.get("gif_file")

    if not token or not chat_id:
        return jsonify({"ok": False, "error": "Потрібні BOT_TOKEN та CHAT_ID"}), 400

    if gif_file and gif_file.filename:
        ext = os.path.splitext(gif_file.filename)[1].lower() or ".gif"
        name = "alert.gif" if ext == ".gif" else "alert.mp4"
        mime = "image/gif" if ext == ".gif" else "video/mp4"
        files = {"animation": (name, gif_file.stream, mime)}
        data = {"chat_id": chat_id}
        if text:
            data["caption"] = text
        result = send_telegram(token, "sendAnimation", data, files)
    elif gif_url:
        data = {"chat_id": chat_id, "animation": gif_url}
        if text:
            data["caption"] = text
        result = send_telegram(token, "sendAnimation", data)
    elif text:
        result = send_telegram(token, "sendMessage", {"chat_id": chat_id, "text": text})
    else:
        return jsonify({"ok": False, "error": "Потрібен текст або GIF"}), 400

    if not result.get("ok"):
        return jsonify({"ok": False, "error": result.get("description") or "Telegram відхилив відправку"}), 502
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8999))
    app.run(host="0.0.0.0", port=port, debug=False)
