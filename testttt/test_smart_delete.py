#!/usr/bin/env python3
"""
Test smart deletion with qualifiers
"""
from bot_engine import ChatbotEngine
import json

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_smart_delete"
    
    print("=" * 70)
    print("Testing Smart Deletion with Qualifiers")
    print("=" * 70)
    
    # Setup: Show what we have
    print("\n📦 DATABASE STATE:")
    print("-" * 70)
    import sqlite3
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, product, date, status FROM orders ORDER BY date DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[3]} ({row[2]})")
    conn.close()
    
    # Test 1: Delete with status qualifier
    print("\n✅ TEST 1: delete wireless charger which is returned")
    print("-" * 70)
    sql = bot.generate_sql("delete wireless charger which is returned")
    print(f"Generated SQL: {sql}")
    if sql:
        expected = "DELETE FROM orders WHERE order_id = 'ORD003'"
        print(f"Expected: {expected}")
        print(f"Match: {sql == expected}\n")
    
    # Test 2: Delete latest
    print("\n✅ TEST 2: delete latest wireless charger")
    print("-" * 70)
    sql = bot.generate_sql("delete latest wireless charger")
    print(f"Generated SQL: {sql}")
    if sql:
        expected = "DELETE FROM orders WHERE order_id = 'ORD789'"
        print(f"Expected: {expected}")
        print(f"Match: {sql == expected}\n")
    
    # Test 3: Delete oldest
    print("\n✅ TEST 3: delete oldest wireless charger")
    print("-" * 70)
    sql = bot.generate_sql("delete oldest wireless charger")
    print(f"Generated SQL: {sql}")
    if sql:
        expected = "DELETE FROM orders WHERE order_id = 'ORD003'"
        print(f"Expected: {expected}")
        print(f"Match: {sql == expected}\n")
    
    # Test 4: Delete pending one
    print("\n✅ TEST 4: delete pending wireless charger")
    print("-" * 70)
    sql = bot.generate_sql("delete pending wireless charger")
    print(f"Generated SQL: {sql}")
    if sql:
        expected = "DELETE FROM orders WHERE order_id = 'ORD789'"
        print(f"Expected: {expected}")
        print(f"Match: {sql == expected}\n")
    
    # Test 5: Delete single match (smartphone)
    print("\n✅ TEST 5: delete smartphone")
    print("-" * 70)
    sql = bot.generate_sql("delete smartphone")
    print(f"Generated SQL: {sql}")
    if sql:
        expected = "DELETE FROM orders WHERE order_id = 'ORD490'"
        print(f"Expected: {expected}")
        print(f"Match: {sql == expected}\n")
    
    print("=" * 70)
    print("✅ Smart deletion tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test()
