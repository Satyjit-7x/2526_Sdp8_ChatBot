
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
    print("WARNING: 'deep-translator' library not found. Translation features will be disabled.")
    print("Please install it using: pip install deep-translator")

class TranslationMixin:
    """Helper class for translation features"""
    def __init__(self):
        if GoogleTranslator:
            self.translator = GoogleTranslator(source='auto', target='en')
        else:
            self.translator = None
    
    def translate_to_english(self, text):
        if not self.translator:
            return text
        try:
            # Detect and translate to English
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation Error: {e}")
            return text

    def translate_from_english(self, text, target_lang):
        if not self.translator:
            return text
        try:
            return GoogleTranslator(source='en', target=target_lang).translate(text)
        except Exception as e:
            print(f"Translation Error: {e}")
            return text

class ChatbotEngine(TranslationMixin):
    def __init__(self, data_path, query_col, response_col):
        TranslationMixin.__init__(self)  # Initialize translator
        self.data_path = data_path
        self.query_col = query_col
        self.response_col = response_col
        
        # Vectorize data and remove stop words
        self.vectorizer = TfidfVectorizer(stop_words='english') 
        
        self.tfidf_matrix = None
        self.df = None

    def load_data(self):
        print(f"Loading data from {self.data_path}...")
        self.df = pd.read_csv(self.data_path)
        
        # Remove empty rows to avoid errors
        self.df.dropna(subset=[self.query_col, self.response_col], inplace=True)
        print(f"Data loaded successfully. {len(self.df)} conversations found.")

    def train(self):
        """
        Train the Data (Vectorization)
        This function converts every question in our CSV into a list of numbers (Vectors).
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print("Training model...")
        # .fit_transform() does two things:
        # 1. Learns all the words in the column (Vocabulary)
        # 2. Converts the sentences into a Matrix of numbers
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df[self.query_col])
        print("Training complete. The bot has 'read' the textbook.")

    def get_response(self, user_query, threshold=0.3): # threshold 0.3 means 30% match of question we generate answer
        if self.tfidf_matrix is None:
            return "Error: Bot is not trained yet."

        # Convert question to numbers using the SAME translator
        user_tfidf = self.vectorizer.transform([user_query])

        # Compare numbers! (Cosine Similarity = Calculate angle between vectors) 1.0 = Exact match, 0.0 = Completely different
        similarities = cosine_similarity(user_tfidf, self.tfidf_matrix).flatten()
        
    
        # Find the best score
        best_match_index = np.argmax(similarities)
        best_score = similarities[best_match_index]

        # If best_score good then return answer we compare with threshold
        if best_score >= threshold:
            return self.df.iloc[best_match_index][self.response_col]
        else:
            return "I'm sorry, I don't understand that request. Could you rephrase?"

