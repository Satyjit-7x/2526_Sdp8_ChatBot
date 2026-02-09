from smart_formatter import SmartFormatter

def test_final_formatting():
    print("🧪 Final Smart Formatting Test")
    print("=" * 50)
    
    formatter = SmartFormatter()
    
    # Test cases that match your exact requirements
    test_cases = [
        {
            "name": "Full Order List",
            "question": "show my full order list",
            "response": "You have 8 total orders: • Wireless Charger (ORD003) - Returned - 2023-08-21 • Wireless Charger (ORD789) - Pending - 2026-02-09 • Car (ORD813) - Pending - 2026-02-09 • Laptop (ORD999) - Delivered - 2026-02-09 • Of Gaming Mouse (ORD917) - Pending - 2026-02-09 • Gaming Keyboard (ORD280) - Pending - 2026-02-09 • Laptop (ORD109) - Pending - 2026-02-09 • Mobile (ORD506) - Pending - 2026-02-09"
        },
        {
            "name": "Order Creation - Mobile",
            "question": "i want to order mobile",
            "response": "Operation completed successfully. Your order for Mobile has been created with order ID ORD123."
        },
        {
            "name": "Order Creation - Smartphone",
            "question": "create order for smartphone",
            "response": "Operation completed successfully. Smartphone order created."
        },
        {
            "name": "Single Order Status",
            "question": "what is the status of my order ORD999?",
            "response": "Your order ORD999 (Laptop) has status: Delivered"
        },
        {
            "name": "Confirmation Message",
            "question": "delete pending order",
            "response": "I am about to execute: `DELETE FROM orders WHERE order_id = 'ORD789'`. This will affect: Wireless Charger (ORD789). Are you sure? Yes to confirm. No to cancel."
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"❓ Question: {test['question']}")
        print(f"🤖 Original Response Length: {len(test['response'])} chars")
        print("🎨 Smart Formatted Response:")
        
        formatted = formatter.format_response(test['question'], test['response'])
        print(formatted)
        
        # Analysis
        lines = formatted.split('\n')
        print(f"📊 Analysis:")
        print(f"   • Lines: {len(lines)} (each line should be one order/item)")
        print(f"   • Characters: {len(formatted)} (should be shorter)")
        print(f"   • Has bullets: {'✅' if '•' in formatted else '❌'}")
        print(f"   • One per line: {'✅' if all('•' in line.strip() or line.strip() == '' for line in lines) else '❌'}")
        print("-" * 50)

if __name__ == "__main__":
    test_final_formatting()
