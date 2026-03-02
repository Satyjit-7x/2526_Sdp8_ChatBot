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
        role = data.get("role", "user")

        if not user_message:
            return jsonify({"reply": "Please say something."}), 400

        session_id = str(user_id) if user_id else "default"
        reply = bot.get_response(user_message, session_id=session_id, role=role)

        return jsonify({"reply": reply})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "I'm having trouble right now. Please try again!"}), 500


# =============================================================================
# ORDERS ENDPOINT
# =============================================================================

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Get all orders from database with creator info."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, o.product_name, o.price, o.order_date, o.status, o.session_id,
                   COALESCE(u.name, 'Unknown') as creator_name, COALESCE(u.email, '') as creator_email
            FROM orders o
            LEFT JOIN users u ON CAST(o.session_id AS TEXT) = CAST(u.user_id AS TEXT)
            ORDER BY o.order_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        orders = [{
            "orderId": r[0], "productName": r[1], "price": r[2],
            "orderDate": r[3], "status": r[4],
            "creatorName": r[6], "creatorEmail": r[7]
        } for r in rows]
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


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order_status(order_id):
    """Update order status (admin only)."""
    try:
        import sqlite3
        data = request.get_json()
        new_status = data.get("status", "").strip()

        valid = ['Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
        if new_status not in valid:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid)}"}), 400

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Order not found"}), 404

        cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "order_id": order_id, "status": new_status})
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    """Delete an order (admin)."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Order not found"}), 404
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "order_id": order_id})
    except Exception as e:
        logger.error(f"Error deleting order: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Get dashboard statistics for admin panel."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
        total_products = cursor.fetchone()[0]

        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
        except Exception:
            total_users = 0

        cursor.execute("SELECT SUM(price * quantity) FROM orders")
        total_revenue = cursor.fetchone()[0] or 0

        conn.close()

        return jsonify({
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "totalUsers": total_users,
            "totalRevenue": round(total_revenue, 2),
            "statusCounts": status_counts
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    """Get all registered users (admin only)."""
    try:
        import sqlite3
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.email, u.name, u.role, u.created_at,
                   COUNT(o.order_id) as order_count
            FROM users u
            LEFT JOIN orders o ON CAST(u.user_id AS TEXT) = CAST(o.session_id AS TEXT)
            GROUP BY u.user_id
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        users = [{
            "userId": r[0], "email": r[1], "name": r[2],
            "role": r[3] or 'user', "createdAt": r[4], "orderCount": r[5]
        } for r in rows]
        return jsonify({"users": users})
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"users": [], "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
