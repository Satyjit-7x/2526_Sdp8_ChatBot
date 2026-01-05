
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

    def get_response(self, user_query, threshold=None): # threshold handled by n_results sort of, but Chroma returns distances
        if self.collection is None:
            return "Error: Data not loaded."

        # Query ChromaDB
        # We ask for n_results=1 to get the best match
        results = self.collection.query(
            query_texts=[user_query],
            n_results=1
        )
        
        # Results structure: {'ids': [['id']], 'distances': [[0.5]], 'metadatas': [[{'response': '...'}]]}
        if not results['metadatas'] or not results['metadatas'][0]:
             return "I'm sorry, I don't see a clear answer to that."
        
        # Check distance if we want strict thresholding. 
        # Chroma default is L2 distance (lower is better, 0 is exact match).
        # However, verifying 'threshold' with distances is tricky without normalization.
        # For now, we trust the best match from Chroma.
        
        best_response = results['metadatas'][0][0]['response']
        dist = results['distances'][0][0]
        
        # Optional: heuristic for "too far"
        # In L2, > 1.0 or 1.5 might be "far" 
        # "threshold" in previous cosine sim was > 0.4 (higher is better)
        # Let's return the match
        
        return best_response

