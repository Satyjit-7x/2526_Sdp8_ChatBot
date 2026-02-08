import os
import chromadb
from chromadb.utils import embedding_functions

def ingest_learning_data():
    learning_file_path = "Learning"
    chroma_db_path = "data/chroma_db"
    
    if not os.path.exists(learning_file_path):
        print(f"Error: {learning_file_path} not found.")
        return

    print(f"Reading {learning_file_path}...")
    with open(learning_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split content into chunks based on "LAB" sections or generic paragraphs if LABs aren't enough
    # The file has "==================================== LAB - X ===================================="
    # We can split by that, and then maybe split by newlines if chunks are too big.
    # For now, let's split by double newlines to get paragraphs/sections.
    
    
    # Split content into chunks based on "LAB" sections
    sections = content.split("====================================")
    
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    for section in sections:
        clean_section = section.strip()
        if not clean_section:
            continue
            
        # Split by newlines to get smaller chunks
        lines = clean_section.split('\n')
        current_chunk = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_chunk:
                    text = "\n".join(current_chunk)
                    if len(text) > 30: # Ignore very short chunks
                        documents.append(text)
                        metadatas.append({"response": text})
                        ids.append(f"learning_{count}")
                        count += 1
                    current_chunk = []
            else:
                current_chunk.append(line)
        
        # Add remainder
        if current_chunk:
             text = "\n".join(current_chunk)
             if len(text) > 30:
                documents.append(text)
                metadatas.append({"response": text})
                ids.append(f"learning_{count}")
                count += 1

    print(f"Found {len(documents)} chunks to ingest.")
    
    print(f"Connecting to ChromaDB at {chroma_db_path}...")
    client = chromadb.PersistentClient(path=chroma_db_path)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Get collection
    try:
        collection = client.get_or_create_collection(name="chatbot_qa", embedding_function=ef)
    except Exception as e:
        print(f"Error getting collection: {e}")
        return

    print("Adding documents...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_learning_data()
