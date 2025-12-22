
import os
from bot_engine import ChatbotEngine

def main():
    dataset_path = "data/english_support_dataset.csv"
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please run 'python3 download_dataset.py' first.")
        return

    #initialization of bot engine
    try:
        bot = ChatbotEngine(
            data_path=dataset_path,
            query_col="user_query_en",
            response_col="bot_response_en"
        )

        bot.load_data()
        
        bot.train() # vectorize data and train bot
    except Exception as e:
        print(f"Failed to start: {e}")
        return

    
    print("\n" + "="*50)
    print(" ECOMMERCE SUPPORT BOT (Ready to help!)")
    print(" Try asking: 'Where is my order?' or 'I want a refund'")
    print(" Type 'exit' to quit.")
    print(" Type 'translate to [language]' to translate the last bot response.")
    print("="*50 + "\n")

    last_response = ""

    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("Bot: Goodbye! Happy Shopping.")
                break
            
            if not user_input.strip():
                continue

            # Check for explicit translation command
            if user_input.lower().startswith("translate to "):
                if not last_response:
                    print("Bot: I haven't said anything yet to translate!")
                    continue
                
                target_lang = user_input.lower().replace("translate to ", "").strip()
                print(f"Bot (translating to {target_lang})...")
                translated_response = bot.translate_from_english(last_response, target_lang)
                print(f"Bot: {translated_response}\n")
                continue

            # 1. Translate User Input to English (if needed) for processing
            english_input = bot.translate_to_english(user_input)
            
            # 2. Get Response (English)
            response_en = bot.get_response(english_input) 
            last_response = response_en

            print(f"Bot: {response_en}\n")
            
        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
