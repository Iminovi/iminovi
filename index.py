import base64
import json
import logging
import os
import requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "iminovi/streaming-sederhana"
FILE_PATH = "videos.json"
GITHUB_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

app = Flask(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-Telegram-Bot-Vercel",
}


def send_telegram_message(chat_id, text, parse_mode=None):
  """Fungsi helper untuk mengirim pesan via HTTP API Telegram langsung"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text}
  if parse_mode:
    payload["parse_mode"] = parse_mode
  try:
    requests.post(url, json=payload)
  except Exception as e:
    logging.error(f"Gagal kirim pesan Telegram: {e}")


def update_github_videos(title, video_url, category):
  try:
    response = requests.get(GITHUB_URL, headers=HEADERS)
    current_videos = []
    sha = None

    if response.status_code == 200:
      file_data = response.json()
      sha = file_data["sha"]
      file_content = base64.b64decode(file_data["content"]).decode("utf-8")
      try:
        current_videos = json.loads(file_content)
        if not isinstance(current_videos, list):
          current_videos = []
      except:
        current_videos = []
    elif response.status_code == 404:
      current_videos = []

    # Otomatis ubah link /d/ menjadi /e/ agar siap diputar di iframe
    clean_url = video_url.strip()
    if "/d/" in clean_url:
      clean_url = clean_url.replace("/d/", "/e/")

    new_entry = {
        "title": title.strip(),
        "videoUrl": clean_url,
        "category": category.strip() if category else "Umum",
        "affiliateUrl": "",
    }
    current_videos.append(new_entry)

    json_string = json.dumps(current_videos, indent=2)
    encoded_content = base64.b64encode(json_string.encode("utf-8")).decode(
        "utf-8"
    )

    payload = {
        "message": f"Tambah video [{category}]: {title} via Vercel Webhook",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    put_response = requests.put(GITHUB_URL, headers=HEADERS, json=payload)
    if put_response.status_code in [200, 201]:
      return "Sukses! Data video berhasil ditambahkan ke GitHub."
    else:
      return f"Gagal menyimpan ke GitHub: {put_response.text}"
  except Exception as e:
    return f"Terjadi kesalahan sistem: {str(e)}"


@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
  update_json = request.get_json(force=True)

  if "message" in update_json:
    message = update_json["message"]
    text_pesan = message.get("text", "")
    chat_id = message["chat"]["id"]
    user_name = message.get("from", {}).get("first_name", "User")

    if "|" not in text_pesan:
      send_telegram_message(
          chat_id,
          (
              "Format salah! Gunakan format:\n`Judul Video | Link Doodstream |"
              " Kategori (opsional)`"
          ),
          parse_mode="Markdown",
      )
      return "OK", 200

    parts = text_pesan.split("|")
    title = parts[0]
    video_url = parts[1]
    category = parts[2] if len(parts) > 2 else "Umum"

    send_telegram_message(
        chat_id,
        (
            f"Halo {user_name}, memproses '{title.strip()}' kategori"
            f" '{category.strip()}'..."
        ),
    )

    hasil = update_github_videos(title, video_url, category)
    send_telegram_message(chat_id, hasil)

  return "OK", 200


@app.route("/", methods=["GET"])
def index():
  return "Vercel Telegram Bot is active!", 200