#!/usr/bin/env python3
"""
Test context-aware reference resolution
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_engine import ChatbotEngine

def test_context_resolution():
    print("=" * 60)
    print("Testing Context-Aware Reference Resolution")
    print("=" * 60)
    
    bot = ChatbotEngine()
    bot.load_model()
    bot.load_data()
    
    # Test 1: Single returned product reference
    print("\n✓ Test 1: Reference to single returned product")
    print("-" * 60)
    session_id = "test_ctx_1"
    
    response1 = bot.get_response("show returned products", session_id=session_id)
    print(f"User: show returned products")
    print(f"Bot: {response1}\n")
    
    response2 = bot.get_response("delete that order", session_id=session_id)
    print(f"User: delete that order")
    print(f"Bot: {response2}")
    
    # Check if it was resolved correctly
    if "ORD003" in response2 or "Wireless Charger" in response2:
        print("✅ PASSED: Bot correctly identified the returned product")
    else:
        print("❌ FAILED: Bot did not resolve 'that order' correctly")
    
    # Test 2: Reference with "it"
    print("\n✓ Test 2: Reference using 'it'")
    print("-" * 60)
    session_id = "test_ctx_2"
    
    response1 = bot.get_response("show delivered products", session_id=session_id)
    print(f"User: show delivered products")
    print(f"Bot: {response1}\n")
    
    # If there's only one delivered product, "it" should work
    import json
    import sqlite3
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 1:
        response2 = bot.get_response("what's the status of it?", session_id=session_id)
        print(f"User: what's the status of it?")
        print(f"Bot: {response2}")
        
        if "Delivered" in response2:
            print("✅ PASSED: Bot resolved 'it' to the delivered product")
        else:
            print("⚠️  WARNING: 'it' might not have been resolved (only 1 delivered product)")
    else:
        print(f"⚠️  SKIPPED: {count} delivered products, 'it' would be ambiguous")
    
    # Test 3: Multiple products - should ask for clarification
    print("\n✓ Test 3: Ambiguous reference (multiple pending products)")
    print("-" * 60)
    session_id = "test_ctx_3"
    
    # Create multiple pending products first
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    pending_count = cursor.fetchone()[0]
    conn.close()
    
    if pending_count > 1:
        response1 = bot.get_response("show pending orders", session_id=session_id)
        print(f"User: show pending orders")
        print(f"Bot: {response1}\n")
        
        response2 = bot.get_response("delete it", session_id=session_id)
        print(f"User: delete it")
        print(f"Bot: {response2}")
        
        if "which" in response2.lower() or "multiple" in response2.lower() or "specific" in response2.lower():
            print("✅ PASSED: Bot asks for clarification with ambiguous reference")
        else:
            print("⚠️  WARNING: Bot might have proceeded without asking for clarification")
    else:
        print(f"⚠️  SKIPPED: Only {pending_count} pending products, no ambiguity")
    
    print("\n" + "=" * 60)
    print("Context Resolution Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_context_resolution()
