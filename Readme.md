# Multilingual E-Commerce Chatbot

A vector-based chatbot capable of understanding English and Hindi queries using semantic search (ChromaDB + SentenceTransformers).

## 🚀 Setup Guide

Follow these steps to set up the project on your machine.

### 1. Clone the Repository
```bash
git clone <repository_url>
cd 2526_sdp8_chatbot
```

### 2. Install Dependencies
Make sure you have Python installed. Then run:
```bash
pip install -r requirements.txt
```

### 3. Get the Data
If you don't have the CSV files in the `data/` folder, run:
```bash
python3 download_dataset.py
```
*This downloads the required dataset from Kaggle.*

### 4. Configure Database (Important! ⚠️)
Before running the bot, you **must** generate the vector database. This script reads the CSV data, creates embeddings, and saves them to `data/chroma_db`.

**Run this command:**
```bash
python3 vectorize_data.py
```
*You only need to run this once, or whenever you update the datasets in `data/`.*

### 5. Run the Chatbot (ML Console Bot)
Now you can start the original console bot (Python + ChromaDB):
```bash
python3 smart_chatbot.py
```

## 🧩 Web Chatbot (Controller + UI)

In addition to the ML console bot above, this repository also contains a **thin Node.js controller** and a **React frontend** for an e‑commerce customer support experience.

> The ML, RAG, and vector DB logic are still handled by a separate Python service. The Node.js backend only acts as a controller and proxy.

---

### 6. Backend (Node.js + Express) Setup

**Requirements**

- Node.js (LTS recommended, e.g., 18+)
- npm (comes with Node.js)

**Install dependencies**

From the project root:

```bash
cd backend
npm install
```

**Configuration**

- The backend exposes a chat controller at: `http://localhost:3001/api/chat`.
- For non‑order questions, it forwards to your friend’s AI service:

  ```text
  POST http://localhost:8000/ai/chat
  Body: { "question": "..." }
  ```

- You can override that URL with an environment variable:

  ```bash
  # optional, only if AI service is not at localhost:8000
  set AI_SERVICE_URL=http://localhost:8000/ai/chat       # Windows (PowerShell/CMD)
  export AI_SERVICE_URL=http://localhost:8000/ai/chat    # Linux/macOS
  ```

**Run the backend**

From `backend/`:

```bash
npm start
```

You should see a message similar to:

```text
Chat controller listening at http://localhost:3001
```

At this point, you have:

- `POST /api/chat` for the web UI.
- Simple dummy logic for:
  - Order list / order history
  - Last order date
- All other intents are proxied to the AI service.

---

### 7. Frontend (React + Vite) Setup

**Requirements**

- Node.js (same as backend)

**Install dependencies**

From the project root:

```bash
cd frontend
npm install
```

**Configuration**

- By default, the frontend sends chat requests to:

  ```text
  http://localhost:3001/api/chat
  ```

- You can override this with a Vite env variable in `frontend/.env`:

  ```bash
  VITE_CHAT_API_URL=http://localhost:3001/api/chat
  ```

  (If `.env` does not exist, create it in the `frontend/` folder.)

**Run the frontend**

From `frontend/`:

```bash
npm run dev
```

Vite will print a local URL, for example:

```text
  Local:   http://localhost:5173/
```

Open that URL in your browser to use the web chat UI.

---

### 8. End‑to‑End Flow (For Teammates)

1. **Clone the repository** (from the top of this README).
2. **Set up the ML pipeline** (Python, datasets, vector DB) using steps 2–5 above.
3. **Start the AI service** your ML teammate provides (it must expose `POST /ai/chat`).
4. **Start the Node.js backend**:

   ```bash
   cd backend
   npm install        # first time only
   npm start
   ```

5. **Start the React frontend** in a second terminal:

   ```bash
   cd frontend
   npm install        # first time only
   npm run dev
   ```

6. Open the URL shown by Vite (e.g., `http://localhost:5173/`) to chat with the bot.

The responsibilities are clearly separated:

- **Python side**: ML, embeddings, ChromaDB/RAG, intent understanding, answer generation.
- **Node.js backend**: Thin controller using dummy order data for simple queries, forwarding all other queries to the AI service.
- **React frontend**: Simple chat UI and a dummy view of the user’s orders for demo/testing.



=============================================TO RUN THE PROJECT=============================================

cd 2526_sdp8_chatbot/2526_sdp8_chatbot  ============BOT

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python vectorize_data.py
PORT=5001 python app.py


 
cd 2526_sdp8_chatbot/2526_sdp8_chatbot/backend           ============BACKEND

npm install
AI_SERVICE_URL=http://localhost:5001/api/chat npm start



cd 2526_sdp8_chatbot/2526_sdp8_chatbot/frontend         ============FRONTEND

npm install
VITE_CHAT_API_URL=http://localhost:3001/api/chat npm run dev



