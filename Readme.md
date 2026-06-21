<p align="center">
  <h1 align="center">🛒 AI Chatbot -Smart e-commerce companion</h1>
  <p align="center">
    An intelligent, three-tier e-commerce chatbot powered by <strong>Google Gemini AI</strong> and <strong>Retrieval-Augmented Generation (RAG)</strong> for natural-language product browsing, order management, and customer support.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Vite-7-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Express-5-000000?style=for-the-badge&logo=express&logoColor=white" alt="Express"/>
  <img src="https://img.shields.io/badge/Gemini_AI-Powered-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI"/>
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/ChromaDB-RAG-FF6F00?style=for-the-badge" alt="ChromaDB"/>
</p>

---

## 📖 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Running the Application](#-running-the-application)
- [Usage Examples](#-usage-examples)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Environment Variables](#-environment-variables)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧐 About the Project

**ShopBot AI** is a full-stack, AI-powered e-commerce chatbot that enables users to browse products, place orders, and manage their shopping experience through natural language conversations. The system combines:

- **RAG (Retrieval-Augmented Generation)** via ChromaDB for accurate FAQ and knowledge-base responses
- **Google Gemini 2.0 Flash** for intent classification, natural language understanding, and response generation
- **Full CRUD operations** on an SQLite database for orders and products
- **Role-based access** with a dedicated admin panel for managing users, orders, and products

This project was developed as part of the **SDP8 (Software Development Project 8)** coursework for the **2025–26** academic session.

---

## ✨ Key Features

### 🤖 AI-Powered Chat
- **Gemini 2.0 Flash LLM** for natural language understanding and response generation
- **RAG pipeline** with SentenceTransformer embeddings + ChromaDB vector store
- **Hybrid intent classification** — Gemini LLM with intelligent keyword fallback
- **Context-aware conversations** — session history tracking for multi-turn dialogue

### 🛍️ Product Management
- Browse products across categories 
- Search products by name, description, or category
- Product details with pricing, availability, and descriptions
- Admin: create, update, and toggle product stock status

### 📦 Order Management (CRUD)
- **Create** — Place orders via natural language (e.g., *"Buy a gaming mouse"*)
- **Read** — View order history with status tracking
- **Update** — Change order status (Pending → Shipped → Delivered / Cancelled / Returned)
- **Delete** — Remove orders with confirmation prompts
- Contextual order referencing (e.g., *"Cancel that order"* uses conversation context)

### 🔐 Authentication & Authorization
- Email/password registration and login
- JWT-based session management (7-day expiry)
- Role-based access control (**User** vs **Admin**)
- Default admin account seeded on first startup
- Persistent sessions via `localStorage`

### 📊 Admin Dashboard
- View all orders across all users
- Manage order statuses (Pending, Shipped, Delivered, Cancelled, Returned)
- User management with order counts
- Product inventory management (add/edit/toggle stock)
- Dashboard statistics (total orders, revenue, users, status breakdown)

### 💬 Smart Conversation
- Greeting handling with time-of-day awareness
- FAQ responses from trained knowledge base
- Help and platform capability queries
- Graceful fallbacks for unrecognized inputs
- Support for casual conversation (thanks, goodbye, etc.)

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                           │
│                   React 19 + Vite (Port 5173)                   │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐   │
│  │LoginPage │   │ ChatPage │   │AdminPanel │   │AuthContext│   │
│  └────┬─────┘   └────┬─────┘   └─────┬─────┘   └────┬─────┘   │
└───────┼──────────────┼────────────────┼──────────────┼─────────┘
        │              │                │              │
        ▼              ▼                ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   NODE.JS MIDDLEWARE (Port 3001)                 │
│                      Express 5 + JWT Auth                       │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────┐            │
│  │ email-auth.js│  │ chat.js  │  │  products.js   │            │
│  │  (Register/  │  │ (Proxy → │  │ (Product CRUD) │            │
│  │  Login/JWT)  │  │  Flask)  │  │                │            │
│  └──────────────┘  └────┬─────┘  └────────────────┘            │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                 PYTHON AI BACKEND (Port 5001)                   │
│                    Flask + Gemini AI Engine                      │
│                                                                  │
│  ┌──────────┐    ┌───────────────────────────────┐              │
│  │  app.py  │───▶│       bot_engine.py            │              │
│  │ (Flask   │    │  ┌─────────┐ ┌──────────────┐ │              │
│  │  Routes) │    │  │ChromaDB │ │ Gemini 2.0   │ │              │
│  └──────────┘    │  │  (RAG)  │ │ Flash (LLM)  │ │              │
│                  │  └─────────┘ └──────────────┘ │              │
│                  │  ┌─────────┐ ┌──────────────┐ │              │
│                  │  │ SQLite  │ │   Intent     │ │              │
│                  │  │  (DB)   │ │ Classifier   │ │              │
│                  │  └─────────┘ └──────────────┘ │              │
│                  └───────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

### Request Pipeline

1. **User types a message** → React frontend sends it to the Node.js middleware
2. **Node.js middleware** proxies the request to the Flask AI backend
3. **Bot Engine** retrieves relevant context from ChromaDB (RAG)
4. **Gemini AI** classifies intent and extracts entities
5. **Database operations** execute based on classified intent (CRUD on SQLite)
6. **Gemini AI** formats a natural, polished response using RAG + DB results
7. **Response flows back** through Node.js → React → displayed to the user

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, Vite 7, Vanilla CSS | UI: Login, Chat, Admin Panel |
| **Middleware** | Node.js, Express 5, JWT, better-sqlite3 | Auth, routing, chat proxy |
| **AI Backend** | Python 3.10+, Flask, Google Gemini AI | Chat engine, intent classification |
| **RAG** | ChromaDB, SentenceTransformers (`all-MiniLM-L6-v2`) | Knowledge base retrieval |
| **Database** | SQLite3 | Orders, products, users, conversation history |
| **Auth** | PBKDF2 (SHA-256), JSON Web Tokens | Secure password hashing, session tokens |

---

## 📁 Project Structure

```
2526_sdp8_chatbot/
│
├── app.py                        # Flask API server (REST endpoints)
├── bot_engine.py                 # Core AI engine (RAG + Gemini + CRUD logic)
├── email_auth_utils.py           # Python auth helpers (hash, verify, register)
├── setup_email_auth.py           # Database schema initialization script
├── requirements.txt              # Python dependencies (pip install -r)
├── start.sh                      # Quick start script (Linux/macOS)
├── orders.db                     # SQLite database (auto-generated)
├── .env.example                  # Environment variables template
├── .env                          # Environment variables (create from .env.example)
├── .gitignore                    # Git ignore rules
│
├── backend/                      # Node.js Express middleware
│   ├── server.js                 #   Express app entry point
│   ├── routes/
│   │   ├── chat.js               #   Chat proxy → Flask backend
│   │   ├── email-auth.js         #   Auth routes (register/login/verify)
│   │   └── products.js           #   Product CRUD routes
│   └── package.json              #   Node.js dependencies
│
├── frontend/                     # React + Vite frontend
│   ├── index.html                #   HTML entry point
│   ├── vite.config.js            #   Vite configuration
│   ├── src/
│   │   ├── main.jsx              #   React entry point
│   │   ├── App.jsx               #   Root component (routing logic)
│   │   ├── App.css               #   Global styles
│   │   ├── index.css             #   Base CSS
│   │   ├── context/
│   │   │   └── AuthContext.jsx   #   Authentication state management
│   │   └── components/
│   │       ├── LoginPage.jsx     #   Login/Register UI
│   │       ├── LoginPage.css     #   Login page styles
│   │       ├── ChatPage.jsx      #   Chat interface
│   │       ├── AdminPanel.jsx    #   Admin dashboard
│   │       ├── AdminPanel.css    #   Admin panel styles
│   │       ├── ProductList.jsx   #   Product browsing component
│   │       └── ProductList.css   #   Product list styles
│   └── package.json              #   Frontend dependencies
│
├── data/
│   ├── chroma_db/                # ChromaDB vector database (RAG knowledge base)
│   ├── english_support_dataset.csv   # English FAQ training data
│   └── hindi_support_dataset.csv     # Hindi FAQ training data
│
├── Learnings/                    # Additional learning resources
└── Others/                       # Miscellaneous files
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| **Python** | 3.10 or higher |
| **Node.js** | 16 or higher |
| **npm** | 8 or higher |
| **Google Gemini API Key** | [Get one here](https://aistudio.google.com/apikey) |

### Step 1: Clone the Repository

```bash
git clone https://github.com/Satyjit-7x/2526_Sdp8_ChatBot.git
cd 2526_Sdp8_ChatBot
```

### Step 2: Setup Python Environment

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Then edit `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> 💡 Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey).

### Step 4: Initialize the Database

```bash
python setup_email_auth.py
```

This creates the `orders.db` SQLite database with tables for users, products, orders, and conversation history.

### Step 5: Setup Node.js Backend

```bash
cd backend
npm install
cd ..
```

### Step 6: Setup React Frontend

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Running the Application

You need **3 terminals** running simultaneously:

### Terminal 1 — Python AI Backend

```bash
python app.py
```

> ✅ Runs on `http://localhost:5001`

### Terminal 2 — Node.js Middleware

```bash
cd backend
npm start
```

> ✅ Runs on `http://localhost:3001`

### Terminal 3 — React Frontend

```bash
cd frontend
npm run dev
```

> ✅ Runs on `http://localhost:5173`

### 🌐 Open in Browser

Navigate to **http://localhost:5173** to start using the chatbot.

### Default Admin Credentials

| Field | Value |
|---|---|
| Email | `admin@admin.com` |
| Password | `admin123` |

> ⚠️ **Change the default admin password in production!**

---

## 💬 Usage Examples

### Browse Products
```
User: "Show me gaming products"
Bot:  "🛍️ Here are the Gaming products:
       1. Gaming Mouse — ₹1999
       2. Gaming Keyboard — ₹2499
       ..."
```

### Buy a Product
```
User: "I want to buy a Gaming Mouse"
Bot:  "Here are the details for Gaming Mouse (₹1999).
       Would you like to confirm the purchase?"
User: "Yes"
Bot:  "🎉 Order placed! Your order ORD456 for Gaming Mouse (₹1999) is now Pending."
```

### View Orders
```
User: "Show my orders"
Bot:  "📦 Your Orders:
       1. ORD456 — Gaming Mouse | ₹1999 | Pending"
```

### Update Order Status
```
User: "Mark ORD456 as delivered"
Bot:  "✅ Order ORD456 (Gaming Mouse) updated: Pending → Delivered"
```

### Cancel an Order
```
User: "Cancel my order"
Bot:  "✅ Order ORD456 status updated to Cancelled."
```

### Ask Questions
```
User: "What is your return policy?"
Bot:  "Our return policy allows returns within 30 days of delivery..."
```

---

## 📡 API Reference

### Authentication (Node.js — Port 3001)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and receive JWT token |
| `POST` | `/api/auth/verify` | Verify JWT token validity |

### Chat (Flask — Port 5001)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a chat message and receive AI response |
| `POST` | `/api/reset` | Reset the current chat session |

### Products (Flask — Port 5001)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products` | Get all products (optionally filter by `?category=`) |
| `GET` | `/api/products/categories` | Get all product categories |
| `GET` | `/api/products/<id>` | Get a specific product by ID |
| `GET` | `/api/products/search?q=` | Search products by name/description |
| `POST` | `/api/products` | Create a new product *(admin)* |
| `PUT` | `/api/products/<id>` | Update a product *(admin)* |

### Orders (Flask — Port 5001)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/orders` | Get orders (`?user_id=` for user-specific) |
| `PUT` | `/api/orders/<id>` | Update order status *(admin)* |
| `DELETE` | `/api/orders/<id>` | Delete an order *(admin)* |

### Admin (Flask — Port 5001)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/stats` | Dashboard statistics |
| `GET` | `/api/admin/users` | List all registered users |

---

## 🗄️ Database Schema

### `users`
| Column | Type | Description |
|---|---|---|
| `user_id` | INTEGER (PK) | Auto-increment user ID |
| `email` | TEXT (UNIQUE) | User email address |
| `password_hash` | TEXT | PBKDF2 hashed password |
| `name` | TEXT | Display name |
| `role` | TEXT | `user` or `admin` |
| `created_at` | TIMESTAMP | Account creation date |

### `products`
| Column | Type | Description |
|---|---|---|
| `product_id` | INTEGER (PK) | Auto-increment product ID |
| `name` | TEXT | Product name |
| `description` | TEXT | Product description |
| `price` | REAL | Price in ₹ (INR) |
| `category` | TEXT | Product category |
| `in_stock` | BOOLEAN | Availability status |

### `orders`
| Column | Type | Description |
|---|---|---|
| `order_id` | TEXT (PK) | Order identifier (e.g., `ORD456`) |
| `session_id` | TEXT | User session / user ID |
| `product_id` | INTEGER (FK) | Reference to product |
| `product_name` | TEXT | Product name (denormalized) |
| `price` | REAL | Order price |
| `quantity` | INTEGER | Quantity ordered |
| `order_date` | TEXT | Order placement date |
| `status` | TEXT | `Pending` / `Shipped` / `Delivered` / `Cancelled` / `Returned` |

### `conversation_history`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment ID |
| `session_id` | TEXT | User session identifier |
| `timestamp` | DATETIME | Message timestamp |
| `user_message` | TEXT | User's input message |
| `bot_response` | TEXT | Bot's generated response |
| `operation_type` | TEXT | Type of action performed |
| `affected_items` | TEXT | Items affected by the action |

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for AI features |
| `JWT_SECRET` | ❌ Optional | Secret key for JWT token signing (defaults to a placeholder — **change in production**) |
| `PORT` | ❌ Optional | Flask server port (default: `5001`) |

---

## 🐛 Troubleshooting

### Port Already in Use

**Windows (PowerShell):**
```powershell
# Find and kill process on a specific port
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

**macOS / Linux:**
```bash
lsof -i :5001 | awk 'NR==2 {print $2}' | xargs kill -9
lsof -i :3001 | awk 'NR==2 {print $2}' | xargs kill -9
lsof -i :5173 | awk 'NR==2 {print $2}' | xargs kill -9
```

### Reset Database

```bash
# Delete existing database and reinitialize
rm orders.db          # or `del orders.db` on Windows
python setup_email_auth.py
```

### Reinstall Dependencies

```bash
# Python
pip install -r requirements.txt

# Node.js backend
cd backend && npm install

# React frontend
cd frontend && npm install
```

### Common Issues

| Issue | Solution |
|---|---|
| `GEMINI_API_KEY` not working | Verify your key at [Google AI Studio](https://aistudio.google.com). Ensure `.env` file is in the project root. |
| ChromaDB collection not found | Ensure the `data/chroma_db/` directory exists and has been populated with training data. |
| `ModuleNotFoundError` | Activate your virtual environment and reinstall Python dependencies. |
| Frontend not connecting | Ensure all 3 services are running on ports 5001, 3001, and 5173. |
| Login not working | Run `python setup_email_auth.py` to initialize the users table. |
| Admin panel not showing | Login with `admin@admin.com` / `admin123`. |

---

## 👥 Team

**Project:** SDP8 — E-Commerce AI Chatbot  
**Session:** 2025–26
**Member-1** CE015 - Chudhari Prince 
**Member-2** CE020 - Chauhan Satyjit 
**Member-3** CE021 - Chovatiya Hepin 

---