# Telegram AI Bot – Uncensored, Voice + Text

A private AI companion on Telegram that uses your local uncensored Ollama model. Replies with text AND voice.

## Setup

1. **Install Python 3.9+** and **Ollama**.
2. Pull an uncensored model:  
   `ollama pull dolphin-mistral`
3. Install dependencies:  
   `pip install -r requirements.txt`
4. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and copy the token.
5. Create a `.env` file with:  
   `TELEGRAM_TOKEN=your_token_here`
6. Run the bot:  
   `python telegram_bot.py`

## Commands

- `/start` – Welcome message
- `/reset` – Erase conversation history

## How it works

- **Text messages** – Bot replies with text + voice.
- **Voice messages** – Bot transcribes (Google Speech Recognition), replies with text + voice.
- **Conversation memory** – Per user, stored in RAM (resets when bot restarts or `/reset`).
- **Uncensored** – Uses `dolphin-mistral` (or any model you set). No filters.

## Requirements

- Ollama running locally (or accessible via network).
- Internet for speech recognition (optional, but recommended).
- pyttsx3 may need additional system drivers on Linux (on Windows it works out of the box).

## Free Hosting (24/7)

To keep the bot running without your laptop:

- **Railway** (free tier with 500 hours/month) – add a credit card for verification, but free.
- **Hugging Face Spaces** – not ideal for long‑polling bots.
- **FPS.ms** – free always‑on Windows VPS (no credit card required) – see [docs.fps.ms](https://docs.fps.ms).

If you deploy to a VPS, ensure Ollama is also installed there and the model is pulled.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ollama not found` | Install Ollama and make sure it's in PATH. |
| Speech recognition fails | Install `pydub` and `ffmpeg` (or `libav`). On Windows: `pip install pydub` and download ffmpeg. |
| Voice reply too long | Telegram limits voice messages to ~1 minute. The bot skips sending if text is very long. |
| Bot doesn't reply | Check that Ollama is running (`ollama serve`). |
