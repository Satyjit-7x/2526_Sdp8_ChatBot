import os
import uuid
from bot_engine import ChatbotEngine
from response_formatter import ResponseFormatter

def main():
    chroma_db_path = "data/chroma_db"
    
    # Generate a session ID for this console session
    session_id = str(uuid.uuid4())[:8]  # Short session ID for console
    print(f"Session ID: {session_id}")
    
    # Initialize bot engine
    try:
        bot = ChatbotEngine(chroma_db_path=chroma_db_path)
        bot.load_model() 
        bot.load_data() 
        print("✅ Chatbot engine loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        return

    # Initialize response formatter
    formatter = ResponseFormatter()
    if formatter.is_available():
        print("✅ Response formatter (Gemini) loaded successfully.")
        print("🎨 Responses will be formatted for better readability!")
    else:
        print("⚠️ Response formatter not available - using raw responses.")
    
    print("\n" + "="*60)
    print(" 🤖 MULTILINGUAL ECOMMERCE SUPPORT BOT")
    print(" 🎨 Enhanced with AI-powered response formatting!")
    print(" 💬 Try: 'Where is my order?' or 'मेरा ऑर्डर कहाँ है?'")
    print(" 📋 Try: 'show my orders' for formatted display")
    print(" Type 'exit' to quit.")
    print("="*60 + "\n")

    pending_sql = None
    pending_items = None
    
    while True:
        try:
            user_input = input("👤 You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("🤖 Bot: Goodbye! Happy Shopping! 👋")
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
                    print(f"🤖 Bot: {parsed.get('message')}\n")
                else:
                    # Format the response using Gemini
                    formatted_response = formatter.format_response(user_input, response)
                    print(f"🤖 Bot: {formatted_response}\n")
            except:
                # Clear pending if we got a regular response
                pending_sql = None
                pending_items = None
                # Format the response using Gemini
                formatted_response = formatter.format_response(user_input, response)
                print(f"🤖 Bot: {formatted_response}\n")
            
        except KeyboardInterrupt:
            print("\n🤖 Bot: Goodbye! 👋")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
