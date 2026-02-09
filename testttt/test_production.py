#!/usr/bin/env python3
"""
Quick test for production-ready chatbot (no Gemini API needed)
"""
from bot_engine import ChatbotEngine

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_prod"
    
    # Test 1: Show orders
    print("\n=== TEST 1: Show orders ===")
    resp = bot.get_response("show all orders", session_id=session)
    print(resp)
    
    # Test 2: Delete mobile
    print("\n=== TEST 2: Delete mobile ===")
    resp = bot.get_response("delete mobile", session_id=session)
    import json
    try:
        data = json.loads(resp)
        print(f"Confirmation: {data.get('message')}")
        print(f"Affected: {data.get('affected_items')}")
        
        # Confirm deletion
        print("\n=== Confirming with 'yes' ===")
        resp2 = bot.get_response("yes", pending_action=data.get('sql'), 
                                pending_items=data.get('affected_items'), session_id=session)
        print(resp2)
    except:
        print(resp)
    
    # Test 3: Memory query
    print("\n=== TEST 3: What did you delete? ===")
    resp = bot.get_response("what product did you just remove?", session_id=session)
    print(resp)
    
    # Check database
    print("\n=== Database Check ===")
    import sqlite3
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, operation_type, affected_items FROM conversation_history WHERE session_id = ? ORDER BY timestamp", (session,))
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    test()
