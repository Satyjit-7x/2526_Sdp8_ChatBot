const express = require('express');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const path = require('path');
const Database = require('better-sqlite3');

const router = express.Router();
const SECRET_KEY = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

// Database path — same orders.db used by the Flask bot engine
const DB_PATH = path.join(__dirname, '../../orders.db');

// ---------- password helpers ----------

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256').toString('hex');
  return `${salt}$${hash}`;
}

function verifyPassword(password, storedHash) {
  try {
    const [salt, hash] = storedHash.split('$');
    const newHash = crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256').toString('hex');
    return newHash === hash;
  } catch {
    return false;
  }
}

// ---------- ensure users table exists ----------

function ensureUsersTable() {
  const db = new Database(DB_PATH);
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      user_id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      name TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
  db.close();
}

// Run once on startup
ensureUsersTable();

// ---------- routes ----------

// POST /api/auth/register
router.post('/register', (req, res) => {
  try {
    const { email, password, name } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }

    const db = new Database(DB_PATH);

    // Check if email already exists
    const existing = db.prepare('SELECT user_id FROM users WHERE email = ?').get(email);
    if (existing) {
      db.close();
      return res.status(400).json({ error: 'Email already registered' });
    }

    const passwordHash = hashPassword(password);
    const displayName = name || email.split('@')[0];

    const result = db.prepare(
      'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)'
    ).run(email, passwordHash, displayName);

    db.close();

    const userId = result.lastInsertRowid;

    // Create JWT
    const token = jwt.sign(
      { user_id: userId, email },
      SECRET_KEY,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token,
      user: { user_id: userId, email, name: displayName }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Registration failed: ' + error.message });
  }
});

// POST /api/auth/login
router.post('/login', (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const db = new Database(DB_PATH);
    const user = db.prepare(
      'SELECT user_id, email, name, password_hash FROM users WHERE email = ?'
    ).get(email);
    db.close();

    if (!user) {
      return res.status(401).json({ error: 'Email not found' });
    }

    if (!verifyPassword(password, user.password_hash)) {
      return res.status(401).json({ error: 'Incorrect password' });
    }

    // Create JWT
    const token = jwt.sign(
      { user_id: user.user_id, email: user.email },
      SECRET_KEY,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token,
      user: { user_id: user.user_id, email: user.email, name: user.name }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Login failed: ' + error.message });
  }
});

// POST /api/auth/verify
router.post('/verify', (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];

    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const decoded = jwt.verify(token, SECRET_KEY);
    res.json({
      success: true,
      user: { user_id: decoded.user_id, email: decoded.email }
    });
  } catch {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
});

module.exports = router;
