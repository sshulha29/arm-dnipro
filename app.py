import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def send_telegram(token, method, data, files=None):
    url = TELEGRAM_API.format(token=token, method=method)
    try:
        if files:
            resp = requests.post(url, data=data, files=files, timeout=30)
        else:
            resp = requests.post(url, data=data, timeout=30)
        return resp.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    token = request.form.get("bot_token") or os.getenv("BOT_TOKEN")
    chat_id = request.form.get("chat_id") or os.getenv("DEFAULT_CHAT_ID")
    text = request.form.get("text", "").strip()
    gif_url = request.form.get("gif_url", "").strip()
    gif_file = request.files.get("gif_file")

    if not token or not chat_id:
        return jsonify({"ok": False, "error": "Потрібні BOT_TOKEN та CHAT_ID"}), 400

    if gif_file and gif_file.filename:
        files = {"animation": (gif_file.filename, gif_file.stream, gif_file.mimetype or "image/gif")}
        data = {"chat_id": chat_id}
        if text:
            data["caption"] = text
        result = send_telegram(token, "sendAnimation", data, files)
    elif gif_url:
        data = {
            "chat_id": chat_id,
            "animation": gif_url,
        }
        if text:
            data["caption"] = text
        result = send_telegram(token, "sendAnimation", data)
    elif text:
        data = {"chat_id": chat_id, "text": text}
        result = send_telegram(token, "sendMessage", data)
    else:
        return jsonify({"ok": False, "error": "Потрібен текст або GIF"}), 400

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8999))
    app.run(host="0.0.0.0", port=port, debug=False)
