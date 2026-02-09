import os
import uuid
from bot_engine_no_gemini import ChatbotEngine

def main():
    chroma_db_path = "data/chroma_db"
    
    session_id = str(uuid.uuid4())[:8]
    print(f"Session ID: {session_id}")
    print("🤖 CHATBOT (NO GEMINI) - Testing Mode")
    print("✅ Features: Database operations, RAG, Pattern matching")
    print("❌ Disabled: Gemini LLM enhancement")
    print("="*50)
    
    try:
        bot = ChatbotEngine(chroma_db_path=chroma_db_path)
        bot.load_model() 
        bot.load_data() 
        print("✅ Bot engine loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        return

    print("\nTry these commands:")
    print("- 'show my orders'")
    print("- 'create order for laptop'")
    print("- 'show pending orders'")
    print("- 'delete laptop order'")
    print("- 'where is my order?'")
    print("- Type 'exit' to quit")
    print("="*50 + "\n")

    pending_sql = None
    pending_items = None
    
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("Bot: Goodbye! 👋")
                break
            
            if not user_input.strip():
                continue

            response = bot.get_response(user_input, pending_action=pending_sql, pending_items=pending_items, session_id=session_id)
            
            # Check if response is JSON (confirmation needed)
            import json
            try:
                parsed = json.loads(response)
                if parsed.get("requires_confirmation"):
                    pending_sql = parsed.get("sql")
                    pending_items = parsed.get("affected_items")
                    print(f"Bot: {parsed.get('message')}\n")
                else:
                    print(f"Bot: {response}\n")
            except:
                # Clear pending if we got a regular response
                pending_sql = None
                pending_items = None
                print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\nBot: Goodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
