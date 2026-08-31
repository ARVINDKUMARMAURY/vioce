"""
Telegram Audio-to-Hindi-Text Bot (Long Audio Version)
========================================================
3-4 ghante tak ke audio/voice files ko Hindi text mein convert karta hai.
faster-whisper (local model) use karta hai - internet per-chunk nahi chahiye,
lambi files reliably handle karta hai.

ENV VARIABLES (Railway ke "Variables" tab mein set karein):
    BOT_TOKEN        -> BotFather se mila token
    TELEGRAM_API_URL  -> (optional) agar local bot-api-server use kar rahe hain,
                          uska base URL, e.g. http://bot-api:8081
    WHISPER_MODEL     -> model size: tiny / base / small / medium (default: small)
"""

import os
import logging
import asyncio
from faster_whisper import WhisperModel
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
LOCAL_API_URL = os.environ.get("TELEGRAM_API_URL")  # local bot-api-server ka base URL, agar hai
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Model ek baar load hoga, sab requests ke liye reuse hoga (CPU optimized)
logger.info(f"Whisper model load ho raha hai: {MODEL_SIZE} ...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
logger.info("Model load ho gaya.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! 👋\n"
        "Koi bhi audio/voice message (lambi files bhi chalengi) forward ya "
        "bhejein, main usse Hindi text mein convert karke .txt file bhej dunga.\n\n"
        "⏳ 3-4 ghante ke audio mein processing time lag sakta hai, dhairya rakhein."
    )


def transcribe_long_audio(file_path: str) -> str:
    """faster-whisper se poori audio ek saath transcribe karta hai (VAD ke saath)."""
    segments, info = model.transcribe(
        file_path,
        language="hi",
        vad_filter=True,           # khaali/silent parts automatically skip karega
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    lines = []
    for seg in segments:
        # Timestamp ke saath text taaki lambi file mein navigate karna aasan ho
        start_min = int(seg.start // 60)
        start_sec = int(seg.start % 60)
        lines.append(f"[{start_min:02d}:{start_sec:02d}] {seg.text.strip()}")

    return "\n".join(lines)


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    file_obj = None
    if message.voice:
        file_obj = message.voice
    elif message.audio:
        file_obj = message.audio
    elif message.document and message.document.mime_type and "audio" in message.document.mime_type:
        file_obj = message.document

    if file_obj is None:
        await message.reply_text("Kripya koi audio ya voice message bhejein.")
        return

    status_msg = await message.reply_text("🎧 Audio download ho raha hai...")

    local_path = None
    try:
        tg_file = await context.bot.get_file(file_obj.file_id)
        ext = os.path.splitext(tg_file.file_path or "")[1] or ".ogg"
        local_path = os.path.join(DOWNLOAD_DIR, f"{file_obj.file_id}{ext}")
        await tg_file.download_to_drive(local_path)

        await status_msg.edit_text(
            "🧠 Transcribe ho raha hai... 3-4 ghante ki file mein kaafi time "
            "lag sakta hai (aksar 20-40 min tak), please wait."
        )

        # Blocking whisper call ko background thread mein chalana taaki bot freeze na ho
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe_long_audio, local_path)

        if not text.strip():
            await status_msg.edit_text("⚠️ Koi text detect nahi hua. Audio saaf hai ya nahi check karein.")
            return

        # Result .txt file ke roop mein bhejna (lambi transcript ke liye)
        out_path = os.path.join(DOWNLOAD_DIR, f"{file_obj.file_id}_transcript.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        await status_msg.edit_text("✅ Transcription poori hui, file bhej raha hoon...")
        with open(out_path, "rb") as f:
            await message.reply_document(f, filename="hindi_transcript.txt")

        os.remove(out_path)

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ Kuch error aaya: {e}")

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)


def main():
    builder = ApplicationBuilder().token(BOT_TOKEN)
    if LOCAL_API_URL:
        # Local bot-api-server use karne se 20MB ki limit hat jaati hai (2GB tak)
        builder = builder.base_url(f"{LOCAL_API_URL}/bot").base_file_url(f"{LOCAL_API_URL}/file/bot")

    app = builder.build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.Document.AUDIO, handle_audio))

    logger.info("Bot chalu ho gaya hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
