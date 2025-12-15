
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
    print("="*50 + "\n")

    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower().strip() in ["exit", "quit", "bye"]:
                print("Bot: Goodbye! Happy Shopping.")
                break
            
            if not user_input.strip():
                continue
            
            response = bot.get_response(user_input) # print response from bot
            print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
