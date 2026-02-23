const express = require('express');
const cors = require('cors');
const chatRoutes = require('./routes/chat');
const productRoutes = require('./routes/products');
const emailAuthRoutes = require('./routes/email-auth');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Authentication routes
app.use('/api/auth', emailAuthRoutes);

// Keep this backend as a thin controller; actual chat decision logic lives in routes/
app.use('/api/chat', chatRoutes);
app.use('/api/products', productRoutes);

// Ensures unhandled paths are clearly signaled for frontend testing
app.use((req, res) => res.status(404).json({ error: 'Endpoint not found' }));

app.listen(PORT, () => {
  console.log(`Chat controller & product API listening at http://localhost:${PORT}`);
});
