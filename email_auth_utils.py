import sqlite3
import hashlib
import hmac
import secrets
from datetime import datetime

db_path = 'orders.db'

def hash_password(password: str) -> str:
    """Hash password using PBKDF2"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = password_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False

def register_user(email: str, password: str, name: str = None) -> dict:
    """Register new user with email and password"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if user already exists
        c.execute('SELECT user_id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            return {'error': 'Email already registered', 'success': False}
        
        # Hash password and create user
        password_hash = hash_password(password)
        c.execute('''
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', (email, password_hash, name or email.split('@')[0]))
        
        conn.commit()
        user_id = c.lastrowid
        
        return {
            'success': True,
            'user_id': user_id,
            'email': email,
            'name': name or email.split('@')[0]
        }
    except Exception as e:
        return {'error': str(e), 'success': False}
    finally:
        conn.close()

def login_user(email: str, password: str) -> dict:
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('SELECT user_id, email, name, password_hash FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if not user:
            return {'error': 'Email not found', 'success': False}
        
        user_id, db_email, name, password_hash = user
        
        if not verify_password(password, password_hash):
            return {'error': 'Incorrect password', 'success': False}
        
        return {
            'success': True,
            'user_id': user_id,
            'email': db_email,
            'name': name
        }
    except Exception as e:
        return {'error': str(e), 'success': False}
    finally:
        conn.close()

def get_user(user_id: int) -> dict:
    """Get user info by ID"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('SELECT user_id, email, name, created_at FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if not user:
            return None
        
        return {
            'user_id': user[0],
            'email': user[1],
            'name': user[2],
            'created_at': user[3]
        }
    finally:
        conn.close()

def get_user_orders(user_id: int) -> list:
    """Get all orders for a user"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT o.order_id, o.product_id, p.name, o.quantity, o.total_price, o.status, o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        ''', (user_id,))
        
        orders = []
        for row in c.fetchall():
            orders.append({
                'order_id': row[0],
                'product_id': row[1],
                'product_name': row[2],
                'quantity': row[3],
                'total_price': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        
        return orders
    finally:
        conn.close()
