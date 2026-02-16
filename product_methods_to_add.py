"""
These three methods should be added to the ChatbotEngine class in bot_engine.py.
Add them after the format_context_for_llm method (around line 123).
"""

def get_available_products(self):
    """Get list of all available product names"""
    try:
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE in_stock = 1 ORDER BY name")
        products = [ row[0] for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def validate_product(self, product_name):
    """Validate product name and suggest alternatives if not found"""
    available = self.get_available_products()
    
    # Exact match (case-insensitive)
    for product in available:
        if product.lower() == product_name.lower():
            return product, True  # Return exact match
    
    # Fuzzy match (partial)
    matches = [p for p in available if product_name.lower() in p.lower()]
    if matches:
        return matches, False  # Return suggestions
    
    return None, False

def get_products_by_category(self, category_name):
    """Get all products in a specific category
    
    Example queries it handles:
    - "show me smartphones"
    - "I want to buy laptop" or "laptops"  
    - "what audio products do you have"
    """
    try:
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fuzzy category match (supports plurals, partial names)
        # Will match "smartphone" to "Smartphones", "laptop" to "Laptops", etc.
        cursor.execute("""
            SELECT name, price, description, category 
            FROM products 
            WHERE in_stock = 1 
            AND (LOWER(category) LIKE ? OR LOWER(category) LIKE ?)
            ORDER BY price
        """, (f'%{category_name.lower()}%', f'%{category_name.lower()}s%'))
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            products = []
            for row in results:
                products.append({
                    'name': row[0],
                    'price': row[1],
                    'description': row[2],
                    'category': row[3]
                })
            return products
        return None
    except Exception as e:
        print(f"Error fetching products by category: {e}")
        return None
