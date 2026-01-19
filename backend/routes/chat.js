const express = require('express');
const fetch = globalThis.fetch || ((...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args)));

const router = express.Router();

const orders = [
  { orderId: 'ORD001', product: 'Mobile', date: '2023-10-03', status: 'Delivered' },
  { orderId: 'ORD002', product: 'Headphones', date: '2023-09-15', status: 'Shipped' },
  { orderId: 'ORD003', product: 'Wireless Charger', date: '2023-08-21', status: 'Returned' },
  { orderId: 'ORD004', product: 'Smartwatch', date: '2023-07-02', status: 'Delivered' },
];

const AI_URL =
  process.env.AI_SERVICE_URL || 'http://localhost:5001/api/chat';

router.post('/', async (req, res) => {
  const message = req.body?.message;

  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Message is required' });
  }

  // Forward questions to AI service with orders context
  try {
    const aiRes = await fetch(AI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        orders: orders // <--- Pass orders as context
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
