import os
import io
from flask import Flask, request, jsonify
import requests
from gtts import gTTS

# === CONFIGURATION ===
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 5000))
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text, parse_mode=None):
    """Send text message to Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        data["parse_mode"] = parse_mode
    requests.post(url, json=data)

def send_voice(chat_id, audio_bytes, caption=None):
    """Send voice message to Telegram"""
    url = f"{TELEGRAM_API_URL}/sendVoice"
    files = {
        "voice": ("speech.ogg", audio_bytes, "audio/ogg")
    }
    data = {
        "chat_id": chat_id
    }
    if caption:
        data["caption"] = caption
    requests.post(url, data=data, files=files)

@app.route('/health')
def health():
    return "OK", 200

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Handle incoming messages"""
    try:
        update = request.get_json()
        
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            
            # Handle /start command
            if "text" in message:
                text = message["text"]
                
                if text == "/start":
                    welcome = "🎤 Welcome to Text to Speech Bot!\n\nSend me any text and I'll convert it to voice!"
                    send_message(chat_id, welcome)
                    return jsonify({"ok": True})
                
                elif text == "/help":
                    help_text = "Send me any text message and I'll reply with a voice message!"
                    send_message(chat_id, help_text)
                    return jsonify({"ok": True})
                
                else:
                    # Convert text to speech
                    try:
                        # Limit text length
                        if len(text) > 1000:
                            send_message(chat_id, "⚠️ Text too long! Send less than 1000 characters.")
                            return jsonify({"ok": True})
                        
                        # Generate speech
                        audio_buffer = io.BytesIO()
                        tts = gTTS(text=text, lang='en', slow=False)
                        tts.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)
                        
                        # Send voice
                        send_voice(chat_id, audio_buffer.read(), f"🗣️ {text[:100]}...")
                        
                    except Exception as e:
                        send_message(chat_id, "❌ Failed to convert text to speech. Try again!")
                        print(f"Error: {e}")
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"ok": False}), 500

def set_webhook():
    """Set the webhook URL for the bot"""
    webhook_url = f"https://textspeechbot.onrender.com/webhook/{TOKEN}"
    url = f"{TELEGRAM_API_URL}/setWebhook"
    response = requests.post(url, json={"url": webhook_url})
    print(f"Webhook set response: {response.json()}")
    return response.json()

if __name__ == "__main__":
    # Set webhook when starting
    set_webhook()
    
    # Run Flask server
    app.run(host='0.0.0.0', port=PORT, debug=False)
