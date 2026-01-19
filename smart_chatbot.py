
import json
import os
import urllib.error
import urllib.request
from typing import Optional

from bot_engine import ChatbotEngine


def _is_no_answer(text: str) -> bool:
    if not text:
        return True

    normalized = " ".join(text.strip().lower().split())
    no_answer_phrases = [
        "no response from ai",
        "i don't know",
        "i dont know",
        "i'm not sure",
        "im not sure",
        "i am not sure",
        "can't help",
        "cannot help",
        "unable to answer",
        "i cannot answer",
    ]

    return any(p in normalized for p in no_answer_phrases)


def _ask_backend(question: str) -> Optional[str]:
    ai_url = os.getenv("AI_SERVICE_URL", "http://localhost:8000/ai/chat").strip()
    if not ai_url:
        return None

    try:
        payload = json.dumps({"question": question}).encode("utf-8")
        req = urllib.request.Request(
            ai_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body) if body else {}

        candidate = data.get("reply") or data.get("answer")
        if isinstance(candidate, str) and candidate.strip() and not _is_no_answer(candidate):
            return candidate.strip()
        return None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None

def main():
    chroma_db_path = "data/chroma_db"
    
    #initialization of bot engine
    try:
        bot = ChatbotEngine(chroma_db_path=chroma_db_path)
        bot.load_model() 
        bot.load_data() 
    except Exception as e:
        print(f"Failed to start: {e}")
        return

    
    print("\n" + "="*50)
    print(" MULTILINGUAL ECOMMERCE SUPPORT BOT")
    print(" Ready to help in English, Hindi, and more!")
    print(" Try: 'Where is my order?' or 'मेरा ऑर्डर कहाँ है?'")
    print(" Type 'exit' to quit.")
    print("="*50 + "\n")

    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("Bot: Goodbye! Happy Shopping.")
                break
            
            if not user_input.strip():
                continue

            response = _ask_backend(user_input)
            if response is None:
                response = bot.get_response(user_input)
            print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
