import base64
import requests

# Konfigurasi GitHub Anda
GITHUB_TOKEN = "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"  # Ganti dengan GitHub PAT Anda
REPO = "iminovi/streaming-sederhana"
FILE_PATH = "videos.json"
url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-Script",
}


def update_videos(new_title):
  # 1. Ambil data (GET) file videos.json yang ada di GitHub saat ini untuk mendapatkan SHA terbaru
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    file_data = response.json()
    sha = file_data["sha"]

    # Decode isi file lama (opsional, jika ingin menambahkan video baru ke daftar yang sudah ada)
    # Untuk sekarang, kita buat array baru berisi video yang dikirim dari Telegram:
    import json

    updated_content = [{"title": new_title, "videoUrl": "", "affiliateUrl": ""}]

    # Ubah ke string JSON lalu encode ke Base64
    json_string = json.dumps(updated_content, indent=2)
    encoded_content = base64.b64encode(json_string.encode("utf-8")).decode(
        "utf-8"
    )

    # 2. Kirim pembaruan (PUT) ke GitHub API
    payload = {
        "message": "Tambah video baru via Python automation",
        "content": encoded_content,
        "sha": sha,
    }

    put_response = requests.put(url, headers=headers, json=payload)
    if put_response.status_code in [200, 201]:
      print("Sukses memperbarui videos.json di GitHub!")
    else:
      print(f"Gagal update ke GitHub: {put_response.text}")
  else:
    print(f"Gagal mengambil file dari GitHub: {response.text}")


# Contoh penggunaan fungsi dengan teks dari Telegram
if __name__ == "__main__":
  pesan_telegram = "Pemenang"  # Ini nanti diganti dari input Telegram Anda
  update_videos(pesan_telegram)
