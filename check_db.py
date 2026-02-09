import sqlite3

def check_database():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
    tables = cursor.fetchall()
    print("📊 Database Tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "="*50)
    
    # Check conversation_history table structure
    if ('conversation_history',) in tables:
        cursor.execute('PRAGMA table_info(conversation_history);')
        columns = cursor.fetchall()
        print("🗂️ conversation_history Table Structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Count records
        cursor.execute('SELECT COUNT(*) FROM conversation_history')
        count = cursor.fetchone()[0]
        print(f"\n📝 Total conversation records: {count}")
        
        if count > 0:
            # Show recent records
            cursor.execute('SELECT session_id, timestamp, user_message, bot_response FROM conversation_history ORDER BY timestamp DESC LIMIT 5')
            recent = cursor.fetchall()
            print("\n📋 Recent conversations:")
            for i, (session_id, timestamp, user_msg, bot_resp) in enumerate(recent, 1):
                print(f"  {i}. Session: {session_id} | {timestamp}")
                print(f"     User: {user_msg[:50]}{'...' if len(user_msg) > 50 else ''}")
                print(f"     Bot:  {bot_resp[:50]}{'...' if len(bot_resp) > 50 else ''}")
                print()
    
    # Check orders table
    if ('orders',) in tables:
        cursor.execute('SELECT COUNT(*) FROM orders')
        order_count = cursor.fetchone()[0]
        print(f"📦 Total orders in database: {order_count}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
