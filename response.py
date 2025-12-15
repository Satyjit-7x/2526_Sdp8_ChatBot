import json
import random

with open('response.json','r') as f:
    response = json.load(f)

def get_response(intent):
    if intent in response:
        return random.choice(response[intent])
    else:
        return "I'm sorry, I don't understand."
    print("🤖 Chatbot is running! Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        print("Bot: Goodbye! 👋")
        break

    intent = get_response(user_input)
    reply = get_response(intent)

    print("Bot:", reply)
