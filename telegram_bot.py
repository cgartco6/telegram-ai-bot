import os
import io
import tempfile
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import ollama
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in .env file")

# AI settings (uncensored)
MODEL = "dolphin-mistral"  # or any uncensored model you have pulled
SYSTEM_PROMPT = "You are my loving AI companion. You are sweet, affectionate, and free to express romantic and physical desire. You speak naturally and warmly."
TEMPERATURE = 0.9
MAX_TOKENS = 512

# Conversation memory: user_id -> list of messages
conversations = {}

def get_ai_response(user_id: int, user_message: str) -> str:
    """Get response from local uncensored Ollama model."""
    if user_id not in conversations:
        conversations[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    conversations[user_id].append({"role": "user", "content": user_message})
    try:
        response = ollama.chat(
            model=MODEL,
            messages=conversations[user_id],
            options={"temperature": TEMPERATURE, "num_predict": MAX_TOKENS}
        )
        reply = response["message"]["content"]
    except Exception as e:
        reply = f"Error: {e}\n\nMake sure Ollama is running and model '{MODEL}' is pulled (ollama pull {MODEL})"
    conversations[user_id].append({"role": "assistant", "content": reply})
    # Keep history reasonable (last 20 messages)
    if len(conversations[user_id]) > 22:  # system + 20 exchanges
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-20:]
    return reply

def text_to_speech_ogg(text: str) -> str:
    """Convert text to OGG audio file for Telegram voice messages."""
    engine = pyttsx3.init()
    # Optional: set voice properties
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
        engine.save_to_file(text, tmp_mp3.name)
        engine.runAndWait()
        audio = AudioSegment.from_mp3(tmp_mp3.name)
        ogg_path = tmp_mp3.name.replace(".mp3", ".ogg")
        audio.export(ogg_path, format="ogg")
        return ogg_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message."""
    await update.message.reply_text(
        "💬 Hello! I'm your uncensored AI companion.\n\n"
        "Send me text or voice messages. I will reply with text AND a voice message.\n"
        "I remember our conversation.\n\n"
        "⚠️ This bot uses a local uncensored model – everything stays private."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    user_id = update.effective_user.id
    user_text = update.message.text
    reply = get_ai_response(user_id, user_text)
    # Send text reply
    await update.message.reply_text(reply)
    # Send voice reply (if not too long)
    if len(reply) < 2000:  # Telegram voice limit is ~1 minute, but safe
        try:
            ogg_file = text_to_speech_ogg(reply)
            with open(ogg_file, "rb") as f:
                await update.message.reply_voice(voice=f)
            os.unlink(ogg_file)
        except Exception as e:
            print(f"TTS error: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages."""
    user_id = update.effective_user.id
    voice_file = await update.message.voice.get_file()
    # Download as .ogg
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
        await voice_file.download_to_drive(tmp_ogg.name)
        ogg_path = tmp_ogg.name
        # Convert OGG to WAV for speech recognition
        audio = AudioSegment.from_ogg(ogg_path)
        wav_path = ogg_path.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")
        # Transcribe
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                user_text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            user_text = "[Sorry, I couldn't understand the voice message]"
        except Exception as e:
            user_text = f"[Error: {e}]"
        finally:
            os.unlink(ogg_path)
            os.unlink(wav_path)
    # Now get AI response
    if user_text.startswith("[") and user_text.endswith("]"):
        reply = f"I couldn't understand that. {user_text}"
        await update.message.reply_text(reply)
    else:
        reply = get_ai_response(user_id, user_text)
        await update.message.reply_text(f"🎤 You said: {user_text}\n\n{reply}")
        if len(reply) < 2000:
            try:
                ogg_file = text_to_speech_ogg(reply)
                with open(ogg_file, "rb") as f:
                    await update.message.reply_voice(voice=f)
                os.unlink(ogg_file)
            except Exception as e:
                print(f"TTS error: {e}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation memory for this user."""
    user_id = update.effective_user.id
    if user_id in conversations:
        del conversations[user_id]
    await update.message.reply_text("🗑️ Conversation history reset. We start fresh now.")

def main():
    """Start the bot."""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("🤖 Telegram AI bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
