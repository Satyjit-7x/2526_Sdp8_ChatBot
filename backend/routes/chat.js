const express = require('express');
const fetch = require('node-fetch');

const router = express.Router();

const orders = [
  { orderId: 'ORD001', product: 'Mobile', date: '2023-10-03', status: 'Delivered' },
  { orderId: 'ORD002', product: 'Headphones', date: '2023-09-15', status: 'Shipped' },
  { orderId: 'ORD003', product: 'Wireless Charger', date: '2023-08-21', status: 'Returned' },
  { orderId: 'ORD004', product: 'Smartwatch', date: '2023-07-02', status: 'Delivered' },
];

const AI_URL =
  process.env.AI_SERVICE_URL || 'http://localhost:8000/ai/chat';

// Simple keyword checks
function isOrderList(text) {
  return /order list|my orders|order history/i.test(text);
}

function isLastOrderDate(text) {
  return /(last|latest) order.*date/i.test(text);
}

router.post('/', async (req, res) => {
  const message = req.body?.message;

  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Message is required' });
  }

  // Handle basic order queries locally
  if (isOrderList(message)) {
    const list = orders
      .map((o) => `${o.orderId} (${o.product}) on ${o.date}`)
      .join(', ');

    return res.json({
      reply: `You have ${orders.length} orders: ${list}`,
    });
  }

  if (isLastOrderDate(message)) {
    const lastOrder = orders[0];
    return res.json({
      reply: `Your last order was placed on ${lastOrder.date}.`,
    });
  }

  // Forward other questions to AI service
  try {
    const aiRes = await fetch(AI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: message }),
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
