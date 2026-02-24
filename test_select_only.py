from bot_engine import ChatbotEngine

def test_select_only():
    print("Testing _handle_select method only...")
    
    bot = ChatbotEngine()
    bot.load_model()
    bot.load_data()
    
    # Test the exact scenario that's causing the error
    test_sql = "SELECT order_id, product_name, order_date, status, price, quantity FROM orders"
    test_query = "show my orders"
    
    try:
        response = bot._handle_select(test_sql, test_query, "test")
        print(f"✅ _handle_select response: {response}")
    except Exception as e:
        print(f"❌ _handle_select error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_select_only()
