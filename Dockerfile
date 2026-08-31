# Railway deployment - Audio-to-Hindi-Text Telegram Bot
FROM python:3.11-slim

# ffmpeg zaroori hai audio processing ke liye
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_audio_bot.py .

# Model ko pehle se download kar lena (startup fast rahega)
ENV WHISPER_MODEL=small
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

CMD ["python", "telegram_audio_bot.py"]
