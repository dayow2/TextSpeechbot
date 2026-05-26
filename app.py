import os
import io
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from gtts import gTTS
import asyncio

# === CONFIGURATION ===
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 5000))

# === FLASK APP for Render Health Checks ===
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is running!", 200

# === TELEGRAM BOT HANDLERS ===
async def start(update: Update, context):
    """Send welcome message when /start is issued."""
    welcome_text = (
        "🎤 *Welcome to Text to Speech Bot!*\n\n"
        "Send me any text, and I'll convert it to voice.\n\n"
        "*Features:*\n"
        "• Supports multiple languages\n"
        "• Fast & free\n"
        "• Works with any text up to 1000 chars\n\n"
        "Just type your message and I'll reply with voice! 🗣️"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def text_to_speech(update: Update, context):
    """Convert text message to speech and send as voice."""
    text = update.message.text
    
    # Limit text length to avoid issues
    if len(text) > 1000:
        await update.message.reply_text("⚠️ Text is too long! Please send less than 1000 characters.")
        return
    
    try:
        # Create audio file in memory (no disk writes)
        audio_buffer = io.BytesIO()
        tts = gTTS(text=text, lang='en', slow=False)
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Send as voice message
        await update.message.reply_voice(
            voice=audio_buffer,
            filename="speech.ogg",
            caption=f"🗣️ *You said:* {text[:100]}..."
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: Could not convert text to speech. Please try again.")
        print(f"Error: {e}")

async def help_command(update: Update, context):
    """Send help message."""
    help_text = (
        "*How to use:*\n"
        "1. Send /start to begin\n"
        "2. Type any text message\n"
        "3. Bot replies with voice!\n\n"
        "*Commands:*\n"
        "/start - Welcome message\n"
        "/help - Show this help\n\n"
        "*Tip:* Try different languages! Just write in your language."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# === MAIN FUNCTION ===
async def main():
    """Initialize and run the Telegram bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    
    # Start bot (using polling)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep the bot running
    print("Bot is running...")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

# === ENTRY POINT ===
if __name__ == "__main__":
    import threading
    
    # Run Flask in a separate thread for health checks
    def run_flask():
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the bot
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
