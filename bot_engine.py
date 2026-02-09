
import chromadb
from chromadb.utils import embedding_functions
import os
import sqlite3
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

class ChatbotEngine:
    def __init__(self, chroma_db_path="data/chroma_db", db_path="orders.db"):
        self.chroma_db_path = chroma_db_path
        self.db_path = db_path
        self.collection = None
        self.ef = None
        self.model = None
        if GENAI_API_KEY:
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Updated from deprecated gemini-pro
        
        # Initialize conversation history table if not exists
        self._init_conversation_table()

    def load_model(self):
        print("Loading SentenceTransformer model (all-MiniLM-L6-v2) for ChromaDB...")
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def load_data(self):
        print(f"Connecting to ChromaDB at {self.chroma_db_path}...")
        client = chromadb.PersistentClient(path=self.chroma_db_path)
        try:
           self.collection = client.get_collection(name="chatbot_qa", embedding_function=self.ef)
           print(f"Connected to collection 'chatbot_qa'. contain {self.collection.count()} documents.")
        except Exception as e:
           print(f"Error connecting to collection: {e}")
           # raise # Don't raise, allowing bot to run with minimal features if DB missing
    
    def _init_conversation_table(self):
        """Initialize conversation history table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_timestamp 
                ON conversation_history(session_id, timestamp DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON conversation_history(session_id)
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize conversation table: {e}")
    
    def save_conversation(self, session_id, user_msg, bot_response, sql=None, op_type=None, affected_items=None):
        """Save conversation to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_history 
                (session_id, user_message, bot_response, sql_executed, operation_type, affected_items)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_msg, bot_response, sql, op_type, affected_items))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")
    
    def get_recent_context(self, session_id, limit=10):
        """Retrieve recent conversation history for context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_message, bot_response, operation_type, affected_items, timestamp
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, limit))
            rows = cursor.fetchall()
            conn.close()
            # Reverse to get chronological order
            return list(reversed(rows))
        except Exception as e:
            print(f"Warning: Could not retrieve context: {e}")
            return []
    
    def format_context_for_llm(self, context_list):
        """Format conversation context for LLM prompts"""
        if not context_list:
            return ""
        
        formatted = "\n\nRecent conversation history:\n"
        for user_msg, bot_resp, op_type, affected, timestamp in context_list:
            formatted += f"User: {user_msg}\n"
            if op_type and affected:
                formatted += f"Bot: {bot_resp} [Action: {op_type}, Items: {affected}]\n"
            else:
                formatted += f"Bot: {bot_resp}\n"
        return formatted

    def generate_sql(self, user_query):
        """Generate SQL from natural language - Enhanced pattern matching"""
        query_lower = user_query.lower().strip()
        
        # Pattern 0: Bare order ID (e.g., "ORD999", "ord123")
        order_match = re.search(r'^ord\d+$', query_lower.strip())
        if order_match:
            order_id = order_match.group(0).upper()
            return f"SELECT * FROM orders WHERE order_id = '{order_id}'"
        
        # Pattern 1: DELETE operations - Enhanced with qualifiers
        if any(word in query_lower for word in ['delete', 'remove', 'cancel order']):
            import sqlite3
            
            # Check if user specified order ID directly
            order_match = re.search(r'ord\d+', query_lower)
            if order_match:
                order_id = order_match.group(0).upper()
                return f"DELETE FROM orders WHERE order_id = '{order_id}'"
            
            # Extract product name
            product = None
            for word in ['delete', 'remove', 'cancel']:
                if word in query_lower:
                    parts = query_lower.split(word)
                    if len(parts) > 1:
                        # Get everything after the command word
                        rest = parts[1].strip()
                        
                        # Remove common phrase qualifiers
                        for qualifier in ['which is', 'that is', 'with status', 'with the status']:
                            if qualifier in rest:
                                rest = rest.split(qualifier)[0].strip()
                        
                        # Remove qualifier keywords (latest, oldest, pending, etc.)
                        qualifier_keywords = ['latest', 'newest', 'recent', 'oldest', 'first', 
                                            'pending', 'delivered', 'shipped', 'returned']
                        words = rest.split()
                        # Filter out qualifier keywords
                        product_words = [w for w in words if w.lower() not in qualifier_keywords]
                        
                        # Filter out generic words
                        generic_words = ['product', 'order', 'item', 'thing', 'entry', 'record']
                        product_words = [w for w in product_words if w.lower() not in generic_words]
                        
                        if product_words:
                            # Take first 2 words as product name
                            product = ' '.join(product_words[:2]) if len(product_words) >= 2 else product_words[0]
                            break
            
            # Handle status-only queries (e.g., "delete pending", "delete returned")
            if not product or len(product) < 3:
                # Check if there's a status qualifier
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                status_query = None
                if 'pending' in query_lower:
                    status_query = 'Pending'
                elif 'delivered' in query_lower:
                    status_query = 'Delivered'
                elif 'shipped' in query_lower:
                    status_query = 'Shipped'
                elif 'returned' in query_lower or 'return' in query_lower:
                    status_query = 'Returned'
                
                if status_query:
                    cursor.execute("SELECT order_id, product, date, status FROM orders WHERE status = ?", (status_query,))
                    matches = cursor.fetchall()
                    conn.close()
                    
                    if not matches:
                        return None  # No matches
                    
                    if len(matches) == 1:
                        # Only one pending/delivered/etc order
                        return f"DELETE FROM orders WHERE order_id = '{matches[0][0]}'"
                    
                    # Multiple matches - ask for clarification
                    options = [f"{m[1]} ({m[0]})" for m in matches]
                    clarify_msg = f"I found {len(matches)} {status_query.lower()} orders: {', '.join(options)}. Which one would you like to delete? Please specify the product name or order ID."
                    return f"CLARIFY:{clarify_msg}"
                else:
                    conn.close()
                    return None
            
            # Check for qualifiers and duplicates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find all matches for this product
            cursor.execute("SELECT order_id, product, date, status FROM orders WHERE LOWER(product) LIKE ?", 
                          (f'%{product.lower()}%',))
            matches = cursor.fetchall()
            conn.close()
            
            if not matches:
                return None  # No matches, will fall through to RAG
            
            if len(matches) == 1:
                # Only one match, safe to delete
                return f"DELETE FROM orders WHERE order_id = '{matches[0][0]}'"
            
            # Multiple matches - check for qualifiers
            # Qualifier 1: Status (returned, pending, delivered, shipped)
            if 'returned' in query_lower or 'return' in query_lower:
                for match in matches:
                    if match[3].lower() == 'returned':
                        return f"DELETE FROM orders WHERE order_id = '{match[0]}'"
            elif 'pending' in query_lower:
                for match in matches:
                    if match[3].lower() == 'pending':
                        return f"DELETE FROM orders WHERE order_id = '{match[0]}'"
            elif 'delivered' in query_lower:
                for match in matches:
                    if match[3].lower() == 'delivered':
                        return f"DELETE FROM orders WHERE order_id = '{match[0]}'"
            elif 'shipped' in query_lower:
                for match in matches:
                    if match[3].lower() == 'shipped':
                        return f"DELETE FROM orders WHERE order_id = '{match[0]}'"
            
            # Qualifier 2: Date (latest, newest, oldest, first ordered)
            elif 'latest' in query_lower or 'newest' in query_lower or 'recent' in query_lower:
                # Sort by date descending, take first
                sorted_matches = sorted(matches, key=lambda x: x[2], reverse=True)
                return f"DELETE FROM orders WHERE order_id = '{sorted_matches[0][0]}'"
            elif 'oldest' in query_lower or 'first' in query_lower:
                # Sort by date ascending, take first
                sorted_matches = sorted(matches, key=lambda x: x[2])
                return f"DELETE FROM orders WHERE order_id = '{sorted_matches[0][0]}'"
            
            # No qualifier found, but multiple matches - need clarification
            # Return None so it falls through, but we should improve this later
            return None
        
        # Pattern 2: CREATE/INSERT operations
        elif any(word in query_lower for word in ['create', 'add', 'insert', 'new order']):
            # Extract product name
            from datetime import date
            
            # Try to find product after keywords
            for word in ['for', 'add', 'create', 'order']:
                if word in query_lower:
                    parts = query_lower.split(word)
                    if len(parts) > 1:
                        product = parts[-1].strip().split(',')[0].strip()
                        # Remove common words
                        product = product.replace('a ', '').replace('an ', '').replace('order', '').strip()
                        if product and len(product) > 2:
                            # Generate random order ID
                            import random
                            order_id = f"ORD{random.randint(100, 999):03d}"
                            today = date.today().strftime('%Y-%m-%d')
                            product_cap = product.title()
                            return f"INSERT INTO orders (order_id, product, date, status) VALUES ('{order_id}', '{product_cap}', '{today}', 'Pending')"
            return None
        
        # Pattern 3: UPDATE operations
        elif any(word in query_lower for word in ['update', 'change', 'modify', 'set']):
            # Extract order ID and new status
            order_match = re.search(r'ord\d+', query_lower)
            if order_match:
                order_id = order_match.group(0).upper()
                # Try to find status
                if 'delivered' in query_lower:
                    return f"UPDATE orders SET status = 'Delivered' WHERE order_id = '{order_id}'"
                elif 'shipped' in query_lower:
                    return f"UPDATE orders SET status = 'Shipped' WHERE order_id = '{order_id}'"
                elif 'cancelled' in query_lower or 'canceled' in query_lower:
                    return f"UPDATE orders SET status = 'Cancelled' WHERE order_id = '{order_id}'"
            return None
        
        
        # Pattern 4: SELECT/READ operations - Enhanced for natural language
        elif any(word in query_lower for word in ['show', 'list', 'get', 'my orders', 'all orders', 'view', 'which', 'what', 'any', 'how many', 'display']):
            # Check if asking for specific order
            order_match = re.search(r'ord\d+', query_lower)
            if order_match:
                order_id = order_match.group(0).upper()
                return f"SELECT * FROM orders WHERE order_id = '{order_id}'"
            
            # Check if asking for specific status (works for "which products are pending", "show pending", etc.)
            if 'pending' in query_lower:
                return "SELECT * FROM orders WHERE status = 'Pending'"
            elif 'delivered' in query_lower:
                return "SELECT * FROM orders WHERE status = 'Delivered'"
            elif 'shipped' in query_lower or 'shipping' in query_lower:
                return "SELECT * FROM orders WHERE status = 'Shipped'"
            elif 'returned' in query_lower or 'return' in query_lower:
                return "SELECT * FROM orders WHERE status = 'Returned'"
            
            # Default: show all orders when asking about "orders" or "products" in general
            elif any(word in query_lower for word in ['orders', 'products', 'items']):
                return "SELECT * FROM orders"
            else:
                # Fallback for vague queries
                return "SELECT * FROM orders"
        
        # Not a SQL query
        return None

    def execute_sql(self, sql):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            if sql.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                conn.close()
                return {"type": "SELECT", "data": results, "columns": columns}
            else:
                conn.commit()
                conn.close()
                return {"type": "ACTION", "status": "success"}
        except Exception as e:
            return {"type": "ERROR", "message": str(e)}

    def get_response(self, user_query, threshold=None, context_data=None, pending_action=None, pending_items=None, session_id="default"):
        # 0. Get conversation context
        context = self.get_recent_context(session_id, limit=10)
        context_str = self.format_context_for_llm(context)
        
        # 1. Check if user is asking about recent actions (memory query)
        # IMPORTANT: Don't include action words like "delete", "remove" here - those are SQL operations!
        # Only include phrases that explicitly ask about PAST actions
        memory_keywords = ["what did", "what product", "what item", "you removed", "you deleted", "you created", "you added", "you updated", "which product deleted", "which product removed", "which product ordered", "which product created", "ordered recently", "created recently", "added recently"]
        is_memory_query = any(k in user_query.lower() for k in memory_keywords)
        
        if is_memory_query and context:
            # Determine which operation types to show based on query
            query_lower = user_query.lower()
            show_ops = []
            
            if any(word in query_lower for word in ["deleted", "removed", "you deleted", "you removed", "which product deleted"]):
                show_ops = ["DELETE"]
            elif any(word in query_lower for word in ["created", "added", "ordered", "you created", "you added", "which product ordered", "which product created", "ordered recently", "created recently"]):
                show_ops = ["CREATE"]
            elif any(word in query_lower for word in ["updated", "changed", "you updated", "you changed"]):
                show_ops = ["UPDATE"]
            else:
                # Generic query - show all operations
                show_ops = ["DELETE", "CREATE", "UPDATE"]
            
            # Get recent actions of the specified types
            response_parts = []
            for user_msg, bot_resp, op_type, affected, timestamp in reversed(context[-5:]):  # Last 5 actions
                if affected and op_type in show_ops:
                    try:
                        import json
                        items = json.loads(affected) if affected.startswith('[') else [affected]
                        if op_type == "DELETE":
                            response_parts.append(f"Deleted: {', '.join(items)}")
                        elif op_type == "CREATE":
                            response_parts.append(f"Created: {', '.join(items)}")
                        elif op_type == "UPDATE":
                            response_parts.append(f"Updated: {', '.join(items)}")
                    except:
                        if op_type == "DELETE":
                            response_parts.append(f"Deleted: {affected}")
                        elif op_type == "CREATE":
                            response_parts.append(f"Created: {affected}")
                        elif op_type == "UPDATE":
                            response_parts.append(f"Updated: {affected}")
            
            if response_parts:
                answer = "Recent actions:\n" + "\n".join(response_parts)
                self.save_conversation(session_id, user_query, answer, op_type="MEMORY_QUERY")
                return answer
            else:
                # Be specific about what wasn't found
                op_name = "create/update/delete" if len(show_ops) == 3 else show_ops[0].lower()
                answer = f"I don't see any recent {op_name} actions in your history."
                self.save_conversation(session_id, user_query, answer, op_type="MEMORY_QUERY")
                return answer
        
        # 2. Handle Confirmation Flow
        if pending_action:
            if user_query.lower() in ['yes', 'confirm', 'sure', 'ok']:
                result = self.execute_sql(pending_action)
                if result['type'] == 'ACTION':
                    response = "Operation completed successfully."
                    # Extract operation details for memory
                    op_type = "DELETE" if "DELETE" in pending_action.upper() else "UPDATE" if "UPDATE" in pending_action.upper() else "CREATE" if "INSERT" in pending_action.upper() else "ACTION"
                    # Save with affected items from pending_items
                    self.save_conversation(session_id, user_query, response, sql=pending_action, op_type=op_type, affected_items=pending_items)
                    return response
                elif result['type'] == 'ERROR':
                    response = f"Database error: {result['message']}"
                    self.save_conversation(session_id, user_query, response)
                    return response
            elif user_query.lower() in ['no', 'cancel', 'stop']:
                response = "Operation cancelled."
                self.save_conversation(session_id, user_query, response)
                return response
            else:
                return "Please answer 'yes' to confirm or 'no' to cancel."


        # 2.5. Check if this is a follow-up to a clarification request
        # If last bot message was asking "which one?", treat simple responses as delete commands
        if context:
            last_user_msg, last_bot_resp, last_op_type, last_affected, last_timestamp = context[-1]
            if last_op_type == "CLARIFY_REQUEST":
                # User is responding to clarification - check if it's a simple product/order reference
                query_lower = user_query.lower().strip()
                order_match = re.search(r'ord\d+', query_lower)
                # If it's an order ID or a short product name (1-3 words), treat as delete
                if order_match or len(query_lower.split()) <= 3:
                    user_query = f"delete {user_query}"
                    print(f"[Context] Detected clarification follow-up, treating as: '{user_query}'")

        # 3. Try SQL generation if query looks like database operation
        # Expanded keywords to catch natural language queries about orders
        sql_keywords = [
            # Actions
            "create", "add", "insert", "update", "change", "modify", "delete", "remove", "cancel order",
            # Queries  
            "show all", "list all", "list my", "show my", "view", "display",
            # Question words about orders
            "which", "what", "how many", "any",
            # Status words
            "pending", "delivered", "shipped", "returned",
            # Product/order references
            "products", "orders", "order", "product", "items"
        ]
        # Also check if query contains an order ID pattern
        has_order_id = bool(re.search(r'ord\d+', user_query.lower()))
        
        is_potential_sql = any(k in user_query.lower() for k in sql_keywords) or has_order_id
        
        if is_potential_sql:
            generated_sql = self.generate_sql(user_query)
            if generated_sql:
                print(f"Generated SQL: {generated_sql}")
                
                # Check if it's a clarification request
                if generated_sql.startswith("CLARIFY:"):
                    clarify_msg = generated_sql.replace("CLARIFY:", "").strip()
                    self.save_conversation(session_id, user_query, clarify_msg, op_type="CLARIFY_REQUEST")
                    return clarify_msg
                
                is_select = generated_sql.strip().upper().startswith("SELECT")
                
                if is_select:
                    result = self.execute_sql(generated_sql)
                    if result['type'] == 'SELECT':
                        data = result['data']
                        if not data:
                            response = "No records found in the database."
                            self.save_conversation(session_id, user_query, response, sql=generated_sql, op_type="READ")
                            return response
                        
                        # Format response in human-readable way
                        count = len(data)
                        affected_items = []
                        
                        # Build nice response based on query type
                        if 'pending' in user_query.lower():
                            status_msg = "pending"
                        elif 'delivered' in user_query.lower():
                            status_msg = "delivered"
                        elif 'shipped' in user_query.lower():
                            status_msg = "shipped"
                        elif 'returned' in user_query.lower():
                            status_msg = "returned"
                        else:
                            status_msg = "total"
                        
                        if count == 1:
                            product_name = data[0][1]  # product column
                            order_id = data[0][0]      # order_id column
                            status = data[0][3]        # status column
                            response = f"You have 1 {status_msg} order: {product_name} ({order_id}) - Status: {status}"
                            affected_items.append(order_id)
                        else:
                            response = f"You have {count} {status_msg} order{'s' if count > 1 else ''}:\n"
                            for row in data:
                                order_id, product, date, status = row
                                response += f"• {product} ({order_id}) - {status} - {date}\n"
                                affected_items.append(order_id)
                        
                        # Save with affected items
                        import json
                        self.save_conversation(session_id, user_query, response, sql=generated_sql, op_type="READ", affected_items=json.dumps(affected_items))
                        return response
                    elif result['type'] == 'ERROR':
                        response = f"Database error: {result['message']}"
                        self.save_conversation(session_id, user_query, response)
                        return response
                else:
                    # For DELETE/UPDATE/INSERT, we need confirmation
                    # FIRST: Get affected items BEFORE deletion!
                    affected_items = []
                    op_type = "DELETE" if "DELETE" in generated_sql.upper() else "UPDATE" if "UPDATE" in generated_sql.upper() else "CREATE"
                    
                    if "DELETE" in generated_sql.upper():
                        # Extract what will be deleted
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        # Try to find the WHERE clause and query what will be deleted
                        where_match = re.search(r'WHERE\s+(.+)', generated_sql, re.IGNORECASE)
                        if where_match:
                            where_clause = where_match.group(1)
                            check_sql = f"SELECT product, order_id FROM orders WHERE {where_clause}"
                            try:
                                cursor.execute(check_sql)
                                items = cursor.fetchall()
                                for product, order_id in items:
                                    affected_items.append(f"{product} ({order_id})")
                            except Exception as e:
                                print(f"Error fetching items to delete: {e}")
                        conn.close()
                    
                    # Build confirmation message with details
                    import json
                    confirmation_msg = f"I am about to execute: `{generated_sql}`. "
                    if affected_items:
                        confirmation_msg += f"This will affect: {', '.join(affected_items)}. "
                    confirmation_msg += "Are you sure?"
                    
                    # Return JSON with SQL and affected items
                    return json.dumps({
                        "requires_confirmation": True,
                        "message": confirmation_msg,
                        "sql": generated_sql,
                        "affected_items": json.dumps(affected_items) if affected_items else None
                    })

        # 4. RAG + Gemini Hybrid Approach (fallback for non-SQL queries)
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[user_query],
                    n_results=2 # Get top 2 for better context
                )
                
                # Check if we got results
                if results['metadatas'] and results['metadatas'][0]:
                    best_doc = results['metadatas'][0][0]['response']
                    dist = results['distances'][0][0]
                    
                    # If match is very close (low distance), return it directly (fast path)
                    # Distance in Chroma (L2) varies, but usually < 1.0 is relevant.
                    # Only return raw text if we are VERY confident.
                    # Otherwise, use Gemini to synthesize.
                    
                    context_text = "\n\n".join([m['response'] for m in results['metadatas'][0]])
                    
                    if self.model:
                        # Use Gemini to answer using the context, with conversation history
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
                        try:
                            response = self.model.generate_content(rag_prompt)
                            answer = response.text.strip()
                            self.save_conversation(session_id, user_query, answer, op_type="RAG_QUERY")
                            return answer
                        except Exception as e:
                            print(f"Gemini RAG Error: {e}")
                            self.save_conversation(session_id, user_query, best_doc, op_type="RAG_QUERY")
                            return best_doc # Fallback to raw text
                    else:
                        self.save_conversation(session_id, user_query, best_doc, op_type="RAG_QUERY")
                        return best_doc

            except Exception as e:
                print(f"ChromaDB Error: {e}")
        
        fallback = "I'm not sure how to answer that. You can ask me to show orders, create an order, or ask about policies."
        self.save_conversation(session_id, user_query, fallback, op_type="FALLBACK")
        return fallback

