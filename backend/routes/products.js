const express = require('express');
const router = express.Router();
const fetch = globalThis.fetch || ((...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args)));

const PYTHON_AI_URL = process.env.AI_SERVICE_URL || 'http://localhost:5001/api/chat';

// GET /api/products - Fetch all products or filter by category
router.get('/', async (req, res) => {
  try {
    const category = req.query.category;

    // Proxy to Python Flask backend for products
    const pythonRes = await fetch(`${PYTHON_AI_URL.replace('/api/chat', '')}/products${category ? `?category=${category}` : ''}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!pythonRes.ok) {
      return res.status(502).json({ products: [], error: 'Product service unavailable' });
    }

    const data = await pythonRes.json();
    res.json(data);
  } catch (err) {
    console.error('Error fetching products:', err);
    res.status(500).json({ products: [], error: 'Could not fetch products' });
  }
});

// GET /api/products/categories - Get all categories
router.get('/categories', async (req, res) => {
  try {
    const pythonRes = await fetch(`${PYTHON_AI_URL.replace('/api/chat', '')}/products/categories`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!pythonRes.ok) {
      return res.status(502).json({ categories: [], error: 'Product service unavailable' });
    }

    const data = await pythonRes.json();
    res.json(data);
  } catch (err) {
    console.error('Error fetching categories:', err);
    res.status(500).json({ categories: [], error: 'Could not fetch categories' });
  }
});

// GET /api/products/:id - Get product by ID
router.get('/:id', async (req, res) => {
  try {
    const productId = req.params.id;

    const pythonRes = await fetch(`${PYTHON_AI_URL.replace('/api/chat', '')}/products/${productId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!pythonRes.ok) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const data = await pythonRes.json();
    res.json(data);
  } catch (err) {
    console.error('Error fetching product:', err);
    res.status(500).json({ error: 'Could not fetch product' });
  }
});

// POST /api/products - Create a new product (admin)
router.post('/', async (req, res) => {
  try {
    const pythonRes = await fetch(`${PYTHON_AI_URL.replace('/api/chat', '')}/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });

    const data = await pythonRes.json();
    res.status(pythonRes.status).json(data);
  } catch (err) {
    console.error('Error creating product:', err);
    res.status(500).json({ error: 'Could not create product' });
  }
});

// PUT /api/products/:id - Update a product (admin)
router.put('/:id', async (req, res) => {
  try {
    const productId = req.params.id;
    const pythonRes = await fetch(`${PYTHON_AI_URL.replace('/api/chat', '')}/products/${productId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });

    const data = await pythonRes.json();
    res.status(pythonRes.status).json(data);
  } catch (err) {
    console.error('Error updating product:', err);
    res.status(500).json({ error: 'Could not update product' });
  }
});

module.exports = router;
