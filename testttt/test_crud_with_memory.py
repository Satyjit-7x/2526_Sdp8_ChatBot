"""
Test script for CRUD operations with conversation memory

This script tests:
1. Creating orders
2. Reading orders
3. Deleting orders
4. Asking about recent actions (conversation memory)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bot_engine import ChatbotEngine
import uuid

def test_crud_with_memory():
    print("\n" + "="*60)
    print(" TESTING CRUD OPERATIONS WITH CONVERSATION MEMORY")
    print("="*60 + "\n")
    
    # Initialize bot
    bot = ChatbotEngine()
    try:
        bot.load_model()
        bot.load_data()
    except Exception as e:
        print(f"Warning: {e}")
    
    # Create a test session
    session_id = "test_" + str(uuid.uuid4())[:8]
    print(f"Test Session ID: {session_id}\n")
    
    # Test 1: Show all orders
    print("TEST 1: Show all orders")
    print("-" * 60)
    response = bot.get_response("Show me all orders", session_id=session_id)
    print(f"Response: {response}\n")
    
    # Test 2: Create a new order
    print("TEST 2: Create a new order for Laptop")
    print("-" * 60)
    response = bot.get_response("Create a new order for Laptop", session_id=session_id)
    print(f"Response: {response}")
    
    # If confirmation required, simulate yes
    if "Are you sure" in response:
        print("\nConfirming with 'yes'...")
        response = bot.get_response("yes", session_id=session_id, pending_action=response.split("`")[1] if "`" in response else None)
        print(f"Response: {response}\n")
    
    # Test 3: Ask what was just created (memory query)
    print("TEST 3: What did I just create?")
    print("-" * 60)
    response = bot.get_response("What did I just create?", session_id=session_id)
    print(f"Response: {response}\n")
    
    # Test 4: Delete an order
    print("TEST 4: Delete order ORD002")
    print("-" * 60)
    response = bot.get_response("Delete order ORD002", session_id=session_id)
    print(f"Response: {response}")
    
    # Simulate confirmation
    if "Are you sure" in response:
        import json
        try:
            parsed = json.loads(response)
            sql = parsed.get("sql")
            print("\nConfirming deletion with 'yes'...")
            response = bot.get_response("yes", session_id=session_id, pending_action=sql)
            print(f"Response: {response}\n")
        except:
            print("\nManual confirmation needed\n")
    
    # Test 5: Ask what was just deleted (memory query)
    print("TEST 5: What product did you just remove?")
    print("-" * 60)
    response = bot.get_response("What product did you just remove?", session_id=session_id)
    print(f"Response: {response}\n")
    
    # Test 6: View conversation history
    print("TEST 6: View conversation history from database")
    print("-" * 60)
    import sqlite3
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_message, bot_response, operation_type, affected_items 
        FROM conversation_history 
        WHERE session_id = ?
        ORDER BY timestamp
    ''', (session_id,))
    
    history = cursor.fetchall()
    for idx, (user_msg, bot_resp, op_type, affected) in enumerate(history, 1):
        print(f"{idx}. User: {user_msg[:50]}...")
        print(f"   Bot: {bot_resp[:50]}...")
        print(f"   Type: {op_type}, Items: {affected}")
        print()
    
    conn.close()
    
    print("="*60)
    print(" ALL TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_crud_with_memory()
