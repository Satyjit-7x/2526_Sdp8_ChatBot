from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from bot_engine import ChatbotEngine

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize chatbot engine
bot = ChatbotEngine()
try:
    bot.load_model()
    bot.load_data()
    logger.info("Chatbot engine loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load chatbot engine: {e}")


# =============================================================================
# CHAT ENDPOINT — All intelligence handled by bot_engine
# =============================================================================

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process chat message via the Gemini + RAG pipeline."""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        user_id = data.get("user_id", "default")

        if not user_message:
            return jsonify({"reply": "Please say something."}), 400

        session_id = str(user_id) if user_id else "default"
        reply = bot.get_response(user_message, session_id=session_id)

        return jsonify({"reply": reply})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble right now. Please try again!"}), 500


# =============================================================================
# ORDERS ENDPOINT
# =============================================================================

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Get all orders from database."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT order_id, product_name, price, order_date, status
            FROM orders ORDER BY order_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        orders = [{"orderId": r[0], "productName": r[1], "price": r[2], "orderDate": r[3], "status": r[4]} for r in rows]
        return jsonify({"orders": orders})
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return jsonify({"orders": [], "error": str(e)}), 500


# =============================================================================
# PRODUCTS ENDPOINTS
# =============================================================================

@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all available products, optionally filtered by category."""
    try:
        import sqlite3
        category = request.args.get('category')
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        if category:
            cursor.execute("SELECT product_id, name, description, price, category, in_stock FROM products WHERE category = ? AND in_stock = 1 ORDER BY name", (category,))
        else:
            cursor.execute("SELECT product_id, name, description, price, category, in_stock FROM products WHERE in_stock = 1 ORDER BY category, name")

        rows = cursor.fetchall()
        conn.close()

        products = [{"productId": r[0], "name": r[1], "description": r[2], "price": r[3], "category": r[4], "inStock": bool(r[5])} for r in rows]
        return jsonify({"products": products})
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({"products": [], "error": str(e)}), 500


@app.route("/api/products/categories", methods=["GET"])
def get_categories():
    """Get all product categories."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"categories": [r[0] for r in rows]})
    except Exception as e:
        return jsonify({"categories": [], "error": str(e)}), 500


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get specific product by ID."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, name, description, price, category, in_stock FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"productId": row[0], "name": row[1], "description": row[2], "price": row[3], "category": row[4], "inStock": bool(row[5])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/search", methods=["GET"])
def search_products():
    """Search products by name or description."""
    try:
        import sqlite3
        q = request.args.get('q', '').strip()
        if not q or len(q) < 2:
            return jsonify({"products": []})

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        p = f"%{q}%"
        cursor.execute("SELECT product_id, name, description, price, category, in_stock FROM products WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)) AND in_stock = 1 ORDER BY name", (p, p))
        rows = cursor.fetchall()
        conn.close()

        products = [{"productId": r[0], "name": r[1], "description": r[2], "price": r[3], "category": r[4], "inStock": bool(r[5])} for r in rows]
        return jsonify({"products": products})
    except Exception as e:
        return jsonify({"products": [], "error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"reply": "Chat session reset."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
