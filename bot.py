import os
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
import os
import re
import subprocess
import tempfile
from pathlib import Path
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

# ✅ Agar ffmpeg PATH'da bo'lmasa, shu qo'shiladi
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

BOT_TOKEN = "8515666012:AAHeUhsXJl6jqdvqBHwARVEps-dn5BI6YCo"

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=[\w\-]{11}|youtu\.be/[\w\-]{11})"
)

# 🎧 Faqat audio stream URL olish (hech narsa yuklamasdan)
def get_audio_url(youtube_url: str) -> str:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"], info.get("title", "audio")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡️ Salom! Link tashlang — 3 soniyada MP3 qilib yuboraman!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = YOUTUBE_REGEX.search(text)
    if not match:
        await update.message.reply_text("❌ Iltimos, haqiqiy YouTube link yuboring.")
        return

    url = match.group(0)
    wait_msg = await update.message.reply_text("🎵 Ovoz olinmoqda...")

    try:
        audio_url, title = get_audio_url(url)
        title = re.sub(r'[<>:"/\\|?*\']', "_", title)

        # ⏳ Audio oqimini ffmpeg orqali to‘g‘ridan-to‘g‘ri MP3ga aylantiramiz (RAM’da)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        cmd = [
            "ffmpeg",
            "-i", audio_url,
            "-vn",                # video yo‘q
            "-acodec", "libmp3lame",
            "-b:a", "128k",
            "-y",
            str(tmp_path)
        ]

        # ⚡️ ffmpeg’ni real vaqtda ishga tushiramiz
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # ✅ Tayyor MP3 faylni yuboramiz
        await update.message.reply_audio(
            audio=InputFile(open(tmp_path, "rb"), filename=f"{title}.mp3"),
            caption=f"✅ {title}",
        )

        tmp_path.unlink(missing_ok=True)  # faylni o‘chirib tashlash
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")
    finally:
        await wait_msg.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_link))
    print("⚡️ Ultra-tez bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
