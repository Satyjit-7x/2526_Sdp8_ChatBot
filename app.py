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


# In-memory session store for pending actions
# Key: user_id (not really available in simple setup, so we might need a singleton or IP based)
# For this simple demo, we'll use a global variable. In production, use Redis or session cookies.
pending_confirmations = {}

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        user_id = request.remote_addr # Simple user identification
        
        if not user_message:
            return jsonify({"reply": "Please say something."}), 400

        # Simple rule-based greetings
        greetings = ["hi", "hello", "hey", "good morning", "good evening"]
        if user_message.lower() in greetings:
            return jsonify({"reply": "Hello! How can I assist you today?"})

        # Check for pending confirmation
        pending_action = pending_confirmations.get(user_id)
        
        # Use bot_engine
        # context_data is legacy dummy frontend data, can be ignored now that we have real DB
        # context_data = data.get("orders", []) 
        
        reply = bot.get_response(user_message, pending_action=pending_action)
        
        # Check if reply is a JSON string indicating confirmation needed
        import json
        try:
            parsed_reply = json.loads(reply)
            if isinstance(parsed_reply, dict) and parsed_reply.get("requires_confirmation"):
                pending_confirmations[user_id] = parsed_reply.get("sql")
                return jsonify({"reply": parsed_reply.get("message")})
        except:
            pass # Not a special JSON response
            
        # If we had a pending action and now we got a normal reply (Process complete or Cancelled)
        if pending_action:
            pending_confirmations.pop(user_id, None)

        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble understanding. Try again later."}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"reply": "Chat session reset."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
