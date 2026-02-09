#!/usr/bin/env python3
"""
Test improved human-readable responses and memory
"""
from bot_engine import ChatbotEngine
import json

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_human_readable"
    
    print("=" * 70)
    print("Testing Human-Readable Responses")
    print("=" * 70)
    
    # Test 1: Single result query
    print("\n✅ TEST 1: Which products are pending?")
    print("-" * 70)
    response = bot.get_response("which products are pending", session_id=session)
    print(f"Response: {response}\n")
    
    # Test 2: Multiple results query
    print("\n✅ TEST 2: Show all orders")
    print("-" * 70)
    response = bot.get_response("show all orders", session_id=session)
    print(f"Response: {response}\n")
    
    # Test 3: Delete with memory tracking
    print("\n✅ TEST 3: Delete watch")
    print("-" * 70)
    response = bot.get_response("delete watch", session_id=session)
    try:
        data = json.loads(response)
        print(f"Confirmation: {data.get('message')}")
        print("\nConfirming with 'yes'...")
        response2 = bot.get_response("yes", pending_action=data.get('sql'), 
                                    pending_items=data.get('affected_items'), session_id=session)
        print(f"Response: {response2}\n")
    except:
        print(f"Response: {response}\n")
    
    # Test 4: Memory query
    print("\n✅ TEST 4: Which product deleted?")
    print("-" * 70)
    response = bot.get_response("which product deleted ?", session_id=session)
    print(f"Response: {response}\n")
    
    # Test 5: Another memory query variation
    print("\n✅ TEST 5: What did you delete?")
    print("-" * 70)
    response = bot.get_response("what did you delete", session_id=session)
    print(f"Response: {response}\n")
    
    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test()
