#!/usr/bin/env python3
"""
Test generic delete queries like 'delete pending', 'delete product which is pending'
"""
from bot_engine import ChatbotEngine
import sqlite3

def test():
    bot = ChatbotEngine()
    bot.load_data()
    
    session = "test_generic_delete"
    
    print("=" * 70)
    print("Testing Generic Delete Queries")
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
    
    # Test 1: delete pending (2 matches)
    print("\n✅ TEST 1: delete pending")
    print("-" * 70)
    sql = bot.generate_sql("delete pending")
    print(f"Generated SQL: {sql}")
    print(f"Expected: None (multiple matches) OR specific order if only one\n")
    
    # Test 2: delete product which is pending
    print("\n✅ TEST 2: delete product which is pending")
    print("-" * 70)
    sql = bot.generate_sql("delete product which is pending")
    print(f"Generated SQL: {sql}")
    print(f"Expected: None (multiple matches) ORspecific order if only one\n")
    
    # Test 3: delete order which is pending
    print("\n✅ TEST 3: delete order which is pending")
    print("-" * 70)
    sql = bot.generate_sql("delete order which is pending")
    print(f"Generated SQL: {sql}")
    print(f"Expected: None (multiple matches) OR specific order if only one\n")
    
    # Test 4: delete returned (should work - 1 match)
    print("\n✅ TEST 4: delete returned")
    print("-" * 70)
    sql = bot.generate_sql("delete returned")
    print(f"Generated SQL: {sql}")
    print(f"Expected: DELETE FROM orders WHERE order_id = 'ORD003'\n")
    
    # Test 5: delete status pending
    print("\n✅ TEST 5: delete status pending")
    print("-" * 70)
    sql = bot.generate_sql("delete status pending")
    print(f"Generated SQL: {sql}")
    print(f"Expected: None (multiple matches) OR specific order if only one\n")
    
    print("=" * 70)
    print("✅ Generic deletion tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test()
