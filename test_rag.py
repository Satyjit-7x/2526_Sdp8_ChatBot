import requests
import json
import time

def test_rag():
    url = "http://localhost:5001/api/chat"
    
    questions = [
        "What is RAG?",
        "Tell me about LLMs",
        "What is the difference between rule based and AI chatbot?",
        "Show all orders", # Should still be SQL
        "Process cancellation" # Should be RAG/Falllback
    ]
    
    for q in questions:
        print(f"\nQuery: {q}")
        payload = {"message": q}
        try:
            response = requests.post(url, json=payload, timeout=15)
            print(f"Bot: {response.json()['reply']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    time.sleep(5)
    test_rag()
