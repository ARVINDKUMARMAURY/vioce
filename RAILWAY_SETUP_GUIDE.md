# Railway Par Deploy Karne Ki Poori Guide

## Zaroori files
Is folder mein 3 files hain jo Railway project mein daalni hain:
- `telegram_audio_bot.py`
- `requirements.txt`
- `Dockerfile`

---

## Step 1: GitHub repo banayein
1. Ek naya GitHub repo banayein (e.g. `hindi-audio-bot`)
2. Teeno files usme upload/push kar dein

---

## Step 2: Railway par naya project banayein
1. https://railway.app par jaayein → **New Project**
2. **Deploy from GitHub repo** choose karein → apna repo select karein
3. Railway automatically `Dockerfile` detect karke build kar lega

---

## Step 3: Environment Variables set karein
Railway project ke **Variables** tab mein jaakar ye add karein:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | BotFather se mila token |
| `WHISPER_MODEL` | `small` (behtar accuracy ke liye `medium` bhi try kar sakte hain, thoda slow hoga) |

---

## Step 4 (IMPORTANT): 20MB file-size limit hatana

Telegram ka **normal cloud Bot API** sirf 20MB tak ki files download karne deta hai.
3-4 ghante ka audio isse bada hoga, isliye ek **local Bot API server** bhi
Railway par run karna hoga (Telegram khud ye open-source tool provide karta hai,
isse 2GB tak ki files chalti hain).

### Kaise karein:
1. Railway project mein **"+ New"** → **"Empty Service"** se ek naya service add karein
2. Us service ki settings mein **Docker Image** deploy karein:
   ```
   aiogram/telegram-bot-api:latest
   ```
3. Us service ke **Variables** mein daalein:
   | Variable | Value |
   |---|---|
   | `TELEGRAM_API_ID` | https://my.telegram.org se apna api_id lein |
   | `TELEGRAM_API_HASH` | wahi site se api_hash lein |
   | `TELEGRAM_LOCAL` | `1` |
4. Is service ka naam note karein (e.g. `bot-api`). Railway internal networking mein
   ye `http://bot-api.railway.internal:8081` jaisa URL degi — Railway ke
   **"Networking"** tab mein internal domain check kar lein.
5. Apne main bot service ke Variables mein add karein:
   | Variable | Value |
   |---|---|
   | `TELEGRAM_API_URL` | `http://<bot-api-internal-domain>:8081` |

Agar ye setup thoda complex lage, to **shuruat mein isse skip kar sakte hain** —
bot 20MB tak ki files (~ 1-1.5 ghante ka compressed voice) bina kisi extra setup
ke handle kar lega. 3-4 ghante ki file ke liye ye step baad mein bhi add kar sakte hain.

---

## Step 5: Deploy & Test
1. Railway apne aap deploy kar dega (Dockerfile ke through)
2. Deploy hone ke baad logs mein "Bot chalu ho gaya hai..." dikhega
3. Apne Telegram bot ko audio forward karein aur wait karein

---

## Performance Notes
- **Model**: `small` fast hai, accuracy decent. `medium` zyada accurate lekin
  2-3x slow hoga CPU par.
- **3-4 ghante ka audio**: Railway Pro ke CPU par lagbhag 20-45 min lag sakte hain
  (model size aur CPU allocation par depend karta hai).
- Bot processing ke dauraan "Transcribe ho raha hai..." message dikhayega,
  koi timeout nahi hoga.
