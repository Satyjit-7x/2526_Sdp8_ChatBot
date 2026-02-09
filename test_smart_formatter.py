from smart_formatter import SmartFormatter

def test_smart_formatter():
    print("🧪 Testing Smart Formatter")
    print("=" * 40)
    
    formatter = SmartFormatter()
    
    test_cases = [
        {
            "question": "show my orders",
            "response": "You have 3 total orders: • Wireless Charger (ORD003) - Returned - 2023-08-21 • Laptop (ORD999) - Delivered - 2026-02-09 • Gaming Mouse (ORD917) - Pending - 2026-02-09"
        },
        {
            "question": "status of ORD999?",
            "response": "Your order ORD999 (Laptop) has status: Delivered"
        },
        {
            "question": "delete pending",
            "response": "I found 2 pending orders: Wireless Charger (ORD789), Car (ORD813). Which one would you like to delete?"
        },
        {
            "question": "confirm action",
            "response": "I am about to execute: `DELETE FROM orders WHERE order_id = 'ORD123'`. Are you sure? Yes to confirm. No to cancel."
        },
        {
            "question": "general help",
            "response": "I can help you with order management. You can ask me to show orders, create orders, or check order status. I'm here to assist you with your e-commerce needs."
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}")
        print(f"❓ Q: {test['question']}")
        print(f"🤖 Original: {test['response'][:60]}...")
        print("🎨 Smart Formatted:")
        formatted = formatter.format_response(test['question'], test['response'])
        print(formatted)
        print("-" * 40)

if __name__ == "__main__":
    test_smart_formatter()
