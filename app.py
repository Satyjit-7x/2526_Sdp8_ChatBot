from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import re
import random
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


# =============================================================================
# CHAT ENDPOINT
# =============================================================================

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process chat message — accepts message and optional user_id for session tracking"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        user_id = data.get("user_id", "default")  # Optional, defaults to "default"
        
        if not user_message:
            return jsonify({"reply": "Please say something."}), 400
        
        # Enhanced greeting detection
        greeting_patterns = [
            r'\b(hi|hello|hey|hiya|yo)\b',
            r'\b(hi there|hey there|hello there)\b',
            r'\b(good morning|good afternoon|good evening|good night)\b',
            r'\b(sup|whats up|what\'s up|howdy|wassup|heya)\b',
            r'^(greetings|salutations)\b',
        ]
        
        normalized_msg = re.sub(r'[!?.]+', '', user_message.lower()).strip()
        normalized_msg = re.sub(r'\s+', ' ', normalized_msg)
        
        is_standalone_greeting = any(re.search(pattern, normalized_msg) for pattern in greeting_patterns)
        if is_standalone_greeting:
            query_keywords = ['order', 'buy', 'show', 'list', 'delete', 'update', 'create', 'product']
            has_other_query = any(keyword in normalized_msg for keyword in query_keywords)
            is_standalone_greeting = not has_other_query
        
        if is_standalone_greeting:
            if any(word in normalized_msg for word in ['morning']):
                return jsonify({"reply": "Good morning! ☀️ How can I help you with your orders today?"})
            elif any(word in normalized_msg for word in ['afternoon']):
                return jsonify({"reply": "Good afternoon! 🌤️ How can I assist you?"})
            elif any(word in normalized_msg for word in ['evening', 'night']):
                return jsonify({"reply": "Good evening! 🌙 What can I do for you?"})
            elif any(word in normalized_msg for word in ['sup', 'whats up', "what's up", 'wassup']):
                return jsonify({"reply": "Hey! What can I help you with? 👋"})
            else:
                greetings = [
                    "Hi there! 👋 How can I help you today?",
                    "Hello! I'm here to assist with your orders and products.",
                    "Hey! What can I do for you?",
                    "Hi! Looking for something specific?",
                ]
                return jsonify({"reply": random.choice(greetings)})
        
        # Get response from bot engine — use user_id as session_id for conversation tracking
        session_id = str(user_id) if user_id else "default"
        reply = bot.get_response(user_message, session_id=session_id)
        
        return jsonify({"reply": reply})
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble understanding. Try again later."}), 500


# =============================================================================
# ORDERS ENDPOINT
# =============================================================================

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Get all orders from database"""
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
        logger.error(f"Error fetching orders: {e}")
        return jsonify({"orders": [], "error": str(e)}), 500


# =============================================================================
# PRODUCTS ENDPOINTS
# =============================================================================

@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all available products from database, optionally filtered by category"""
    try:
        import sqlite3
        category = request.args.get('category')
        
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT product_id, name, description, price, category, in_stock 
                FROM products 
                WHERE category = ? AND in_stock = 1
                ORDER BY name
            """, (category,))
        else:
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
        logger.error(f"Error fetching products: {e}")
        return jsonify({"products": [], "error": str(e)}), 500

@app.route("/api/products/categories", methods=["GET"])
def get_categories():
    """Get all product categories"""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category FROM products ORDER BY category
        """)
        rows = cursor.fetchall()
        conn.close()
        
        categories = [row[0] for row in rows]
        return jsonify({"categories": categories})
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({"categories": [], "error": str(e)}), 500

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get specific product by ID"""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, name, description, price, category, in_stock
            FROM products 
            WHERE product_id = ?
        """, (product_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"error": "Product not found"}), 404
        
        product = {
            "productId": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "category": row[4],
            "inStock": bool(row[5])
        }
        
        return jsonify(product)
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/search", methods=["GET"])
def search_products():
    """Search products by name or description"""
    try:
        import sqlite3
        search_term = request.args.get('q', '').strip()
        
        if not search_term or len(search_term) < 2:
            return jsonify({"products": []})
        
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        search_pattern = f"%{search_term}%"
        
        cursor.execute("""
            SELECT product_id, name, description, price, category, in_stock
            FROM products 
            WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
            AND in_stock = 1
            ORDER BY name
        """, (search_pattern, search_pattern))
        
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
        logger.error(f"Error searching products: {e}")
        return jsonify({"products": [], "error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"reply": "Chat session reset."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
