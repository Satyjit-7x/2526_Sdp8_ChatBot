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

### 5. Run the Chatbot
Now you can start the bot:
```bash
python3 smart_chatbot.py
```

## 🏗️ Project Structure
- `data/`: Contains CSV datasets and the generated `chroma_db`.
- `vectorize_data.py`: Script to ingest data and build the database.
- `smart_chatbot.py`: Main entry point for the chatbot.
- `bot_engine.py`: Core logic handling vector search.
