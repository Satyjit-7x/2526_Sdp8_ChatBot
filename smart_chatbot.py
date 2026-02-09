

import os
import uuid
from bot_engine import ChatbotEngine

def main():
    chroma_db_path = "data/chroma_db"
    
    # Generate a session ID for this console session
    session_id = str(uuid.uuid4())[:8]  # Short session ID for console
    print(f"Session ID: {session_id}")
    
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

    pending_sql = None
    pending_items = None
    
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("Bot: Goodbye! Happy Shopping.")
                break
            
            if not user_input.strip():
                continue

            # Get Response with session_id and pending context
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
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
