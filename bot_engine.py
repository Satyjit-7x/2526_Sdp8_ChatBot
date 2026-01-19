
import chromadb
from chromadb.utils import embedding_functions
import os

class ChatbotEngine:
    def __init__(self, chroma_db_path="data/chroma_db"):
        self.chroma_db_path = chroma_db_path
        self.collection = None
        self.ef = None

    def load_model(self):
        print("Loading SentenceTransformer model (all-MiniLM-L6-v2) for ChromaDB...")
        # initialization for embedding function
        #Directory Based
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def load_data(self):
        print(f"Connecting to ChromaDB at {self.chroma_db_path}...")
        
        client = chromadb.PersistentClient(path=self.chroma_db_path)
        
        # check if collection exists
        try:
           self.collection = client.get_collection(name="chatbot_qa", embedding_function=self.ef)
           print(f"Connected to collection 'chatbot_qa'. contain {self.collection.count()} documents.")
        except Exception as e:
           print(f"Error connecting to collection: {e}")
           raise

    def get_response(self, user_query, threshold=None, context_data=None):
        if self.collection is None:
            return "Error: Data not loaded."

        # 1. Check Dynamic Context (RAG on Orders)
        if context_data and isinstance(context_data, list) and len(context_data) > 0:
            try:
                import numpy as np
                from numpy.linalg import norm

                # Format orders into searchable text
                order_texts = []
                for order in context_data:
                    # e.g. "Order ORD001: Mobile, Delivered on 2023-10-03"
                    text = f"Order {order.get('orderId')}: {order.get('product')}, Status: {order.get('status')}, Date: {order.get('date')}"
                    order_texts.append(text)
                
                # Generate embeddings
                # self.ef is a callable that takes a list of strings
                query_embedding = self.ef([user_query])[0]
                context_embeddings = self.ef(order_texts)

                # Calculate Cosine Similarities
                # Cosine Similarity = (A . B) / (||A|| * ||B||)
                scores = []
                for i, ctx_emb in enumerate(context_embeddings):
                    # Convert to numpy arrays if they aren't already
                    q_vec = np.array(query_embedding)
                    c_vec = np.array(ctx_emb)
                    
                    cosine_sim = np.dot(q_vec, c_vec) / (norm(q_vec) * norm(c_vec))
                    scores.append((cosine_sim, i))
                
                # Find best match
                scores.sort(key=lambda x: x[0], reverse=True)
                best_score, best_idx = scores[0]

                print(f"Best order match score: {best_score} for query '{user_query}'")

                # Threshold for dynamic context (0.3 is usually a safe baseline for 'relevant')
                if best_score > 0.3: 
                    best_order = context_data[best_idx]
                    return f"Based on your recent orders, here is the info for {best_order.get('product')} ({best_order.get('orderId')}): Status is {best_order.get('status')}, Last updated on {best_order.get('date')}."

            except Exception as e:
                print(f"Error processing context data: {e}")
                # Fallback to general DB if context check fails

        # 2. Query ChromaDB (General Knowledge)
        # We ask for n_results=1 to get the best match
        results = self.collection.query(
            query_texts=[user_query],
            n_results=1
        )
        
        # Results structure: {'ids': [['id']], 'distances': [[0.5]], 'metadatas': [[{'response': '...'}]]}
        if not results['metadatas'] or not results['metadatas'][0]:
            return "I'm not sure how to answer that. Can you tell me more?"
        
        best_response = results['metadatas'][0][0]['response']
        dist = results['distances'][0][0]
        
        # Debugging distance
        # print(f"ChromaDB distance: {dist}")

        return best_response

