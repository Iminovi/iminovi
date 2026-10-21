import base64
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- KONFIGURASI ---
TELEGRAM_BOT_TOKEN = "8601178930:AAEJlrcH8Xg0iX0PdBsVObkYNcN_DWNyS1g"
GITHUB_TOKEN = "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"
REPO = "iminovi/streaming-sederhana"
FILE_PATH = "videos.json"
GITHUB_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

# Aktifkan logging untuk memantau status bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-Telegram-Bot",
}


def update_github_videos(new_title):
  """Fungsi untuk mengambil, menambahkan data baru, dan mengunggah ulang ke GitHub"""
  try:
    # 1. Ambil file videos.json yang ada di GitHub saat ini
    response = requests.get(GITHUB_URL, headers=HEADERS)

    current_videos = []
    sha = None

    if response.status_code == 200:
      file_data = response.json()
      sha = file_data["sha"]
      # Decode isi file lama dari base64
      file_content = base64.b64decode(file_data["content"]).decode("utf-8")
      try:
        current_videos = json.loads(file_content)
        if not isinstance(current_videos, list):
          current_videos = []
      except:
        current_videos = []
    elif response.status_code == 404:
      current_videos = []

    # 2. Tambahkan video baru ke dalam daftar list
    new_entry = {"title": new_title, "videoUrl": "", "affiliateUrl": ""}
    current_videos.append(new_entry)

    # 3. Ubah ke string JSON yang valid menggunakan json.dumps()
    json_string = json.dumps(current_videos, indent=2)

    # 4. Encode ke Base64
    encoded_content = base64.b64encode(json_string.encode("utf-8")).decode(
        "utf-8"
    )

    # 5. Kirim pembaruan (PUT) ke GitHub API
    payload = {
        "message": f"Tambah video baru: {new_title} via Python Bot",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    put_response = requests.put(GITHUB_URL, headers=HEADERS, json=payload)

    if put_response.status_code in [200, 201]:
      return "Sukses! Format JSON berhasil diperbarui di GitHub."
    else:
      return f"Gagal menyimpan ke GitHub: {put_response.text}"

  except Exception as e:
    return f"Terjadi kesalahan sistem: {str(e)}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Fungsi yang berjalan otomatis saat ada pesan teks masuk ke bot Telegram"""
  text_pesan = update.message.text
  user_name = update.message.from_user.first_name

  await update.message.reply_text(
      f"Halo {user_name}, memproses judul '{text_pesan}' ke GitHub..."
  )

  # Panggil fungsi GitHub
  hasil = update_github_videos(text_pesan)

  # Kirim balasan ke Telegram
  await update.message.reply_text(hasil)


if __name__ == "__main__":
  # Inisialisasi Bot Telegram
  app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

  # Daftarkan handler untuk menangkap semua pesan teks yang masuk
  app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

  print("Bot Telegram sedang berjalan... Tekan Ctrl+C untuk berhenti.")
  app.run_polling()