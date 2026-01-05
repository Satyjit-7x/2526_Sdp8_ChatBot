
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
import shutil

def vectorize_data():
    #file paths
    english_data_path = "data/english_support_dataset.csv"
    hindi_data_path = "data/hindi_support_dataset.csv"
    chroma_db_path = "data/chroma_db"

    #Load Data
    print("Loading data...")
    if os.path.exists(english_data_path):
        df_en = pd.read_csv(english_data_path)
        df_en = df_en.rename(columns={'user_query_en': 'query', 'bot_response_en': 'response'})
        df_en = df_en[['query', 'response']]
    else:
        df_en = pd.DataFrame(columns=['query', 'response'])

    if os.path.exists(hindi_data_path):
        df_hi = pd.read_csv(hindi_data_path)
        df_hi = df_hi.rename(columns={'user_query_hi': 'query', 'bot_response_hi': 'response'})
        df_hi = df_hi[['query', 'response']]
    else:
        df_hi = pd.DataFrame(columns=['query', 'response'])

    #Combine and Deduplicate
    print("Combining and deduplicating data...")
    combined_df = pd.concat([df_en, df_hi], ignore_index=True)
    
    # Remove duplicates based on query AND response tuple
    original_len = len(combined_df)
    combined_df.drop_duplicates(subset=['query', 'response'], inplace=True)
    combined_df.dropna(subset=['query', 'response'], inplace=True)
    
    unique_count = len(combined_df)
    print(f"Reduced data from {original_len} rows to {unique_count} unique Question-Answer pairs.")

    #Setup ChromaDB
    print(f"Setting up ChromaDB details at {chroma_db_path}...")
    
    # for fresh start we have to Clear existing DB
    # if os.path.exists(chroma_db_path):
    #     shutil.rmtree(chroma_db_path)

    client = chromadb.PersistentClient(path=chroma_db_path)
    
    #all-MiniLM-L6-v2 is a sentence embedding model converts text → numerical vectors
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Get or create collection
    # We delete it first if it exists to ensure we don't have stale data from previous runs if we re-run this script
    try:
        client.delete_collection("chatbot_qa")
        print("Deleted existing collection to start fresh.")
    except:
        pass

    collection = client.create_collection(name="chatbot_qa", embedding_function=sentence_transformer_ef)

    print("Adding documents to ChromaDB...")
    
    # Prepare data for Chroma
    documents = combined_df['query'].tolist()
    metadatas = [{'response': r} for r in combined_df['response'].tolist()]
    ids = [str(i) for i in range(unique_count)]

    # Add in batches
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Vectorization complete! Added {unique_count} documents to ChromaDB.")

if __name__ == "__main__":
    vectorize_data()
