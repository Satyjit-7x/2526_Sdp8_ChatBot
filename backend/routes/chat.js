const express = require('express');
const jwt = require('jsonwebtoken');
const fetch = globalThis.fetch || ((...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args)));

const router = express.Router();
const SECRET_KEY = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

const AI_URL =
  process.env.AI_SERVICE_URL || 'http://localhost:5001/api/chat';

router.post('/', async (req, res) => {
  const message = req.body?.message;
  const user_id = req.body?.user_id;

  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Message is required' });
  }

  // Extract user_id from JWT token if not provided in body
  let sessionUserId = user_id || 'default';
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (token) {
      const decoded = jwt.verify(token, SECRET_KEY);
      sessionUserId = decoded.user_id || sessionUserId;
    }
  } catch (e) {
    // Token verification failed, use default or provided user_id
  }

  // Extract role from JWT or request body
  let userRole = req.body?.role || 'user';
  try {
    const authToken = req.headers.authorization?.split(' ')[1];
    if (authToken) {
      const decodedToken = jwt.verify(authToken, SECRET_KEY);
      userRole = decodedToken.role || userRole;
    }
  } catch (e) {
    // Token verification failed, use provided role
  }

  // Forward to Flask AI service with user_id and role for session tracking
  try {
    const aiRes = await fetch(AI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        user_id: sessionUserId,
        role: userRole
      }),
    });

    if (!aiRes.ok) {
      return res.status(502).json({ error: 'AI service failed' });
    }

    const aiData = await aiRes.json();

    return res.json({
      reply: aiData.reply || aiData.answer || 'No response from AI',
    });
  } catch (err) {
    return res.status(502).json({
      error: 'Could not connect to AI service',
    });
  }
});

module.exports = router;
