import base64
import json
import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Muat variabel dari file .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "iminovi/streaming-sederhana"
FILE_PATH = "videos.json"
GITHUB_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-Telegram-Bot",
}


def update_github_videos(title, video_url):
  """Fungsi untuk menambahkan data video dengan link Doodstream ke GitHub"""
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

    # Masukkan Judul dan Link Doodstream ke dalam database
    new_entry = {
        "title": title.strip(),
        "videoUrl": video_url.strip(),
        "affiliateUrl": "",  # Bisa diisi link Shopee jika ada nanti
    }
    current_videos.append(new_entry)

    json_string = json.dumps(current_videos, indent=2)
    encoded_content = base64.b64encode(json_string.encode("utf-8")).decode(
        "utf-8"
    )

    payload = {
        "message": f"Tambah video Doodstream: {title} via Telegram Bot",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    put_response = requests.put(GITHUB_URL, headers=HEADERS, json=payload)

    if put_response.status_code in [200, 201]:
      return "Sukses! Data video Doodstream berhasil ditambahkan ke GitHub."
    else:
      return f"Gagal menyimpan ke GitHub: {put_response.text}"

  except Exception as e:
    return f"Terjadi kesalahan sistem: {str(e)}"


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Menerima pesan teks dengan format: Judul | LinkVideo"""
  text_pesan = update.message.text
  user_name = update.message.from_user.first_name

  # Validasi apakah pesan mengandung pemisah '|'
  if "|" not in text_pesan:
    await update.message.reply_text(
        "Format salah! Gunakan format:\n`Judul Video | Link Doodstream`",
        parse_mode="Markdown",
    )
    return

  # Pisahkan judul dan link
  parts = text_pesan.split("|", 1)
  title = parts[0]
  video_url = parts[1]

  await update.message.reply_text(
      f"Halo {user_name}, memproses '{title.strip()}' ke GitHub..."
  )

  hasil = update_github_videos(title, video_url)
  await update.message.reply_text(hasil)


if __name__ == "__main__":
  app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

  # Bot mendengarkan pesan teks biasa
  app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

  print("Bot Doodstream siap digunakan... Tekan Ctrl+C untuk berhenti.")
  app.run_polling()