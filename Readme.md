# 🚀 E-Commerce Chatbot with Gemini AI

A smart, three-tier chatbot system for e-commerce customer support with product management, order tracking, and intelligent CRUD operations powered by Google Gemini AI.

## ✨ Key Features

✅ **Product Management**
- Browse 69+ products across 10 categories
- Search products by name/category
- Beautiful formatted product displays with emojis
- Product details (price, description, category)

✅ **Order Management (CRUD)**
- **Create**: Place new orders from products
- **Read**: View complete order history
- **Update**: Change order status (Pending → Shipped → Delivered)
- **Delete**: Cancel orders with confirmation

✅ **AI-Powered Responses**
- Google Gemini AI for natural language processing
- Context-aware conversation with session tracking
- FAQ retrieval using ChromaDB vector database (RAG)
- Beautiful, formatted responses with proper formatting

✅ **Session Management**
- User session tracking
- Conversation history per session
- Order history tied to user sessions
- Persistent data storage

---

## 📋 System Architecture

```
Frontend (React + Vite)
http://localhost:5173
        │
Node.js Backend (Express)
http://localhost:3001
        │
Python Backend (Flask + AI)
http://localhost:5001
        │
    SQLite3 + ChromaDB + Gemini API
```

---

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- SQLite3
- Gemini API Key

### Step 1: Setup Python
```bash
cd 2526_sdp8_chatbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Setup Gemini API
```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Step 3: Initialize Database
```bash
python setup_database.py
```

### Step 4: Setup Node.js Backend
```bash
cd backend
npm install
```

### Step 5: Setup React Frontend
```bash
cd frontend
npm install
```

---

## 🚀 Running the Application

Open 3 different terminals:

**Terminal 1: Flask Backend**
```bash
python app.py
# Runs on http://localhost:5001
```

**Terminal 2: Node.js Backend**
```bash
cd backend && npm start
# Runs on http://localhost:3001
```

**Terminal 3: React Frontend**
```bash
cd frontend && npm run dev
# Runs on http://localhost:5173
```

Visit: **http://localhost:5173**

---

## 💬 Usage Examples

### Browse Products
```
User: "Show me gaming products"
Bot: "📦 Available Products in Gaming:
     1. **Gaming Mouse** - ₹1999"
```

### Create Order
```
User: "place order for Gaming Mouse"
Bot: "✅ Order ORD456 created!"
```

### View Orders
```
User: "show my orders"
Bot: "Your Orders:
     1. ORD456 - Gaming Mouse [Pending]"
```

### Update Order
```
User: "mark order as delivered"
Bot: "✅ Order updated to Delivered"
```

### Cancel Order
```
User: "cancel my order"
Bot: "✅ Order cancelled"
```

---

## 📊 Database Schema

**Products** (69 items across 10 categories)
- Accessories, Audio, Books, Cameras, Clothing, Computing, Gaming, Health, Home, Mobile

**Orders**
- order_id, session_id, product_id, product_name, price, quantity, status

**Conversation History**
- id, session_id, timestamp, user_message, bot_response

---

## 📁 Project Structure

```
2526_sdp8_chatbot/
├── app.py                    # Flask API Server
├── bot_engine.py             # AI Engine & Logic
├── setup_database.py         # Database Initialization
├── orders.db                 # SQLite Database
├── ARCHITECTURE.md           # Detailed Design
├── backend/                  # Node.js Express
├── frontend/                 # React + Vite
└── data/chroma_db/          # Vector Database
```

---

## 🔌 API Endpoints

```
POST /api/chat                              # Send message
GET /api/products                           # All products
GET /api/products?category=Gaming           # Filter by category
GET /api/orders                             # User orders
POST /api/orders                            # Create order
PUT /api/orders/<id>                        # Update order
DELETE /api/orders/<id>                     # Delete order
```

---

## ✅ Testing

```bash
# Test syntax
python -m py_compile app.py bot_engine.py setup_database.py

# Test database
sqlite3 orders.db "SELECT COUNT(*) FROM products"

# Test API
curl http://localhost:5001/api/products/categories
```

---

## 🧠 Bot Intelligence

- Product queries: "Show me gaming products", "Find laptops"
- Order operations: "Create order", "Mark as delivered", "Cancel order"
- Session tracking: Per-user orders and history
- Natural language understanding via Gemini AI

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -i :5001 | awk 'NR==2 {print $2}' | xargs kill -9
lsof -i :3001 | awk 'NR==2 {print $2}' | xargs kill -9
lsof -i :5173 | awk 'NR==2 {print $2}' | xargs kill -9
```

### Reset Database
```bash
rm orders.db
python setup_database.py
```

### Reinstall Dependencies
```bash
pip install -r requirements.txt
cd backend && npm install
cd frontend && npm install
```

### Gemini API Issues
- Verify GEMINI_API_KEY in .env
- Check API key validity at [Google AI Studio](https://aistudio.google.com)
- Ensure quota remaining

---

## 🚀 Production Deployment

1. Use environment variables for secrets
2. Setup SSL/TLS certificates
3. Use PostgreSQL instead of SQLite
4. Add load balancer
5. Implement rate limiting
6. Add authentication
7. Setup monitoring

---

## 📚 Documentation

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

---

## 📞 Support

Issues? Check:
1. .env has GEMINI_API_KEY
2. All 3 services running
3. Check terminal logs
4. Verify ports free (5001, 3001, 5173)
5. Reset database if needed

---

**Status**: ✅ Production Ready  
**Python**: 3.10+  
**Node.js**: 16+  
**Updated**: February 16, 2026
