"""
E-Commerce Chatbot Engine — RAG + Gemini Architecture

Pipeline:
    1. Retrieve relevant context from ChromaDB (trained knowledge base / RAG)
    2. Classify intent using Gemini LLM (with keyword fallback)
    3. Execute database operations based on classified intent
    4. Format response using Gemini + RAG context for polished output
"""

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

# ── Configure Gemini ────────────────────────────────────────────────────────
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

# ── Constants ───────────────────────────────────────────────────────────────
VALID_STATUSES = {
    "pending": "Pending", "delivered": "Delivered", "shipped": "Shipped",
    "ship": "Shipped", "cancelled": "Cancelled", "canceled": "Cancelled",
    "cancel": "Cancelled", "returned": "Returned", "return": "Returned",
}

DB_SCHEMA = """Database Tables:
1. orders (order_id TEXT PK, session_id TEXT, product_id INT FK, product_name TEXT, price REAL, quantity INT DEFAULT 1, order_date TEXT, status TEXT)
   - status values: 'Pending', 'Delivered', 'Shipped', 'Cancelled', 'Returned'
2. products (product_id INT PK, name TEXT, description TEXT, price REAL, category TEXT, in_stock BOOL)"""


class ChatbotEngine:
    """Hybrid chatbot: ChromaDB RAG + Gemini LLM + SQLite for structured data."""

    def __init__(self, chroma_db_path="data/chroma_db", db_path="orders.db"):
        self.chroma_db_path = chroma_db_path
        self.db_path = db_path
        self.collection = None
        self.ef = None
        self.gemini_model = None
        self._pending = {}  # session_id -> {sql, params, description}

        if GENAI_API_KEY:
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")

        self._init_conversation_table()

    # ════════════════════════════════════════════════════════════════════════
    # DATABASE HELPERS
    # ════════════════════════════════════════════════════════════════════════

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn, conn.cursor()
            conn.commit()
        finally:
            conn.close()

    def _db_fetch_all(self, sql, params=()):
        with self._db() as (conn, cur):
            cur.execute(sql, params)
            return cur.fetchall()

    def _db_fetch_one(self, sql, params=()):
        with self._db() as (conn, cur):
            cur.execute(sql, params)
            return cur.fetchone()

    def _db_run(self, sql, params=()):
        with self._db() as (conn, cur):
            cur.execute(sql, params)

    # ════════════════════════════════════════════════════════════════════════
    # GEMINI HELPER
    # ════════════════════════════════════════════════════════════════════════

    def _ask_gemini(self, prompt, fallback=""):
        if not self.gemini_model:
            return fallback
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini Error] {e}")
            return fallback

    # ════════════════════════════════════════════════════════════════════════
    # MODEL / DATA LOADING (ChromaDB RAG)
    # ════════════════════════════════════════════════════════════════════════

    def load_model(self):
        print("Loading SentenceTransformer model for ChromaDB RAG...")
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def load_data(self):
        print(f"Connecting to ChromaDB at {self.chroma_db_path}...")
        client = chromadb.PersistentClient(path=self.chroma_db_path)
        try:
            self.collection = client.get_collection(name="chatbot_qa", embedding_function=self.ef)
            print(f"RAG collection loaded: {self.collection.count()} documents.")
        except Exception as e:
            print(f"ChromaDB Error: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CONVERSATION HISTORY
    # ════════════════════════════════════════════════════════════════════════

    def _init_conversation_table(self):
        try:
            self._db_run('''CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                operation_type TEXT,
                affected_items TEXT
            )''')
            self._db_run('CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_history(session_id, timestamp DESC)')
        except Exception as e:
            print(f"Warning: {e}")

    def _save(self, session_id, user_msg, bot_resp, op_type=None, affected=None):
        try:
            self._db_run(
                'INSERT INTO conversation_history (session_id, user_message, bot_response, operation_type, affected_items) VALUES (?, ?, ?, ?, ?)',
                (session_id, user_msg, bot_resp, op_type, affected)
            )
        except Exception:
            pass

    def _get_context(self, session_id, limit=8):
        try:
            rows = self._db_fetch_all(
                'SELECT user_message, bot_response, operation_type, affected_items FROM conversation_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?',
                (session_id, limit)
            )
            return list(reversed(rows))
        except Exception:
            return []

    def _format_context(self, context):
        if not context:
            return ""
        lines = ["\nRecent conversation:"]
        for user_msg, bot_resp, op_type, affected in context:
            lines.append(f"User: {user_msg}")
            short = bot_resp[:120] + "..." if len(bot_resp) > 120 else bot_resp
            lines.append(f"Bot: {short}")
            if op_type and affected:
                lines.append(f"  [Action: {op_type} → {affected}]")
        return "\n".join(lines)

    def _resolve_from_context(self, session_id):
        """Extract last-mentioned order_id and product_name from conversation history.
        Processes rows in recency order — most recent conversation entry wins."""
        try:
            rows = self._db_fetch_all(
                'SELECT operation_type, affected_items, bot_response, user_message '
                'FROM conversation_history '
                'WHERE session_id = ? '
                'ORDER BY timestamp DESC LIMIT 5',
                (session_id,)
            )
            # Process each row fully before moving to the next (recency wins)
            for _op, affected, bot_resp, user_msg in rows:
                # Try 1: structured affected_items like "Product Name (ORD123)"
                if affected:
                    m = re.match(r'^(.+?)\s*\((ORD\w+)\)$', affected)
                    if m:
                        return {"product_name": m.group(1).strip(), "order_id": m.group(2)}
                # Try 2: extract ORD### from user message or bot response
                for text in [user_msg, bot_resp]:
                    oid_match = re.search(r'(ORD\d+)', text or '', re.IGNORECASE)
                    if oid_match:
                        return {"product_name": None, "order_id": oid_match.group(1).upper()}
        except Exception as e:
            print(f"[Context Resolve Error] {e}")
        return {"product_name": None, "order_id": None}

    def _find_orders_by_product_name(self, product_name):
        """Find orders matching a product name (fuzzy match)."""
        try:
            # Try exact match first
            rows = self._db_fetch_all(
                "SELECT order_id, product_name, price, quantity, order_date, status "
                "FROM orders WHERE LOWER(product_name) = LOWER(?) "
                "ORDER BY order_date DESC",
                (product_name,)
            )
            if rows:
                return rows
            # Fall back to fuzzy match
            return self._db_fetch_all(
                "SELECT order_id, product_name, price, quantity, order_date, status "
                "FROM orders WHERE LOWER(product_name) LIKE LOWER(?) "
                "ORDER BY order_date DESC",
                (f"%{product_name}%",)
            )
        except Exception:
            return []

    # ════════════════════════════════════════════════════════════════════════
    # RAG — CHROMADB RETRIEVAL
    # ════════════════════════════════════════════════════════════════════════

    def _get_rag_context(self, query, n=3):
        if not self.collection:
            return ""
        try:
            results = self.collection.query(query_texts=[query], n_results=n)
            if results and results.get('metadatas') and results['metadatas'][0]:
                return "\n".join(m.get('response', '') for m in results['metadatas'][0] if m.get('response'))
        except Exception as e:
            print(f"[RAG Error] {e}")
        return ""

    # ════════════════════════════════════════════════════════════════════════
    # INTENT CLASSIFICATION — Gemini + Keyword Fallback
    # ════════════════════════════════════════════════════════════════════════

    def _classify_intent(self, user_query, context_str=""):
        prompt = f"""You are an intent classifier for an e-commerce chatbot.
{DB_SCHEMA}

Classify the user's message into ONE intent and extract entities.

Intents: GREETING, SHOW_ORDERS, ORDER_DETAIL, CREATE_ORDER, BUY_PRODUCT, UPDATE_ORDER, DELETE_ORDER, SHOW_PRODUCTS, MEMORY_QUERY, GENERAL_QUERY
{context_str}

IMPORTANT CONTEXT RULES:
- If the user says "delete that", "cancel it", "remove that order", "update it", etc., look at the conversation history to find which order they are referring to. Set refers_to_previous to true.
- If the user mentions a product NAME (e.g. "delete my gaming mouse order"), extract it as product_name.
- If the user provides an order ID like ORD123, extract it as order_id.
- If the conversation history mentions a specific order and the user refers to it with "that", "it", "this", resolve the order_id from the history.

User message: "{user_query}"

Respond with ONLY valid JSON:
{{"intent": "INTENT_NAME", "refers_to_previous": false, "entities": {{"order_id": null, "status": null, "product_name": null, "product_id": null, "search_term": null, "new_status": null}}}}"""

        resp = self._ask_gemini(prompt, fallback="")
        if resp:
            try:
                cleaned = re.sub(r'```json\s*|\s*```', '', resp).strip()
                match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                    if "intent" in parsed:
                        print(f"[Gemini Intent] {parsed['intent']} | refers_prev={parsed.get('refers_to_previous', False)} | {parsed.get('entities', {})}")
                        return parsed
            except (json.JSONDecodeError, AttributeError):
                pass

        return self._keyword_classify(user_query)

    def _keyword_classify(self, user_query):
        q = user_query.lower().strip()
        ent = {"order_id": None, "status": None, "product_name": None,
               "product_id": None, "search_term": None, "new_status": None}

        # General questions take priority (e.g., "return policy" ≠ returned orders)
        general_patterns = ['policy', 'how to', 'how do', 'what is', 'help me', 'tell me about',
                            'shipping', 'refund', 'contact', 'support', 'warranty', 'exchange',
                            'what day', 'what time', 'date today', 'who are you', 'what are you',
                            'what can you', 'about this', 'this platform', 'thank', 'thanks',
                            'bye', 'goodbye', 'see you', 'how are you', 'your name']
        if any(p in q for p in general_patterns):
            return {"intent": "GENERAL_QUERY", "entities": ent}

        oid = re.search(r'(ord\d+)', q, re.IGNORECASE)
        if oid:
            ent["order_id"] = oid.group(1).upper()

        for kw, canonical in VALID_STATUSES.items():
            if kw in q:
                ent["status"] = canonical
                break

        if re.match(r'^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening))', q):
            return {"intent": "GREETING", "entities": ent}

        if any(w in q for w in ['what did', 'you deleted', 'you removed', 'you created', 'recently']):
            return {"intent": "MEMORY_QUERY", "entities": ent}

        # Contextual references ("delete that", "cancel it", "remove that order")
        context_words = ['that', 'it', 'this', 'the order', 'that one', 'same', 'this one']
        has_context_ref = any(w in q for w in context_words) and not ent["order_id"]

        if any(w in q for w in ['delete', 'remove']) and ('order' in q or ent["order_id"] or has_context_ref):
            return {"intent": "DELETE_ORDER", "refers_to_previous": has_context_ref, "entities": ent}

        if any(w in q for w in ['update', 'change', 'modify', 'mark', 'set']) and ('order' in q or ent["order_id"] or has_context_ref):
            ent["new_status"] = ent.pop("status", None)
            return {"intent": "UPDATE_ORDER", "refers_to_previous": has_context_ref, "entities": ent}

        if any(w in q for w in ['buy', 'purchase', 'want to buy']):
            for trigger in ['buy', 'purchase']:
                if trigger in q:
                    parts = q.split(trigger, 1)
                    if len(parts) > 1:
                        name = re.sub(r'\b(the|a|an|please|me)\b', '', parts[1]).strip()
                        if name:
                            ent["product_name"] = name
            return {"intent": "BUY_PRODUCT", "entities": ent}

        if any(w in q for w in ['create order', 'new order', 'place order', 'add order']):
            for kw in ['for', 'order']:
                if kw in q:
                    parts = q.split(kw, 1)
                    if len(parts) > 1:
                        name = re.sub(r'\b(a|an|the|please|new)\b', '', parts[1]).strip()
                        if name and len(name) > 2:
                            ent["product_name"] = name
                            break
            return {"intent": "CREATE_ORDER", "entities": ent}

        if ent["order_id"]:
            return {"intent": "ORDER_DETAIL", "entities": ent}

        if any(w in q for w in ['product', 'browse', 'catalog', 'categor']):
            return {"intent": "SHOW_PRODUCTS", "entities": ent}

        if ent["status"] or any(w in q for w in ['orders', 'order list', 'my order']):
            return {"intent": "SHOW_ORDERS", "entities": ent}

        if any(w in q for w in ['show', 'list', 'display', 'view']):
            return {"intent": "SHOW_ORDERS" if 'order' in q else "SHOW_PRODUCTS", "entities": ent}

        return {"intent": "GENERAL_QUERY", "entities": ent}

    @staticmethod
    def _extract_status(text):
        for kw, canonical in VALID_STATUSES.items():
            if kw in text.lower():
                return canonical
        return None

    # ════════════════════════════════════════════════════════════════════════
    # PRODUCT HELPERS
    # ════════════════════════════════════════════════════════════════════════

    def get_all_categories(self):
        try:
            return [r[0] for r in self._db_fetch_all("SELECT DISTINCT category FROM products ORDER BY category")]
        except Exception:
            return []

    def _get_products(self, category=None, search_term=None):
        try:
            if category:
                return self._db_fetch_all(
                    "SELECT product_id, name, description, price, category FROM products WHERE LOWER(category) LIKE LOWER(?) AND in_stock = 1 ORDER BY price",
                    (f"%{category}%",))
            elif search_term:
                p = f"%{search_term}%"
                return self._db_fetch_all(
                    "SELECT product_id, name, description, price, category FROM products WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?)) AND in_stock = 1 ORDER BY name",
                    (p, p, p))
            else:
                return self._db_fetch_all(
                    "SELECT product_id, name, description, price, category FROM products WHERE in_stock = 1 ORDER BY category, name")
        except Exception:
            return []

    def _find_product(self, name=None, product_id=None):
        try:
            if product_id:
                return self._db_fetch_one("SELECT product_id, name, description, price, category FROM products WHERE product_id = ?", (product_id,))
            if name:
                row = self._db_fetch_one("SELECT product_id, name, description, price, category FROM products WHERE LOWER(name) = LOWER(?)", (name,))
                if row:
                    return row
                return self._db_fetch_one("SELECT product_id, name, description, price, category FROM products WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
        except Exception:
            pass
        return None

    # ════════════════════════════════════════════════════════════════════════
    # ORDER ACTIONS
    # ════════════════════════════════════════════════════════════════════════

    def _do_show_orders(self, entities):
        status = entities.get("status")
        if status:
            return self._db_fetch_all(
                "SELECT order_id, product_name, price, quantity, order_date, status FROM orders WHERE status = ? ORDER BY order_date DESC", (status,))
        return self._db_fetch_all(
            "SELECT order_id, product_name, price, quantity, order_date, status FROM orders ORDER BY order_date DESC")

    def _do_order_detail(self, entities):
        oid = entities.get("order_id")
        pname = entities.get("product_name")

        # If no order_id but product_name given, look up by product name
        if not oid and pname:
            matches = self._find_orders_by_product_name(pname)
            if not matches:
                return None
            if len(matches) > 1:
                items = [f"• {r[1]} (ID: **{r[0]}**) — ₹{r[2]} — {r[5]}" for r in matches]
                return f"I found {len(matches)} orders for '{pname}':\n" + "\n".join(items) + "\n\nWhich one would you like details for? Please specify the order ID."
            oid = matches[0][0]  # Single match — use its order_id

        if not oid:
            return None
        return self._db_fetch_one(
            "SELECT o.order_id, o.product_name, o.price, o.quantity, o.order_date, o.status, p.description, p.category "
            "FROM orders o LEFT JOIN products p ON o.product_id = p.product_id WHERE o.order_id = ?", (oid,))

    def _do_buy(self, entities, session_id):
        """Find the product and show details for confirmation — does NOT create the order yet."""
        product = self._find_product(name=entities.get("product_name"), product_id=entities.get("product_id"))
        if not product:
            search = entities.get("product_name") or entities.get("search_term")
            if search:
                prods = self._get_products(search_term=search)
                if prods:
                    return {"type": "suggestions", "products": prods[:5], "search": search}
            return {"type": "not_found", "search": search or "unknown"}

        pid, name, desc, price, category = product
        # Store pending buy — order will only be created on confirmation
        self._pending[session_id] = {
            "action": "BUY",
            "product_id": pid,
            "product_name": name,
            "description": desc,
            "price": price,
            "category": category,
            "desc": f"{name} (₹{price})"
        }
        return {
            "type": "confirm_buy",
            "product_name": name,
            "description": desc or "No description available",
            "price": price,
            "category": category
        }

    def _do_update(self, entities):
        oid = entities.get("order_id")
        pname = entities.get("product_name")
        new_status = entities.get("new_status") or entities.get("status")

        # If no order_id but product_name given, look up by product name
        if not oid and pname:
            matches = self._find_orders_by_product_name(pname)
            if not matches:
                return f"No orders found for '{pname}'."
            if len(matches) > 1:
                items = [f"• {r[1]} (ID: **{r[0]}**) — ₹{r[2]} — {r[5]}" for r in matches]
                return f"I found {len(matches)} orders for '{pname}':\n" + "\n".join(items) + "\n\nWhich one should I update? Please specify the order ID."
            oid = matches[0][0]

        if not oid:
            return "Which order would you like to update? Please specify an order ID (e.g., ORD123) or product name."
        if not new_status:
            return f"What status should I set for {oid}? Options: Pending, Shipped, Delivered, Cancelled, Returned"
        existing = self._db_fetch_one("SELECT order_id, product_name, status FROM orders WHERE order_id = ?", (oid,))
        if not existing:
            return f"Order {oid} not found."
        self._db_run("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, oid))
        return {"type": "success", "order_id": oid, "product_name": existing[1], "old_status": existing[2], "new_status": new_status}

    def _do_delete(self, entities, session_id):
        oid = entities.get("order_id")
        pname = entities.get("product_name")
        status = entities.get("status")

        if oid:
            rows = self._db_fetch_all("SELECT order_id, product_name, status FROM orders WHERE order_id = ?", (oid,))
        elif pname:
            # Look up order by product name
            matches = self._find_orders_by_product_name(pname)
            if not matches:
                return f"No orders found for '{pname}'."
            if len(matches) > 1:
                items = [f"• {r[1]} (ID: **{r[0]}**) — ₹{r[2]} — {r[5]}" for r in matches]
                return f"I found {len(matches)} orders for '{pname}':\n" + "\n".join(items) + "\n\nWhich one should I delete? Please specify the order ID."
            rows = [(matches[0][0], matches[0][1], matches[0][5])]
        elif status:
            rows = self._db_fetch_all("SELECT order_id, product_name, status FROM orders WHERE status = ?", (status,))
        else:
            return "Which order would you like to delete? Please specify an order ID (e.g., ORD123) or product name."

        if not rows:
            return "No matching orders found."
        if len(rows) > 1:
            items = [f"• {r[1]} ({r[0]}) — {r[2]}" for r in rows]
            return f"I found {len(rows)} matching orders:\n" + "\n".join(items) + "\n\nWhich one should I delete? Please specify the order ID."

        oid, pname, st = rows[0]
        self._pending[session_id] = {"sql": "DELETE FROM orders WHERE order_id = ?", "params": (oid,), "desc": f"{pname} ({oid})"}
        return f"⚠️ Are you sure you want to delete **{pname}** ({oid}, status: {st})?\n\nReply **yes** to confirm or **no** to cancel."

    def _handle_confirmation(self, user_query, session_id):
        pending = self._pending.pop(session_id, None)
        if not pending:
            return None
        lower = user_query.lower().strip()
        action = pending.get("action", "DELETE")  # legacy entries default to DELETE

        if lower in ('yes', 'y', 'confirm', 'sure', 'ok', 'yeah', 'yep', 'do it', 'buy it', 'place order', 'place it', 'order it'):
            try:
                if action == "BUY":
                    # Now actually create the order
                    order_id = f"ORD{random.randint(100, 999)}"
                    today = date.today().strftime("%Y-%m-%d")
                    self._db_run(
                        "INSERT INTO orders (order_id, session_id, product_id, product_name, price, quantity, order_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (order_id, session_id, pending["product_id"], pending["product_name"], pending["price"], 1, today, "Pending")
                    )
                    desc = f"{pending['product_name']} ({order_id})"
                    enhanced = self._ask_gemini(
                        f"The user confirmed buying: {pending['product_name']} for ₹{pending['price']}. Order ID: {order_id}. "
                        f"Write a brief, friendly order confirmation (2-3 sentences). Mention the order ID, product name, price, and that the status is Pending.",
                        fallback=f"🎉 Order placed! Your order **{order_id}** for **{pending['product_name']}** (₹{pending['price']}) is now **Pending**. You'll be notified when it ships!")
                    self._save(session_id, user_query, enhanced, op_type="BUY", affected=desc)
                    return enhanced
                else:
                    # DELETE confirmation (existing logic)
                    self._db_run(pending["sql"], pending.get("params", ()))
                    desc = pending["desc"]
                    enhanced = self._ask_gemini(
                        f"The user confirmed deleting order: {desc}. Write a brief, friendly confirmation (1-2 sentences). Mention item was removed.",
                        fallback=f"✅ Successfully deleted {desc}.")
                    self._save(session_id, user_query, enhanced, op_type="DELETE", affected=desc)
                    return enhanced
            except Exception as e:
                return f"❌ Error: {e}"
        elif lower in ('no', 'n', 'cancel', 'stop', 'nope', 'nevermind', 'no thanks', 'change'):
            if action == "BUY":
                resp = "No problem! The order was **not** placed. Would you like to look at other products or modify your choice?"
            else:
                resp = "No worries! Operation cancelled. Anything else I can help with?"
            self._save(session_id, user_query, resp)
            return resp
        else:
            self._pending[session_id] = pending
            if action == "BUY":
                return f"Please reply **yes** to confirm the purchase of **{pending['product_name']}** (₹{pending['price']}), or **no** to cancel."
            else:
                return f"Please reply **yes** to confirm or **no** to cancel the deletion of {pending['desc']}."

    # ════════════════════════════════════════════════════════════════════════
    # GEMINI RESPONSE FORMATTING (RAG-enhanced)
    # ════════════════════════════════════════════════════════════════════════

    def _format_response(self, user_query, data, intent, rag_ctx="", conv_ctx=""):
        if intent == "SHOW_ORDERS" and isinstance(data, list):
            if not data:
                data_desc = "No orders found."
            else:
                lines = [f"- {r[1]} (ID: {r[0]}) | ₹{r[2]} x{r[3]} | {r[4]} | {r[5]}" for r in data]
                data_desc = f"{len(data)} order(s):\n" + "\n".join(lines)
        elif intent == "ORDER_DETAIL" and isinstance(data, tuple):
            data_desc = f"Order {data[0]}: {data[1]}, ₹{data[2]} x{data[3]}, Date: {data[4]}, Status: {data[5]}"
            if len(data) > 6 and data[6]:
                data_desc += f", Description: {data[6]}"
            if len(data) > 7 and data[7]:
                data_desc += f", Category: {data[7]}"
        elif intent == "SHOW_PRODUCTS" and isinstance(data, list):
            if not data:
                data_desc = "No products found."
            else:
                lines = [f"- {r[1]} (ID: {r[0]}) | ₹{r[3]} | {r[4]} | {r[2]}" for r in data]
                data_desc = f"{len(data)} product(s):\n" + "\n".join(lines)
        elif intent in ("BUY_PRODUCT", "CREATE_ORDER") and isinstance(data, dict):
            if data.get("type") == "success":
                data_desc = f"Order created! ID: {data['order_id']}, Product: {data['product_name']}, Price: ₹{data['price']}"
            elif data.get("type") == "suggestions":
                lines = [f"- {p[1]} (ID: {p[0]}) | ₹{p[3]} | {p[4]}" for p in data["products"]]
                data_desc = f"No exact match for '{data['search']}'. Similar products:\n" + "\n".join(lines)
            else:
                data_desc = f"Product '{data.get('search', 'unknown')}' not found."
        elif intent == "UPDATE_ORDER" and isinstance(data, dict) and data.get("type") == "success":
            data_desc = f"Order {data['order_id']} ({data['product_name']}) updated: {data['old_status']} → {data['new_status']}"
        else:
            data_desc = str(data) if data else "No data"

        prompt = f"""You are a friendly e-commerce chatbot. Generate a natural, helpful response.

User asked: "{user_query}"
Intent: {intent}
Data: {data_desc}

{f"Knowledge base context:{chr(10)}{rag_ctx}" if rag_ctx else ""}{conv_ctx}

Rules:
- Be warm, concise (2-4 sentences for simple replies, more for lists)
- For lists, use clean formatting with emojis (📦 for orders, 🛍️ for products)
- Include product IDs so users can buy by ID
- Use ₹ for prices
- NEVER mention SQL, databases, or technical details
- For greetings, be warm and mention you help with orders & products
- For order creation, congratulate and mention the order ID
- Respond naturally, don't say "Based on records" """

        return self._ask_gemini(prompt, fallback=data_desc)

    # ════════════════════════════════════════════════════════════════════════
    # CONVERSATIONAL HANDLERS (Greeting, General, Casual)
    # ════════════════════════════════════════════════════════════════════════

    def _handle_greeting(self, user_query, rag_ctx="", conv_ctx=""):
        """Handle greetings with warm, contextual responses."""
        q = user_query.lower()

        # Build time-aware fallback
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        fallback_greetings = [
            f"{time_greeting}! 👋 I'm your e-commerce assistant. I can help you browse products, manage orders, track deliveries, and more. What can I do for you?",
            f"Hi there! 👋 Welcome! I can help you with:\n• 🛍️ Browse & buy products\n• 📦 View & manage orders\n• ✏️ Update order status\n• ❓ Answer your questions\n\nWhat would you like to do?",
            f"Hey! 😊 I'm here to help with your shopping needs. You can ask me to show products, place orders, check order status, or ask any questions!",
        ]

        # Pick a contextual fallback
        if 'morning' in q:
            fallback = "Good morning! ☀️ Ready to help you with your orders and products today. What can I do for you?"
        elif 'afternoon' in q:
            fallback = "Good afternoon! 🌤️ How can I assist you today? I can help with orders, products, or any questions."
        elif 'evening' in q or 'night' in q:
            fallback = "Good evening! 🌙 What can I help you with? Browse products, check orders, or ask me anything!"
        else:
            fallback = random.choice(fallback_greetings)

        # Try Gemini for a more natural response
        prompt = f"""You are a friendly e-commerce chatbot assistant. The user is greeting you.

User said: "{user_query}"
{conv_ctx}

Respond warmly (2-3 sentences). Mention that you can help with:
- Browsing and buying products
- Managing orders (create, update, delete, track)
- Answering questions about policies, shipping, etc.
Use a relevant emoji or two. Be warm and inviting."""

        return self._ask_gemini(prompt, fallback)

    def _handle_general(self, user_query, rag_ctx="", conv_ctx=""):
        """Handle general conversation: date/time, platform info, thanks, casual chat."""
        q = user_query.lower().strip()

        # ── Date/Time questions ──
        if any(w in q for w in ['date', 'day today', 'today', 'what time', 'current time', 'what day']):
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            fallback = f"📅 Today is **{date_str}** and the time is **{time_str}**. Is there anything else I can help you with?"

            prompt = f"""User asked: "{user_query}"
Current date: {date_str}, Time: {time_str}
Give a friendly reply mentioning the date/time, then offer to help with orders or products. Keep it to 2 sentences."""
            return self._ask_gemini(prompt, fallback)

        # ── Platform/About questions ──
        if any(w in q for w in ['what is this', 'about this', 'what can you do', 'who are you',
                                 'what are you', 'your purpose', 'platform', 'this app', 'capabilities']):
            fallback = ("🤖 I'm an AI-powered e-commerce assistant! Here's what I can do:\n\n"
                        "• 🛍️ **Browse Products** — Search by category or name\n"
                        "• 🛒 **Buy Products** — Place orders instantly\n"
                        "• 📦 **Manage Orders** — View, update status, or delete orders\n"
                        "• 📊 **Track Orders** — Check order status and details\n"
                        "• ❓ **Answer Questions** — Shipping, returns, policies & more\n\n"
                        "Just type your question or request naturally!")

            prompt = f"""User asked: "{user_query}"
You are an AI e-commerce chatbot built with RAG (Retrieval Augmented Generation) + Gemini LLM.
You help users browse products, place orders, manage orders, and answer questions.
Explain what you can do in a friendly way. Use emojis and bullet points. Keep it concise (4-5 lines)."""
            return self._ask_gemini(prompt, fallback)

        # ── Thank you ──
        if any(w in q for w in ['thank', 'thanks', 'thx', 'appreciate']):
            fallback = "You're welcome! 😊 Happy to help. Let me know if there's anything else you need!"
            prompt = f'User said: "{user_query}"\nRespond warmly to their thanks. Offer continued help. Keep it to 1-2 sentences.'
            return self._ask_gemini(prompt, fallback)

        # ── Goodbye ──
        if any(w in q for w in ['bye', 'goodbye', 'see you', 'good night', 'cya', 'ttyl']):
            fallback = "Goodbye! 👋 Have a great day! Come back anytime you need help with orders or products. 😊"
            prompt = f'User said: "{user_query}"\nSay a warm goodbye. Keep it brief (1-2 sentences).'
            return self._ask_gemini(prompt, fallback)

        # ── Help ──
        if any(w in q for w in ['help', 'how to use', 'guide', 'tutorial']):
            fallback = ("Here's how to use me! 💡\n\n"
                        "📝 **Try these commands:**\n"
                        "• \"Show my orders\" — View all your orders\n"
                        "• \"Show pending orders\" — Filter by status\n"
                        "• \"Buy gaming mouse\" — Purchase a product\n"
                        "• \"Show products\" — Browse the catalog\n"
                        "• \"Delete order ORD123\" — Remove an order\n"
                        "• \"Update ORD123 to shipped\" — Change order status\n\n"
                        "Or just ask me anything in natural language! 🗣️")
            return self._ask_gemini(
                f'User asked for help: "{user_query}"\nList the main things you can do with example commands. Use emojis. Be concise.',
                fallback)

        # ── Fallback: RAG + Gemini ──
        prompt = f"""You are a helpful e-commerce chatbot assistant.

User question: "{user_query}"
{f"Knowledge base info:{chr(10)}{rag_ctx}" if rag_ctx else ""}
{conv_ctx}

Give a helpful, friendly answer. Use knowledge base info if relevant.
If you don't know the answer, say so honestly and suggest what you CAN help with (orders, products, policies).
Be concise (2-3 sentences). Never mention databases or technical details."""

        fallback = rag_ctx if rag_ctx else "I'm not sure about that, but I can help you with:\n• 🛍️ Browsing and buying products\n• 📦 Managing your orders\n• ❓ Answering questions about shipping, returns, etc.\n\nWhat would you like to do?"
        return self._ask_gemini(prompt, fallback)

    # ════════════════════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ════════════════════════════════════════════════════════════════════════

    def get_response(self, user_query, session_id="default", role="user"):
        """
        Main pipeline:
        1. Check pending confirmations
        2. Retrieve RAG context (ChromaDB trained model)
        3. Classify intent (Gemini LLM)
        4. Execute action (with role-based permissions)
        5. Format response (Gemini + RAG)
        """
        # Step 0: Pending confirmation
        if session_id in self._pending:
            return self._handle_confirmation(user_query, session_id)

        # Step 1: Conversation context
        context = self._get_context(session_id)
        conv_ctx = self._format_context(context)

        # Step 2: RAG retrieval from trained model
        rag_ctx = self._get_rag_context(user_query)

        # Step 3: Intent classification via Gemini
        classification = self._classify_intent(user_query, conv_ctx)
        intent = classification.get("intent", "GENERAL_QUERY")
        entities = classification.get("entities", {})
        refers_to_previous = classification.get("refers_to_previous", False)

        # Clean null values from Gemini output
        for k, v in list(entities.items()):
            if v in ("null", "None", "", None):
                entities[k] = None

        # Step 3.5: Context resolution — resolve "that", "it", etc. from history
        if intent in ("DELETE_ORDER", "UPDATE_ORDER", "ORDER_DETAIL") and not entities.get("order_id") and not entities.get("product_name"):
            if refers_to_previous or any(w in user_query.lower() for w in ['that', 'it', 'this', 'same', 'that one', 'this one']):
                resolved = self._resolve_from_context(session_id)
                if resolved.get("order_id"):
                    entities["order_id"] = resolved["order_id"]
                    print(f"[Context Resolved] order_id={resolved['order_id']} from conversation history")
                elif resolved.get("product_name"):
                    entities["product_name"] = resolved["product_name"]
                    print(f"[Context Resolved] product_name={resolved['product_name']} from conversation history")

        print(f"[Pipeline] Intent: {intent} | Entities: {entities} | ContextRef: {refers_to_previous}")

        # Step 4 & 5: Execute + Format
        try:
            if intent == "GREETING":
                resp = self._handle_greeting(user_query, rag_ctx, conv_ctx)
                self._save(session_id, user_query, resp, op_type="GREETING")
                return resp

            elif intent == "SHOW_ORDERS":
                data = self._do_show_orders(entities)
                resp = self._format_response(user_query, data, intent, rag_ctx, conv_ctx)
                self._save(session_id, user_query, resp, op_type="READ")
                return resp

            elif intent == "ORDER_DETAIL":
                data = self._do_order_detail(entities)
                if not data:
                    resp = f"No order found with ID {entities.get('order_id', 'unknown')}."
                    self._save(session_id, user_query, resp, op_type="READ")
                elif isinstance(data, str):
                    # Duplicate disambiguation message
                    resp = data
                    self._save(session_id, user_query, resp, op_type="READ")
                else:
                    resp = self._format_response(user_query, data, intent, rag_ctx, conv_ctx)
                    affected = f"{data[1]} ({data[0]})" if data else None
                    self._save(session_id, user_query, resp, op_type="READ", affected=affected)
                return resp

            elif intent in ("BUY_PRODUCT", "CREATE_ORDER"):
                data = self._do_buy(entities, session_id)
                if isinstance(data, dict) and data.get("type") == "confirm_buy":
                    # Show product details and ask for confirmation
                    resp = self._ask_gemini(
                        f"""The user wants to buy a product. Show them the product details and ask for confirmation.

Product details:
- Name: {data['product_name']}
- Price: ₹{data['price']}
- Description: {data['description']}
- Category: {data['category']}

Show the details in a clean, attractive format with emojis. Then ask: "Would you like me to place this order? Reply **yes** to confirm or **no** to cancel."
Do NOT say the order has been placed. Do NOT mention order IDs. This is just a preview.""",
                        fallback=f"🛍️ Here's the product you want to buy:\n\n"
                                 f"**{data['product_name']}**\n"
                                 f"💰 Price: ₹{data['price']}\n"
                                 f"📝 {data['description']}\n"
                                 f"📂 Category: {data['category']}\n\n"
                                 f"Would you like me to place this order? Reply **yes** to confirm or **no** to cancel.")
                    self._save(session_id, user_query, resp, op_type="CONFIRM_REQUEST")
                    return resp
                else:
                    # suggestions or not_found
                    resp = self._format_response(user_query, data, intent, rag_ctx, conv_ctx)
                    self._save(session_id, user_query, resp)
                    return resp

            elif intent == "UPDATE_ORDER":
                # Only admins can update order status
                if role != "admin":
                    resp = "🔒 Sorry, only administrators can update order statuses (e.g., Pending → Shipped). If you need a status change, please contact an admin.\n\nI can still help you with viewing, creating, or deleting orders!"
                    self._save(session_id, user_query, resp, op_type="BLOCKED")
                    return resp
                data = self._do_update(entities)
                if isinstance(data, str):
                    self._save(session_id, user_query, data)
                    return data
                resp = self._format_response(user_query, data, intent, rag_ctx, conv_ctx)
                affected = f"{data['product_name']} ({data['order_id']})" if data.get("type") == "success" else None
                self._save(session_id, user_query, resp, op_type="UPDATE", affected=affected)
                return resp

            elif intent == "DELETE_ORDER":
                result = self._do_delete(entities, session_id)
                self._save(session_id, user_query, result, op_type="CONFIRM_REQUEST" if session_id in self._pending else None)
                return result

            elif intent == "SHOW_PRODUCTS":
                search = entities.get("search_term") or entities.get("product_name")
                products = []
                if search:
                    cats = self.get_all_categories()
                    for c in cats:
                        if search.lower() in c.lower() or c.lower() in search.lower():
                            products = self._get_products(category=c)
                            break
                    if not products:
                        products = self._get_products(search_term=search)
                if not products:
                    products = self._get_products()
                resp = self._format_response(user_query, products, intent, rag_ctx, conv_ctx)
                self._save(session_id, user_query, resp, op_type="PRODUCT_LIST")
                return resp

            elif intent == "MEMORY_QUERY":
                actions = []
                for u, b, op, aff in context:
                    if op and aff and op in ("DELETE", "BUY", "UPDATE", "CREATE"):
                        label = {"DELETE": "🗑️ Deleted", "BUY": "🛒 Purchased", "UPDATE": "✏️ Updated", "CREATE": "📦 Created"}.get(op, op)
                        actions.append(f"{label}: {aff}")
                raw = "\n".join(actions) if actions else "No recent actions found."
                resp = self._ask_gemini(
                    f'User asked: "{user_query}"\n\nRecent actions:\n{raw}\n\nSummarize in a friendly, conversational way. Be concise.',
                    fallback=raw)
                self._save(session_id, user_query, resp, op_type="MEMORY")
                return resp

            else:  # GENERAL_QUERY
                resp = self._handle_general(user_query, rag_ctx, conv_ctx)
                self._save(session_id, user_query, resp, op_type="GENERAL")
                return resp

        except Exception as e:
            print(f"[Error] {e}")
            error_resp = "Sorry, something went wrong. Please try again!"
            self._save(session_id, user_query, error_resp)
            return error_resp
