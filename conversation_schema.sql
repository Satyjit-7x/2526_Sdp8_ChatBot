-- Conversation History Table Schema
-- This table stores the conversation history to enable context-aware responses

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    sql_executed TEXT,
    operation_type TEXT,
    affected_items TEXT
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_session_timestamp 
ON conversation_history(session_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_session_id 
ON conversation_history(session_id);
