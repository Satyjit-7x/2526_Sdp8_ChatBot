from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import re
import random
from bot_engine import ChatbotEngine
from smart_formatter import SmartFormatter

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

# Initialize response formatter
formatter = SmartFormatter()
if formatter.is_available():
    logger.info("Smart formatter (Gemini) loaded successfully.")
else:
    logger.warning("Smart formatter not available - will use raw responses.")


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


        # Enhanced greeting detection with more patterns
        greeting_patterns = [
            r'\b(hi|hello|hey)\b',
            r'\b(hi there|hey there|hello there)\b',
            r'\b(good morning|good afternoon|good evening|good night)\b',
            r'\b(sup|whats up|what\'s up|howdy)\b',
        ]
        
        # Normalize: remove punctuation and extra spaces
        normalized_msg = re.sub(r'[!?.]+', '', user_message.lower()).strip()
        
        is_greeting = any(re.search(pattern, normalized_msg) for pattern in greeting_patterns)
        
        if is_greeting:
            # Vary responses based on greeting type
            if any(word in normalized_msg for word in ['morning']):
                return jsonify({"reply": "Good morning! ☀️ How can I help you with your orders today?"})
            elif any(word in normalized_msg for word in ['afternoon']):
                return jsonify({"reply": "Good afternoon! How can I assist you?"})
            elif any(word in normalized_msg for word in ['evening', 'night']):
                return jsonify({"reply": "Good evening! What can I do for you?"})
            elif any(word in normalized_msg for word in ['sup', 'whats up', "what's up"]):
                return jsonify({"reply": "Hey! What can I help you with?"})
            else:
                # Default friendly greeting
                greetings = [
                    "Hi there! 👋 How can I help you today?",
                    "Hello! I'm here to assist with your orders.",
                    "Hey! What can I do for you?",
                ]
                return jsonify({"reply": random.choice(greetings)})


        # Check for pending confirmation
        pending_action = pending_confirmations.get(user_id)
        pending_items = pending_confirmations.get(f"{user_id}_affected")
        
        # Use bot_engine with session_id and pending_items
        reply = bot.get_response(user_message, pending_action=pending_action, pending_items=pending_items, session_id=user_id)
        
        # Check if reply is a JSON string indicating confirmation needed
        import json
        try:
            parsed_reply = json.loads(reply)
            if isinstance(parsed_reply, dict) and parsed_reply.get("requires_confirmation"):
                pending_confirmations[user_id] = parsed_reply.get("sql")
                # Cache affected items for use after confirmation
                if parsed_reply.get("affected_items"):
                    pending_confirmations[f"{user_id}_affected"] = parsed_reply.get("affected_items")
                return jsonify({"reply": parsed_reply.get("message")})
        except:
            pass # Not a special JSON response
            
        # If we had a pending action and now we got a normal reply (Process complete or Cancelled)
        if pending_action:
            pending_confirmations.pop(user_id, None)
            pending_confirmations.pop(f"{user_id}_affected", None)  # Clean up cache

        # Format the response using Gemini for better user experience
        formatted_reply = formatter.format_response(user_message, reply)
        
        return jsonify({"reply": formatted_reply})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble understanding. Try again later."}), 500

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Get all orders from database for frontend display"""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT order_id, product_name, price, order_date, status 
            FROM orders 
            ORDER BY order_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                "orderId": row[0],
                "productName": row[1],
                "price": row[2],
                "orderDate": row[3],
                "status": row[4]
            })
        
        return jsonify({"orders": orders})
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return jsonify({"orders": [], "error": str(e)}), 500

@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all available products from database"""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, name, description, price, category, in_stock 
            FROM products 
            WHERE in_stock = 1
            ORDER BY category, name
        """)
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                "productId": row[0],
                "name": row[1],
                "description": row[2],
                "price": row[3],
                "category": row[4],
                "inStock": bool(row[5])
            })
        
        return jsonify({"products": products})
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify({"products": [], "error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"reply": "Chat session reset."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
