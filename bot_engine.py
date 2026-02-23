
import chromadb
from chromadb.utils import embedding_functions
import os
import sqlite3
import google.generativeai as genai
import json
import re
import random
from datetime import date
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

# ── Status constants ────────────────────────────────────────────────────────
VALID_STATUSES = {
    "pending": "Pending",
    "delivered": "Delivered",
    "shipped": "Shipped",
    "ship": "Shipped",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "cancel": "Cancelled",
    "returned": "Returned",
    "return": "Returned",
}


class ChatbotEngine:
    def __init__(self, chroma_db_path="data/chroma_db", db_path="orders.db"):
        self.chroma_db_path = chroma_db_path
        self.db_path = db_path
        self.collection = None
        self.ef = None
        self.model = None
        if GENAI_API_KEY:
            self.model = genai.GenerativeModel('gemini-1.5-pro')

        # Initialize conversation history table if not exists
        self._init_conversation_table()

    # ════════════════════════════════════════════════════════════════════════
    # DATABASE HELPERS
    # ════════════════════════════════════════════════════════════════════════

    @contextmanager
    def _db(self):
        """Context manager for database connections — avoids repeated open/close boilerplate."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn, conn.cursor()
            conn.commit()
        finally:
            conn.close()

    def _db_fetch_all(self, sql, params=()):
        """Run a SELECT and return all rows."""
        with self._db() as (conn, cur):
            cur.execute(sql, params)
            return cur.fetchall()

    def _db_fetch_one(self, sql, params=()):
        """Run a SELECT and return the first row (or None)."""
        with self._db() as (conn, cur):
            cur.execute(sql, params)
            return cur.fetchone()

    def _db_run(self, sql, params=()):
        """Run an INSERT/UPDATE/DELETE."""
        with self._db() as (conn, cur):
            cur.execute(sql, params)

    # ════════════════════════════════════════════════════════════════════════
    # GEMINI HELPER
    # ════════════════════════════════════════════════════════════════════════

    def _ask_gemini(self, prompt, fallback=""):
        """Call Gemini and return text. On failure, return *fallback*."""
        if not self.model:
            return fallback
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini error: {e}")
            return fallback

    # ════════════════════════════════════════════════════════════════════════
    # STATUS HELPER
    # ════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_status(text):
        """Return the canonical status string if any status keyword is found in *text*, else None."""
        text_lower = text.lower()
        for keyword, canonical in VALID_STATUSES.items():
            if keyword in text_lower:
                return canonical
        return None

    # ════════════════════════════════════════════════════════════════════════
    # MODEL / DATA LOADING
    # ════════════════════════════════════════════════════════════════════════

    def load_model(self):
        print("Loading SentenceTransformer model (all-MiniLM-L6-v2) for ChromaDB...")
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def load_data(self):
        print(f"Connecting to ChromaDB at {self.chroma_db_path}...")
        client = chromadb.PersistentClient(path=self.chroma_db_path)
        try:
            self.collection = client.get_collection(name="chatbot_qa", embedding_function=self.ef)
            print(f"Connected to collection 'chatbot_qa'. contain {self.collection.count()} documents.")
        except Exception as e:
            print(f"Error connecting to collection: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CONVERSATION HISTORY
    # ════════════════════════════════════════════════════════════════════════

    def _init_conversation_table(self):
        """Initialize conversation history table if it doesn't exist."""
        try:
            self._db_run('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    sql_executed TEXT,
                    operation_type TEXT,
                    affected_items TEXT
                )
            ''')
            # Indices are created separately because _db_run commits after 1 statement
            self._db_run('''
                CREATE INDEX IF NOT EXISTS idx_session_timestamp
                ON conversation_history(session_id, timestamp DESC)
            ''')
            self._db_run('''
                CREATE INDEX IF NOT EXISTS idx_session_id
                ON conversation_history(session_id)
            ''')
        except Exception as e:
            print(f"Warning: Could not initialize conversation table: {e}")

    def save_conversation(self, session_id, user_msg, bot_response, sql=None, op_type=None, affected_items=None):
        """Save conversation to history."""
        try:
            self._db_run(
                '''INSERT INTO conversation_history
                   (session_id, user_message, bot_response, sql_executed, operation_type, affected_items)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (session_id, user_msg, bot_response, sql, op_type, affected_items),
            )
        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")

    def get_recent_context(self, session_id, limit=10):
        """Retrieve recent conversation history for context."""
        try:
            rows = self._db_fetch_all(
                '''SELECT user_message, bot_response, operation_type, affected_items, timestamp
                   FROM conversation_history WHERE session_id = ?
                   ORDER BY timestamp DESC LIMIT ?''',
                (session_id, limit),
            )
            return list(reversed(rows))
        except Exception as e:
            print(f"Warning: Could not retrieve context: {e}")
            return []

    def format_context_for_llm(self, context_list):
        """Format conversation context for LLM prompts."""
        if not context_list:
            return ""
        lines = ["\n\nRecent conversation history:"]
        for user_msg, bot_resp, op_type, affected, _ts in context_list:
            lines.append(f"User: {user_msg}")
            if op_type and affected:
                lines.append(f"Bot: {bot_resp} [Action: {op_type}, Items: {affected}]")
            else:
                lines.append(f"Bot: {bot_resp}")
        return "\n".join(lines)

    # ════════════════════════════════════════════════════════════════════════
    # PRODUCT MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════

    def get_all_categories(self):
        """Get all unique product categories."""
        try:
            rows = self._db_fetch_all("SELECT DISTINCT category FROM products ORDER BY category")
            return [r[0] for r in rows]
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def get_products_by_category(self, category):
        """Get all products in a specific category."""
        try:
            return self._db_fetch_all(
                "SELECT product_id, name, description, price, category FROM products WHERE category = ? ORDER BY price",
                (category,),
            )
        except Exception as e:
            print(f"Error fetching products by category: {e}")
            return []

    def search_products(self, search_term):
        """Search products by name or description."""
        try:
            pattern = f"%{search_term}%"
            return self._db_fetch_all(
                """SELECT product_id, name, description, price, category FROM products
                   WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
                   ORDER BY name""",
                (pattern, pattern),
            )
        except Exception as e:
            print(f"Error searching products: {e}")
            return []

    def get_product_by_id(self, product_id):
        """Get product details by ID."""
        try:
            return self._db_fetch_one(
                "SELECT product_id, name, description, price, category FROM products WHERE product_id = ?",
                (product_id,),
            )
        except Exception as e:
            print(f"Error fetching product: {e}")
            return None

    # ── Single order-creation entry point ────────────────────────────────
    def create_order(self, product_id=None, product_name_search=None, quantity=1, session_id="default"):
        """Create an order by product ID **or** by a product-name search.

        Returns a dict with 'status' ('success' | 'error') and relevant details.
        """
        # Resolve the product
        product = None
        if product_id is not None:
            product = self.get_product_by_id(product_id)
        elif product_name_search:
            # Exact match first, then partial
            product = self._db_fetch_one(
                "SELECT product_id, name, description, price, category FROM products WHERE LOWER(name) = LOWER(?)",
                (product_name_search,),
            )
            if not product:
                product = self._db_fetch_one(
                    "SELECT product_id, name, description, price, category FROM products WHERE LOWER(name) LIKE LOWER(?)",
                    (f"%{product_name_search}%",),
                )

        if not product:
            return {"status": "error", "message": f"Product not found"}

        pid, name, _desc, price, category = product
        order_id = f"ORD{random.randint(100, 999)}"
        today = date.today().strftime('%Y-%m-%d')
        total_price = price * quantity

        try:
            self._db_run(
                """INSERT INTO orders (order_id, session_id, product_id, product_name, price, quantity, order_date, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (order_id, session_id, pid, name, total_price, quantity, today, 'Pending'),
            )
            return {
                "status": "success",
                "order_id": order_id,
                "product_name": name,
                "price": total_price,
                "quantity": quantity,
                "category": category,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ════════════════════════════════════════════════════════════════════════
    # FORMATTING HELPERS (Gemini‑enhanced)
    # ════════════════════════════════════════════════════════════════════════

    def format_products_with_gemini(self, products, category=None, search_term=None):
        """Format product list into readable markdown."""
        if not products:
            return "No products found."

        formatted = f"\n📦 Available Products{f' in {category}' if category else ''}:\n\n"
        for i, (product_id, name, description, price, cat) in enumerate(products, 1):
            formatted += f"{i}. **{name}**\n"
            formatted += f"   💰 Price: ₹{price}\n"
            formatted += f"   📝 {description}\n"
            formatted += f"   🏷️  Category: {cat}\n"
            formatted += f"   ID: {product_id}\n\n"
        return formatted

    def _format_buy_confirmation(self, user_query, result):
        """Build a friendly Gemini-powered confirmation after a purchase, with fallback."""
        prompt = f"""User wants to buy: {user_query}

Action completed:
- Order ID: {result['order_id']}
- Product: {result['product_name']}
- Category: {result['category']}
- Price: ₹{result['price']}
- Quantity: {result['quantity']}

Create a friendly confirmation message (2-3 sentences) that:
1. Confirms the order was placed
2. Mentions the order ID and product name
3. Includes next steps (like tracking or delivery info)
Keep it warm and conversational."""
        fallback = f"✅ Order {result['order_id']} for {result['product_name']} has been created! Your order is pending confirmation."
        return self._ask_gemini(prompt, fallback)

    def format_order_details_with_gemini(self, user_query, order_data, columns):
        """Format a single order lookup with Gemini for a rich, user-friendly response."""
        if not order_data:
            return "No order found with that ID."

        order_info = {col: order_data[0][i] for i, col in enumerate(columns)}

        # Fetch linked product details for richer description
        product_details = None
        pid = order_info.get('product_id')
        if pid:
            row = self._db_fetch_one(
                "SELECT name, description, category, price FROM products WHERE product_id = ?", (pid,)
            )
            if row:
                product_details = {'name': row[0], 'description': row[1], 'category': row[2], 'listed_price': row[3]}

        prompt = f"""User asked: "{user_query}"

Order Information:
- Order ID: {order_info.get('order_id', 'N/A')}
- Product Name: {order_info.get('product_name', 'N/A')}
- Price: ₹{order_info.get('price', 0)}
- Quantity: {order_info.get('quantity', 1)}
- Order Date: {order_info.get('order_date', 'N/A')}
- Status: {order_info.get('status', 'N/A')}
"""
        if product_details:
            prompt += f"""
Product Details:
- Description: {product_details['description']}
- Category: {product_details['category']}
- Current Price: ₹{product_details['listed_price']}
"""
        prompt += """
Create a friendly, informative response (3-4 sentences) that:
1. Describes what this order is about
2. Includes the order status and date
3. Provides the product description
4. If relevant, mentions next steps or helpful information
Keep it conversational and helpful!"""

        fallback = (
            f"**Order {order_info.get('order_id')}**\n"
            f"Product: {order_info.get('product_name')}\n"
            f"Price: ₹{order_info.get('price')}\n"
            f"Status: {order_info.get('status')}\n"
            f"Ordered on: {order_info.get('order_date')}\n"
        )
        if product_details:
            fallback += f"\n{product_details['description']}"

        return self._ask_gemini(prompt, fallback)

    def format_action_response_with_gemini(self, user_query, sql_query, sql_result):
        """Format SQL action results with Gemini for user-friendly responses."""
        # Get context from ChromaDB for relevance
        rag_context = ""
        try:
            if self.collection:
                results = self.collection.query(query_texts=[user_query], n_results=2)
                if results and results.get('documents') and results['documents'][0]:
                    rag_context = " ".join(results['documents'][0][:2])
        except Exception:
            pass

        sql_upper = sql_query.upper()
        if 'INSERT' in sql_upper:
            order_match = re.search(r"'(ORD\d+)'", sql_query)
            product_match = re.search(r"product.*?'([^']+)'", sql_query, re.IGNORECASE)
            order_id = order_match.group(1) if order_match else "your order"
            product = product_match.group(1) if product_match else "the product"
            prompt = (
                f'User said: "{user_query}"\n\n'
                f'Action: Order {order_id} for {product} was created successfully.\n\n'
                f'Relevant context: {rag_context}\n\n'
                'Create a brief (2-3 sentences), friendly confirmation that:\n'
                '1. Confirms the order was created\n'
                '2. Mentions the order ID and product name\n'
                '3. Includes helpful next steps from context if relevant\n'
                'Be conversational and concise!'
            )
            fallback = "✅ Order created successfully!"
        elif 'UPDATE' in sql_upper:
            prompt = (
                f'User said: "{user_query}"\n\n'
                f'Action: Order status was updated successfully.\n\n'
                f'Context: {rag_context}\n\n'
                'Create a brief (1-2 sentences) friendly confirmation of the update.'
            )
            fallback = "✅ Order updated successfully!"
        elif 'DELETE' in sql_upper:
            prompt = (
                f'User said: "{user_query}"\n\n'
                f'Action: Order was removed successfully.\n\n'
                f'Context: {rag_context}\n\n'
                'Create a brief (1-2 sentences) empathetic confirmation of the deletion.'
            )
            fallback = "✅ Order deleted successfully!"
        else:
            return "Done! Let me know if you need anything else."

        return self._ask_gemini(prompt, fallback)

    # ════════════════════════════════════════════════════════════════════════
    # SQL EXECUTION
    # ════════════════════════════════════════════════════════════════════════

    def execute_sql(self, sql):
        try:
            with self._db() as (conn, cur):
                cur.execute(sql)
                if sql.strip().upper().startswith("SELECT"):
                    columns = [d[0] for d in cur.description]
                    return {"type": "SELECT", "data": cur.fetchall(), "columns": columns}
                else:
                    return {"type": "ACTION", "status": "success"}
        except Exception as e:
            return {"type": "ERROR", "message": str(e)}

    # ════════════════════════════════════════════════════════════════════════
    # SQL / COMMAND GENERATION  (natural language → action)
    # ════════════════════════════════════════════════════════════════════════

    def generate_sql(self, user_query):
        """Generate SQL from user query using pattern matching."""
        query_lower = user_query.lower()
        categories = self.get_all_categories()

        # ── PRODUCT QUERIES (HIGHEST PRIORITY) ──────────────────────────

        # 1. Category match
        for category in categories:
            if category.lower() in query_lower:
                return f"PRODUCTS:category:{category}"

        # 2. Buy / purchase with product ID
        if any(w in query_lower for w in ['buy', 'purchase', 'want to buy']):
            id_match = re.search(r'(?:id|product|#)\s*(\d+)', query_lower)
            if id_match:
                return f"PRODUCTS:buy:{int(id_match.group(1))}"

            # Try to extract product name for search-based buy
            for trigger in ['buy', 'purchase', 'want to buy']:
                if trigger in query_lower:
                    parts = query_lower.split(trigger)
                    if len(parts) > 1:
                        name = parts[-1].strip()
                        for noise in ['the', 'a', 'an', 'please', 'product', 'products', 'item', 'this', 'me', 'a ']:
                            name = name.replace(noise, '').strip()
                        if name and len(name) > 1:
                            # Could be a category
                            for cat in categories:
                                if cat.lower() == name.lower():
                                    return f"PRODUCTS:category:{cat}"
                            return f"PRODUCTS:search_buy:{name}"

        # 3. Product listing / search (only when no 'order' keyword)
        if 'order' not in query_lower and any(w in query_lower for w in ['product', 'show', 'list', 'browse']):
            for word in ['show', 'list', 'browse', 'find', 'search']:
                if word in query_lower:
                    parts = query_lower.split(word)
                    if len(parts) > 1:
                        term = parts[-1].strip()
                        for noise in ['product', 'products', 'items', 'please', 'me', 'a ']:
                            term = term.replace(noise, '').strip()
                        if term and len(term) > 1:
                            return f"PRODUCTS:search:{term}"
            if any(w in query_lower for w in ['all products', 'product list', 'all items']):
                return "PRODUCTS:all"

        # ── ORDER OPERATIONS ────────────────────────────────────────────

        # DELETE
        if any(w in query_lower for w in ['delete', 'remove', 'cancel order']):
            return self._generate_delete_sql(query_lower)

        # CREATE / INSERT
        if any(w in query_lower for w in ['create', 'add', 'insert', 'new order']):
            return self._generate_create_sql(query_lower)

        # UPDATE
        if any(w in query_lower for w in ['update', 'change', 'modify', 'set', 'mark']):
            return self._generate_update_sql(query_lower)

        # SELECT / READ
        if any(w in query_lower for w in ['show', 'view', 'display', 'my orders', 'all orders',
                                           'which', 'what', 'any', 'how many']):
            return self._generate_select_sql(query_lower, user_query)

        return None

    # ── DELETE helper ────────────────────────────────────────────────────

    def _generate_delete_sql(self, query_lower):
        # Direct order-ID reference
        order_match = re.search(r'ord\d+', query_lower)
        if order_match:
            return f"DELETE FROM orders WHERE order_id = '{order_match.group(0).upper()}'"

        # Try to extract product name
        product = self._extract_product_name(query_lower, ['delete', 'remove', 'cancel'])

        # If no useful product name, try status-only delete
        if not product or len(product) < 3:
            return self._delete_by_status_or_clarify(query_lower)

        # Find matching orders
        matches = self._db_fetch_all(
            "SELECT order_id, product_name, order_date, status FROM orders WHERE LOWER(product_name) LIKE ?",
            (f'%{product.lower()}%',),
        )
        if not matches:
            return None
        if len(matches) == 1:
            return f"DELETE FROM orders WHERE order_id = '{matches[0][0]}'"

        # Multiple matches — try qualifiers (status / date)
        return self._resolve_by_qualifier(query_lower, matches, "DELETE")

    # ── CREATE helper ────────────────────────────────────────────────────

    def _generate_create_sql(self, query_lower):
        print(f"[DEBUG] CREATE pattern matched for: {query_lower}")

        product_id = None
        product_name = None

        id_match = re.search(r'(?:product|id)\s*#?\s*(\d+)', query_lower)
        if id_match:
            product_id = int(id_match.group(1))
        else:
            for kw in ['for', 'add', 'create order for', 'order for', 'order']:
                if kw in query_lower:
                    parts = query_lower.split(kw, 1)
                    if len(parts) > 1:
                        product_name = parts[1].strip()
                        for noise in ['a ', 'an ', 'the ', 'order', 'please', ',', '.']:
                            product_name = product_name.replace(noise, '').strip()
                        if product_name and len(product_name) > 2:
                            break

        print(f"[DEBUG] Extracted - product_name: '{product_name}', product_id: {product_id}")

        # Look up product
        product = None
        if product_id:
            product = self._db_fetch_one(
                "SELECT product_id, name, price FROM products WHERE product_id = ?", (product_id,)
            )
        elif product_name:
            product = self._db_fetch_one(
                "SELECT product_id, name, price FROM products WHERE LOWER(name) = LOWER(?)", (product_name,)
            )
            if not product:
                product = self._db_fetch_one(
                    "SELECT product_id, name, price FROM products WHERE LOWER(name) LIKE LOWER(?)",
                    (f'%{product_name}%',),
                )

        if not product:
            print("[DEBUG] Product not found in database")
            return None

        db_pid, db_name, db_price = product
        order_id = f"ORD{random.randint(100, 999):03d}"
        today = date.today().strftime('%Y-%m-%d')

        sql = (
            f"INSERT INTO orders (order_id, session_id, product_id, product_name, price, quantity, order_date, status) "
            f"VALUES ('{order_id}', 'default', {db_pid}, '{db_name}', {db_price}, 1, '{today}', 'Pending')"
        )
        print(f"[DEBUG] Generated SQL: {sql}")
        return sql

    # ── UPDATE helper ────────────────────────────────────────────────────

    def _generate_update_sql(self, query_lower):
        new_status = self._extract_status(query_lower)
        if not new_status:
            print("[DEBUG] Could not detect status to update to")
            return None

        order_match = re.search(r'ord\d+', query_lower)
        if order_match:
            return f"UPDATE orders SET status = '{new_status}' WHERE order_id = '{order_match.group(0).upper()}'"

        # Qualifiers: latest / oldest / my order
        order_id = self._resolve_order_by_recency(query_lower)
        if order_id:
            return f"UPDATE orders SET status = '{new_status}' WHERE order_id = '{order_id}'"

        print("[DEBUG] Could not determine which order to update")
        return None

    # ── SELECT helper ────────────────────────────────────────────────────

    def _generate_select_sql(self, query_lower, original_query):
        # Specific order by ID
        order_match = re.search(r'ord\d+', query_lower)
        if order_match:
            oid = order_match.group(0).upper()
            return f"SELECT order_id, product_id, product_name, price, quantity, order_date, status FROM orders WHERE order_id = '{oid}'"

        # Filter by status
        status = self._extract_status(query_lower)
        if status:
            return f"SELECT order_id, product_name, order_date, status, price, quantity FROM orders WHERE status = '{status}'"

        # Default: all orders
        if any(w in query_lower for w in ['orders', 'items']):
            return "SELECT order_id, product_name, order_date, status, price, quantity FROM orders"

        return "SELECT order_id, product_name, order_date, status, price, quantity FROM orders"

    # ── Shared sub-helpers ───────────────────────────────────────────────

    @staticmethod
    def _extract_product_name(query_lower, trigger_words):
        """Pull a product name out of the query, stripping qualifiers and generic words."""
        for word in trigger_words:
            if word in query_lower:
                parts = query_lower.split(word)
                if len(parts) > 1:
                    rest = parts[1].strip()
                    # Remove phrase qualifiers
                    for q in ['which is', 'that is', 'with status', 'with the status']:
                        if q in rest:
                            rest = rest.split(q)[0].strip()
                    # Remove qualifier & generic keywords
                    skip = {'latest', 'newest', 'recent', 'oldest', 'first',
                            'pending', 'delivered', 'shipped', 'returned',
                            'product', 'order', 'item', 'thing', 'entry', 'record'}
                    words = [w for w in rest.split() if w.lower() not in skip]
                    if words:
                        return ' '.join(words[:2])
        return None

    def _delete_by_status_or_clarify(self, query_lower):
        """Handle delete when only a status is given (no product name)."""
        status = self._extract_status(query_lower)
        if not status:
            return None

        matches = self._db_fetch_all(
            "SELECT order_id, product_name, order_date, status FROM orders WHERE status = ?", (status,)
        )
        if not matches:
            return None
        if len(matches) == 1:
            return f"DELETE FROM orders WHERE order_id = '{matches[0][0]}'"

        options = [f"{m[1]} ({m[0]})" for m in matches]
        msg = (
            f"I found {len(matches)} {status.lower()} orders: {', '.join(options)}. "
            "Which one would you like to delete? Please specify the product name or order ID."
        )
        return f"CLARIFY:{msg}"

    def _resolve_by_qualifier(self, query_lower, matches, operation):
        """Disambiguate among multiple matches using status or date qualifiers."""
        # Status qualifier
        status = self._extract_status(query_lower)
        if status:
            for m in matches:
                if m[3] == status:
                    return f"{operation} FROM orders WHERE order_id = '{m[0]}'"

        # Date qualifier
        if any(w in query_lower for w in ['latest', 'newest', 'recent']):
            best = sorted(matches, key=lambda x: x[2], reverse=True)[0]
            return f"{operation} FROM orders WHERE order_id = '{best[0]}'"
        if any(w in query_lower for w in ['oldest', 'first']):
            best = sorted(matches, key=lambda x: x[2])[0]
            return f"{operation} FROM orders WHERE order_id = '{best[0]}'"

        return None

    def _resolve_order_by_recency(self, query_lower):
        """Return an order_id based on recency keywords (latest/oldest/my order)."""
        if any(w in query_lower for w in ['latest', 'last', 'recent']):
            row = self._db_fetch_one("SELECT order_id FROM orders ORDER BY order_date DESC LIMIT 1")
            return row[0] if row else None
        if any(w in query_lower for w in ['oldest', 'first']):
            row = self._db_fetch_one("SELECT order_id FROM orders ORDER BY order_date ASC LIMIT 1")
            return row[0] if row else None
        if any(w in query_lower for w in ['my order', 'the order']):
            row = self._db_fetch_one("SELECT order_id FROM orders ORDER BY order_date DESC LIMIT 1")
            return row[0] if row else None
        return None

    # ════════════════════════════════════════════════════════════════════════
    # AGENTIC CONTEXT RESOLUTION
    # ════════════════════════════════════════════════════════════════════════

    # Phrases that indicate the user is referring to something from context
    _CONTEXT_TRIGGERS = [
        'that order', 'that one', 'this order', 'this one',
        'the order', 'same order', 'it', 'that', 'this',
        'the same', 'above order', 'previous order',
    ]

    def _resolve_context_references(self, user_query, context):
        """If the query contains vague references like 'that order' or 'it',
        resolve them to the most recently mentioned order ID from conversation history.

        Returns the (possibly rewritten) user_query.
        """
        if not context:
            return user_query

        query_lower = user_query.lower().strip()

        # Only resolve if user already has an action word + vague reference
        action_words = ['delete', 'remove', 'cancel', 'update', 'change', 'modify',
                        'mark', 'set', 'show', 'what is', 'tell me about', 'details of']
        has_action = any(w in query_lower for w in action_words)
        has_vague_ref = any(t in query_lower for t in self._CONTEXT_TRIGGERS)

        # Also handle bare-action queries like just "delete it"
        if not (has_action and has_vague_ref):
            return user_query

        # Already has a concrete order ID — no need to resolve
        if re.search(r'ord\d+', query_lower):
            return user_query

        # Scan conversation history (most recent first) for an order ID
        last_order_id = None
        last_product_name = None

        for user_msg, bot_resp, op_type, affected, _ts in reversed(context):
            # 1. Check bot response for order IDs  (e.g. "Order ORD007")
            oid_match = re.search(r'(ORD\d+)', bot_resp, re.IGNORECASE)
            if oid_match:
                last_order_id = oid_match.group(1).upper()
                break

            # 2. Check user message for order IDs
            oid_match = re.search(r'(ord\d+)', user_msg, re.IGNORECASE)
            if oid_match:
                last_order_id = oid_match.group(1).upper()
                break

            # 3. Check affected_items JSON
            if affected:
                try:
                    items = json.loads(affected) if affected.startswith('[') else [affected]
                    for item in items:
                        oid = re.search(r'(ORD\d+)', str(item), re.IGNORECASE)
                        if oid:
                            last_order_id = oid.group(1).upper()
                            break
                except Exception:
                    pass
                if last_order_id:
                    break

            # 4. Try to extract product name from bot response
            prod_match = re.search(r'Product:\s*(.+)', bot_resp)
            if prod_match and not last_product_name:
                last_product_name = prod_match.group(1).strip()

        if last_order_id:
            # Replace the vague reference with the concrete order ID
            for trigger in sorted(self._CONTEXT_TRIGGERS, key=len, reverse=True):
                if trigger in query_lower:
                    resolved = user_query.lower().replace(trigger, last_order_id.lower())
                    print(f"[Context] Resolved '{user_query}' → '{resolved}' (found {last_order_id} in history)")
                    return resolved
        elif last_product_name:
            for trigger in sorted(self._CONTEXT_TRIGGERS, key=len, reverse=True):
                if trigger in query_lower:
                    resolved = user_query.lower().replace(trigger, last_product_name.lower())
                    print(f"[Context] Resolved '{user_query}' → '{resolved}' (found product '{last_product_name}' in history)")
                    return resolved

        return user_query

    # ════════════════════════════════════════════════════════════════════════
    # MAIN RESPONSE DISPATCHER
    # ════════════════════════════════════════════════════════════════════════

    def get_response(self, user_query, threshold=None, context_data=None,
                     pending_action=None, pending_items=None, session_id="default"):
        # 0. Conversation context
        context = self.get_recent_context(session_id, limit=10)
        context_str = self.format_context_for_llm(context)

        # ── 1. Memory query (about past actions) ────────────────────────
        if self._handle_memory_query(user_query, context, session_id):
            return self._handle_memory_query(user_query, context, session_id)

        # ── 2. Confirmation flow ────────────────────────────────────────
        if pending_action:
            return self._handle_confirmation(user_query, pending_action, pending_items, session_id)

        # ── 2.5. Clarification follow-up ────────────────────────────────
        if context:
            last_user_msg, last_bot_resp, last_op_type, last_affected, last_ts = context[-1]
            if last_op_type == "CLARIFY_REQUEST":
                order_match = re.search(r'ord\d+', user_query.lower().strip())
                if order_match or len(user_query.strip().split()) <= 3:
                    user_query = f"delete {user_query}"
                    print(f"[Context] Detected clarification follow-up, treating as: '{user_query}'")

        # ── 2.7. Resolve vague references ('that order', 'it', etc.) ────
        user_query = self._resolve_context_references(user_query, context)

        # ── 3. SQL / product operations ─────────────────────────────────
        sql_keywords = [
            "create", "add", "insert", "update", "change", "modify",
            "delete", "remove", "cancel order",
            "show all", "list all", "list my", "show my", "view", "display",
            "which", "what", "how many", "any",
            "pending", "delivered", "shipped", "returned",
            "products", "orders", "order", "product", "items", "buy", "purchase", "get",
        ]
        if any(k in user_query.lower() for k in sql_keywords):
            result = self._handle_sql_or_product(user_query, session_id)
            if result is not None:
                return result

        # ── 4. RAG + Gemini fallback ────────────────────────────────────
        if self.collection:
            try:
                results = self.collection.query(query_texts=[user_query], n_results=2)
                if results['metadatas'] and results['metadatas'][0]:
                    context_text = "\n\n".join(m['response'] for m in results['metadatas'][0])
                    rag_prompt = f"""
                    You are a helpful support chatbot for an e-commerce platform.
                    User Query: "{user_query}"

                    Here is some relevant information from our knowledge base:
                    {context_text}
                    {context_str}

                    Instructions:
                    1. Answer the user's question based on the knowledge base.
                    2. If relevant, use the conversation history to provide better context.
                    3. If the knowledge base doesn't have the answer, use your general knowledge to be helpful, but mention you are an AI assistant.
                    4. Be concise and professional.
                    5. Do NOT say "Based on the context provided". Just answer naturally.
                    """
                    fallback = results['metadatas'][0][0]['response']
                    answer = self._ask_gemini(rag_prompt, fallback)
                    self.save_conversation(session_id, user_query, answer, op_type="RAG_QUERY")
                    return answer
            except Exception as e:
                print(f"ChromaDB Error: {e}")

        fallback = "I'm not sure how to answer that. You can ask me to show orders, create an order, or ask about policies."
        self.save_conversation(session_id, user_query, fallback, op_type="FALLBACK")
        return fallback

    # ── Sub-dispatchers for get_response ─────────────────────────────────

    def _handle_memory_query(self, user_query, context, session_id):
        """Return a response if the user is asking about recent actions, else None."""
        memory_keywords = [
            "what did", "what product", "what item",
            "you removed", "you deleted", "you created", "you added", "you updated",
            "which product deleted", "which product removed",
            "which product ordered", "which product created",
            "ordered recently", "created recently", "added recently",
        ]
        if not any(k in user_query.lower() for k in memory_keywords) or not context:
            return None

        query_lower = user_query.lower()
        # Determine which operation types to look for
        op_map = {
            "DELETE": ["deleted", "removed", "you deleted", "you removed", "which product deleted"],
            "CREATE": ["created", "added", "ordered", "you created", "you added",
                       "which product ordered", "which product created", "ordered recently", "created recently"],
            "UPDATE": ["updated", "changed", "you updated", "you changed"],
        }
        show_ops = []
        for op, triggers in op_map.items():
            if any(t in query_lower for t in triggers):
                show_ops.append(op)
        if not show_ops:
            show_ops = ["DELETE", "CREATE", "UPDATE"]

        response_parts = []
        for user_msg, bot_resp, op_type, affected, _ts in reversed(context[-5:]):
            if affected and op_type in show_ops:
                try:
                    items = json.loads(affected) if affected.startswith('[') else [affected]
                except Exception:
                    items = [affected]
                label = {"DELETE": "Deleted", "CREATE": "Created", "UPDATE": "Updated"}.get(op_type, op_type)
                response_parts.append(f"{label}: {', '.join(items)}")

        if response_parts:
            answer = "Recent actions:\n" + "\n".join(response_parts)
        else:
            op_name = "create/update/delete" if len(show_ops) == 3 else show_ops[0].lower()
            answer = f"I don't see any recent {op_name} actions in your history."

        self.save_conversation(session_id, user_query, answer, op_type="MEMORY_QUERY")
        return answer

    def _handle_confirmation(self, user_query, pending_action, pending_items, session_id):
        """Handle yes/no confirmation for destructive operations."""
        lower = user_query.lower()
        if lower in ('yes', 'confirm', 'sure', 'ok'):
            result = self.execute_sql(pending_action)
            if result['type'] == 'ACTION':
                response = self.format_action_response_with_gemini(user_query, pending_action, result)
                op_type = "DELETE" if "DELETE" in pending_action.upper() else \
                          "UPDATE" if "UPDATE" in pending_action.upper() else \
                          "CREATE" if "INSERT" in pending_action.upper() else "ACTION"
                self.save_conversation(session_id, user_query, response,
                                       sql=pending_action, op_type=op_type, affected_items=pending_items)
                return response
            return f"Database error: {result['message']}"
        if lower in ('no', 'cancel', 'stop'):
            response = "Operation cancelled."
            self.save_conversation(session_id, user_query, response)
            return response
        return "Please answer 'yes' to confirm or 'no' to cancel."

    def _handle_sql_or_product(self, user_query, session_id):
        """Route product / order operations and return a response (or None to fall through)."""
        generated = self.generate_sql(user_query)
        if not generated:
            return None

        print(f"Generated SQL/Query: {generated}")

        # ── Product queries ──────────────────────────────────────────
        if generated.startswith("PRODUCTS:"):
            return self._dispatch_product(generated, user_query, session_id)

        # ── Clarification ────────────────────────────────────────────
        if generated.startswith("CLARIFY:"):
            msg = generated.replace("CLARIFY:", "").strip()
            self.save_conversation(session_id, user_query, msg, op_type="CLARIFY_REQUEST")
            return msg

        # ── SELECT ───────────────────────────────────────────────────
        if generated.strip().upper().startswith("SELECT"):
            return self._handle_select(generated, user_query, session_id)

        # ── INSERT / UPDATE / DELETE (action) ────────────────────────
        return self._handle_action(generated, user_query, session_id)

    # ── Product dispatcher ───────────────────────────────────────────────

    def _dispatch_product(self, command, user_query, session_id):
        """Handle PRODUCTS:* commands."""
        action = command.replace("PRODUCTS:", "")

        if action.startswith("category:"):
            category = action.replace("category:", "")
            products = self.get_products_by_category(category)
            response = self.format_products_with_gemini(products, category=category) if products else f"No products found in {category} category."
            self.save_conversation(session_id, user_query, response, op_type="PRODUCT_LIST")
            return response

        if action.startswith("search:"):
            term = action.replace("search:", "")
            products = self.search_products(term)
            response = self.format_products_with_gemini(products, search_term=term) if products else f"No products found matching '{term}'."
            self.save_conversation(session_id, user_query, response, op_type="PRODUCT_SEARCH")
            return response

        if action.startswith("buy:") or action.startswith("search_buy:"):
            return self._handle_buy(action, user_query, session_id)

        if action == "all":
            try:
                all_products = self._db_fetch_all(
                    "SELECT product_id, name, description, price, category FROM products"
                )
                response = self.format_products_with_gemini(all_products) if all_products else "No products available."
            except Exception as e:
                response = f"Error fetching products: {e}"
            self.save_conversation(session_id, user_query, response, op_type="PRODUCT_LIST_ALL")
            return response

        return None

    # ── Unified buy handler ──────────────────────────────────────────────

    def _handle_buy(self, action, user_query, session_id):
        """Handle both buy-by-ID and buy-by-name in a single flow."""
        if action.startswith("buy:"):
            pid = int(action.replace("buy:", ""))
            result = self.create_order(product_id=pid, session_id=session_id)
        else:
            # search_buy:
            name = action.replace("search_buy:", "")
            products = self.search_products(name)
            if not products:
                response = f"Sorry, I couldn't find a product matching '{name}'. Would you like to browse our catalog?"
                self.save_conversation(session_id, user_query, response)
                return response
            result = self.create_order(product_id=products[0][0], session_id=session_id)

        if result["status"] == "success":
            response = self._format_buy_confirmation(user_query, result)
            self.save_conversation(session_id, user_query, response,
                                   op_type="ORDER_CREATED",
                                   affected_items=json.dumps([result['order_id']]))
            return response

        response = f"Error: {result['message']}"
        self.save_conversation(session_id, user_query, response)
        return response

    # ── SELECT handler ───────────────────────────────────────────────────

    def _handle_select(self, sql, user_query, session_id):
        result = self.execute_sql(sql)
        if result['type'] == 'ERROR':
            response = f"Database error: {result['message']}"
            self.save_conversation(session_id, user_query, response)
            return response

        data, columns = result['data'], result['columns']

        if not data:
            response = "No records found in the database."
            self.save_conversation(session_id, user_query, response, sql=sql, op_type="READ")
            return response

        # Specific single-order lookup → Gemini detailed view
        order_match = re.search(r'ord\d+', user_query.lower())
        if order_match and len(data) == 1:
            response = self.format_order_details_with_gemini(user_query, data, columns)
            self.save_conversation(session_id, user_query, response, sql=sql, op_type="ORDER_DETAIL")
            return response

        # List view
        status = self._extract_status(user_query)
        status_msg = status.lower() if status else "total"

        affected_items = []
        if len(data) == 1:
            row = data[0]
            oid = row[columns.index('order_id')] if 'order_id' in columns else row[0]
            pname = row[columns.index('product_name')] if 'product_name' in columns else row[1]
            st = row[columns.index('status')] if 'status' in columns else row[-1]
            price = row[columns.index('price')] if 'price' in columns else None
            qty = row[columns.index('quantity')] if 'quantity' in columns else 1
            response = f"You have 1 {status_msg} order:\n📦 {pname} ({oid})\n   Status: {st}\n"
            if price:
                response += f"   Price: ₹{price} x {qty}\n"
            affected_items.append(oid)
        else:
            response = f"You have {len(data)} {status_msg} order{'s' if len(data) > 1 else ''}:\n\n"
            for row in data:
                oid = row[columns.index('order_id')] if 'order_id' in columns else row[0]
                pname = row[columns.index('product_name')] if 'product_name' in columns else row[1]
                odate = row[columns.index('order_date')] if 'order_date' in columns else row[2]
                st = row[columns.index('status')] if 'status' in columns else row[3]
                price = row[columns.index('price')] if 'price' in columns else None
                qty = row[columns.index('quantity')] if 'quantity' in columns else 1
                response += f"📦 {pname} ({oid})\n   Status: {st} | Date: {odate}"
                if price:
                    response += f" | ₹{price} x {qty}"
                response += "\n\n"
                affected_items.append(oid)

        self.save_conversation(session_id, user_query, response, sql=sql,
                               op_type="READ", affected_items=json.dumps(affected_items))
        return response

    # ── ACTION (INSERT / UPDATE / DELETE) handler ────────────────────────

    def _handle_action(self, sql, user_query, session_id):
        sql_upper = sql.upper()
        op_type = "DELETE" if "DELETE" in sql_upper else \
                  "UPDATE" if "UPDATE" in sql_upper else "CREATE"

        # For DELETE, pre-fetch affected items
        affected_items = []
        if op_type == "DELETE":
            where_match = re.search(r'WHERE\s+(.+)', sql, re.IGNORECASE)
            if where_match:
                try:
                    rows = self._db_fetch_all(
                        f"SELECT product_name, order_id FROM orders WHERE {where_match.group(1)}"
                    )
                    affected_items = [f"{p} ({oid})" for p, oid in rows]
                except Exception as e:
                    print(f"Error fetching items to delete: {e}")

        # CREATE → execute immediately
        if op_type == "CREATE":
            result = self.execute_sql(sql)
            if result['type'] == 'ACTION':
                response = self.format_action_response_with_gemini(user_query, sql, result)
                self.save_conversation(session_id, user_query, response, sql=sql,
                                       op_type=op_type, affected_items=json.dumps(affected_items))
                return response
            response = f"Error: {result.get('message', 'Unknown error')}"
            self.save_conversation(session_id, user_query, response)
            return response

        # UPDATE / DELETE → ask confirmation
        confirmation_msg = f"I am about to execute: `{sql}`. "
        if affected_items:
            confirmation_msg += f"This will affect: {', '.join(affected_items)}. "
        confirmation_msg += "Are you sure?"

        return json.dumps({
            "requires_confirmation": True,
            "message": confirmation_msg,
            "sql": sql,
            "affected_items": json.dumps(affected_items) if affected_items else None,
        })
