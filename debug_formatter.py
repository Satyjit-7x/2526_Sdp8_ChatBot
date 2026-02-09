from smart_formatter import SmartFormatter

def debug_formatter():
    print("🔍 Debugging Smart Formatter")
    print("=" * 40)
    
    try:
        formatter = SmartFormatter()
        print("✅ Formatter initialized successfully")
        
        # Test simple case
        test_response = "Your order ORD999 (Laptop) has status: Delivered"
        test_question = "what is ORD999?"
        
        print(f"📝 Testing: {test_question}")
        print(f"🤖 Response: {test_response}")
        
        result = formatter.format_response(test_question, test_response)
        print(f"🎨 Formatted: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_formatter()
