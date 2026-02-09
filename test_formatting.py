from response_formatter import ResponseFormatter

def test_formatting():
    print("🧪 Testing Response Formatter")
    print("=" * 50)
    
    formatter = ResponseFormatter()
    
    if not formatter.is_available():
        print("❌ Gemini not available. Please set GEMINI_API_KEY in .env file")
        return
    
    # Test cases
    test_cases = [
        {
            "question": "show my orders",
            "response": "You have 3 total orders: • Wireless Charger (ORD003) - Returned - 2023-08-21 • Laptop (ORD999) - Delivered - 2026-02-09 • Gaming Mouse (ORD917) - Pending - 2026-02-09"
        },
        {
            "question": "what is the status of my order ORD999?",
            "response": "Your order ORD999 (Laptop) has status: Delivered"
        },
        {
            "question": "create order for smartphone",
            "response": "Operation completed successfully."
        },
        {
            "question": "delete pending order",
            "response": "I found 2 pending orders: Wireless Charger (ORD789), Car (ORD813). Which one would you like to delete?"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}")
        print(f"❓ Question: {test['question']}")
        print(f"🤖 Original Response: {test['response']}")
        print("🎨 Formatted Response:")
        formatted = formatter.format_response(test['question'], test['response'])
        print(formatted)
        print("-" * 50)

if __name__ == "__main__":
    test_formatting()
