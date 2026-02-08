
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
            self.model = genai.GenerativeModel('gemini-pro')

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

    def get_sql_from_gemini(self, user_query):
        if not self.model:
            return None

        prompt = f"""
        You are an expert SQL generator for a SQLite database.
        The table schema is:
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            product TEXT NOT NULL,
            date TEXT,
            status TEXT
        );
        
        Generate a SQL query for the following user request: "{user_query}"
        
        Rules:
        1. Return ONLY the SQL query. No markdown, no explanation.
        2. If the user asks to create an order, generate an INSERT statement. Use 'ORD' + random 3 digits if no ID provided (or handle in logic, but valid SQL is needed). Assume today's date if not specified.
        3. If the user asks to update, generate an UPDATE statement.
        4. If the user asks to delete, generate a DELETE statement.
        5. If the user asks to read/show/list, generate a SELECT statement.
        6. If the request is NOT about orders or database, return "NO_SQL".
        """
        
        try:
            response = self.model.generate_content(prompt)
            sql = response.text.strip().replace('```sql', '').replace('```', '').strip()
            if "NO_SQL" in sql:
                return None
            return sql
        except Exception as e:
            print(f"Gemini Error: {e}")
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

    def get_response(self, user_query, threshold=None, context_data=None, pending_action=None):
        # 0. Handle Confirmation Flow
        if pending_action:
            if user_query.lower() in ['yes', 'confirm', 'sure', 'ok']:
                result = self.execute_sql(pending_action)
                if result['type'] == 'ACTION':
                    return "Operation completed successfully."
                elif result['type'] == 'ERROR':
                    return f"Database error: {result['message']}"
            elif user_query.lower() in ['no', 'cancel', 'stop']:
                return "Operation cancelled."
            else:
                return "Please answer 'yes' to confirm or 'no' to cancel."

        # 1. Strict Intent Check for SQL
        # Only invoke Gemini for SQL if the query looks like a database operation.
        # This prevents "Show me cancellation policy" from being interpreted as "SHOW TABLE cancellation" by a confused LLM
        # or prevents "Where is my order" (RAG) from being handled as SQL if it's better suited for RAG.
        
        sql_keywords = ["create", "add", "insert", "update", "change", "modify", "delete", "remove", "cancel order", "show all", "list all", "list my", "show my", "status of order"]
        is_potential_sql = any(k in user_query.lower() for k in sql_keywords)
        
        # Exception: "Where is my order" is usually RAG, but "Status of order ORD123" is SQL.
        # Let's rely on the LLM but give it better instructions and fallback.

        if self.model and is_potential_sql:
            generated_sql = self.get_sql_from_gemini(user_query)
            if generated_sql and generated_sql != "NO_SQL":
                print(f"Generated SQL: {generated_sql}")
                
                is_select = generated_sql.strip().upper().startswith("SELECT")
                
                if is_select:
                    result = self.execute_sql(generated_sql)
                    if result['type'] == 'SELECT':
                        data = result['data']
                        if not data:
                            return "No records found in the database."
                        # Format output
                        response = "Here are the results from your orders:\n"
                        for row in data:
                            response += str(row) + "\n"
                        return response
                    else:
                        return f"Error executing query: {result['message']}"
                else:
                    return json.dumps({
                        "requires_confirmation": True,
                        "sql": generated_sql,
                        "message": f"I am about to execute: `{generated_sql}`. Are you sure?"
                    })

        # 2. RAG + Gemini Hybrid Approach
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
                        # Use Gemini to answer using the context
                        rag_prompt = f"""
                        You are a helpful support chatbot for an e-commerce platform.
                        User Query: "{user_query}"
                        
                        Here is some relevant information from our knowledge base:
                        {context_text}
                        
                        Instructions:
                        1. Answer the user's question based on the knowledge base.
                        2. If the knowledge base doesn't have the answer, use your general knowledge to be helpful, but mention you are an AI assistant.
                        3. Be concise and professional.
                        4. Do NOT say "Based on the context provided". Just answer naturally.
                        """
                        try:
                            response = self.model.generate_content(rag_prompt)
                            return response.text.strip()
                        except Exception as e:
                            print(f"Gemini RAG Error: {e}")
                            return best_doc # Fallback to raw text
                    else:
                        return best_doc

            except Exception as e:
                print(f"ChromaDB Error: {e}")
            
        return "I'm not sure how to answer that. You can ask me to show orders, create an order, or ask about policies."

