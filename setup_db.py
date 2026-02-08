import sqlite3
import os

def setup_database():
    db_path = "orders.db"
    
    # Remove existing db to start fresh if needed
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            product TEXT NOT NULL,
            date TEXT,
            status TEXT
        )
    ''')
    
    # Dummy data from bot_engine/frontend
    dummy_orders = [
      ('ORD001', 'Mobile', '2023-10-03', 'Delivered'),
      ('ORD002', 'Headphones', '2023-09-15', 'Shipped'),
      ('ORD003', 'Wireless Charger', '2023-08-21', 'Returned'),
      ('ORD004', 'Smartwatch', '2023-07-02', 'Delivered')
    ]
    
    cursor.executemany('INSERT INTO orders (order_id, product, date, status) VALUES (?, ?, ?, ?)', dummy_orders)
    
    conn.commit()
    print(f"Database {db_path} created with {len(dummy_orders)} records.")
    
    # Verify
    cursor.execute('SELECT * FROM orders')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    setup_database()
