#!/usr/bin/env python3
"""
Test full conversation with generic delete queries
"""
from bot_engine import ChatbotEngine
import sqlite3

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_full_conversation"
    
    print("=" * 70)
    print("Testing Full Conversation with Generic Deletes")
    print("=" * 70)
    
    # Setup: Show what we have
    print("\n📦 DATABASE STATE:")
    print("-" * 70)
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, product, date, status FROM orders ORDER BY date DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[3]} ({row[2]})")
    conn.close()
    
    # Test 1: Ask to delete pending (should get clarification)
    print("\n📝 User: delete pending")
    print("-" * 70)
    response = bot.get_response("delete pending", session_id=session)
    print(f"Bot: {response}\n")
    
    # Test 2: Ask to delete product which is pending (should get clarification)
    print("\n📝 User: delete product which is pending")
    print("-" * 70)
    response = bot.get_response("delete product which is pending", session_id=session)
    print(f"Bot: {response}\n")
    
    # Test 3: Ask to delete returned (should work directly - only 1 match)
    print("\n📝 User: delete returned")
    print("-" * 70)
    response = bot.get_response("delete returned", session_id=session)
    print(f"Bot: {response}\n")
    
    # Test 4: Specific delete after clarification
    print("\n📝 User: delete smartphone")
    print("-" * 70)
    response = bot.get_response("delete smartphone", session_id=session)
    print(f"Bot: {response}\n")
    
    print("=" * 70)
    print("✅ Full conversation tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test()
