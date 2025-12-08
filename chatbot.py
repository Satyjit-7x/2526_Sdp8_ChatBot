import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

def chat_loop():
    chat = client.chats.create(model="gemini-2.5-flash")

    print("Chatbot ready! Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower().strip() in ["exit", "quit", "bye"]:
            print("Bot: Bye !")
            break

        response = chat.send_message(user_input)

        bot_reply = response.text.strip()
        print("Bot:", bot_reply)
        print()

if __name__ == "__main__":
    chat_loop()
