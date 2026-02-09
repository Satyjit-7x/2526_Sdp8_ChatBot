#!/usr/bin/env python3
"""
Test the improved bot logic with natural language queries
"""
from bot_engine import ChatbotEngine

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_natural"
    
    print("=" * 60)
    print("Testing Natural Language Query Understanding")
    print("=" * 60)
    
    # Test 1: "which products are pending"
    print("\n📝 TEST 1: Which products are pending?")
    print("-" * 60)
    response = bot.get_response("which products are pending", session_id=session)
    print(f"Bot Response:\n{response}\n")
    
    # Test 2: "what orders do I have"
    print("\n📝 TEST 2: What orders do I have?")
    print("-" * 60)
    response = bot.get_response("what orders do i have", session_id=session)
    print(f"Bot Response:\n{response}\n")
    
    # Test 3: "show me delivered orders"
    print("\n📝 TEST 3: Show me delivered orders")
    print("-" * 60)
    response = bot.get_response("show me delivered orders", session_id=session)
    print(f"Bot Response:\n{response}\n")
    
    # Test 4: "any returned items"
    print("\n📝 TEST 4: Any returned items?")
    print("-" * 60)
    response = bot.get_response("any returned items", session_id=session)
    print(f"Bot Response:\n{response}\n")
    
    # Test 5: Regular greeting (should NOT trigger SQL)
    print("\n📝 TEST 5: Hi (should use RAG, not SQL)")
    print("-" * 60)
    response = bot.get_response("hii", session_id=session)
    print(f"Bot Response:\n{response}\n")
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test()
