
import os
from bot_engine import ChatbotEngine

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

            # Get Response (Directly supported by multilingual model)
            response = bot.get_response(user_input) 
            print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
