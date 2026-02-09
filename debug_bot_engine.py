from bot_engine import ChatbotEngine

def debug_bot_engine():
    print("🔍 Debugging Bot Engine")
    print("=" * 40)
    
    try:
        bot = ChatbotEngine()
        bot.load_model()
        bot.load_data()
        print("✅ Bot engine initialized successfully")
        
        # Test order queries
        test_queries = [
            "ORD999",
            "what is ORD999?",
            "show order ORD999"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing: {query}")
            try:
                result = bot.get_response(query, session_id="test")
                print(f"🤖 Response: {result}")
            except Exception as e:
                print(f"❌ Error in get_response: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_bot_engine()
