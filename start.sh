#!/bin/bash
# Quick Start Script for Chatbot

echo "================================"
echo "🚀 CHATBOT QUICK START"
echo "================================"
echo ""

PROJECT_ROOT="/Users/ravirajsinhpadhiyar/Documents/GitHub/2526_sdp8_chatbot/2526_sdp8_chatbot"

# Step 1: Setup Database
echo "Step 1️⃣ : Setting up database with products..."
cd "$PROJECT_ROOT"
python setup_email_auth.py

if [ $? -ne 0 ]; then
    echo "❌ Database setup failed!"
    exit 1
fi

echo ""
echo "Step 2️⃣ : Starting Flask backend..."
echo "Running: python app.py"
echo "You'll see logs below. Flask is ready when you see: 'Running on http://127.0.0.1:5001'"
echo ""
echo "NEXT STEPS:"
echo "1. In another terminal, run: cd $PROJECT_ROOT/backend && npm start"
echo "2. In a third terminal, run:  cd $PROJECT_ROOT/frontend && npm run dev"
echo "3. Open http://localhost:5173 in your browser"
echo "4. Try: 'I want to buy Titan Wallet'"
echo ""
echo "Press Enter to start Flask..."
read

python app.py
