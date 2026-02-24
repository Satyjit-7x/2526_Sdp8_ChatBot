from bot_engine import ChatbotEngine

def test_smart_order_filtering():
    print("🧪 Testing Smart Order Filtering")
    print("=" * 50)
    
    bot = ChatbotEngine()
    bot.load_model()
    bot.load_data()
    
    test_queries = [
        "show my orders",
        "what is pending order list", 
        "delivered orders",
        "show pending orders",
        "what are my shipped orders",
        "returned orders list",
        "cancelled orders"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            response = bot.get_response(query, session_id="test")
            print(f"🤖 Response:\n{response}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("=" * 50)

if __name__ == "__main__":
    test_smart_order_filtering()
