from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from bot_engine import ChatbotEngine

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = ChatbotEngine()
try:
    bot.load_model()
    bot.load_data()
    logger.info("Chatbot engine loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load chatbot engine: {e}")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Please say something."}), 400

        # Simple rule-based greetings
        greetings = ["hi", "hello", "hey", "good morning", "good evening"]
        if user_message.lower() in greetings:
            return jsonify({"reply": "Hello! How can I assist you today?"})

        # Use bot_engine for other queries
        reply = bot.get_response(user_message)
        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble understanding. Try again later."}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"reply": "Chat session reset."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
