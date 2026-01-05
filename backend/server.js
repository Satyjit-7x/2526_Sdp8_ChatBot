const express = require('express');
const cors = require('cors');
const chatRoutes = require('./routes/chat');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Keep this backend as a thin controller; actual chat decision logic lives in routes/chat.js
app.use('/api/chat', chatRoutes);

// Ensures unhandled paths are clearly signaled for frontend testing
app.use((req, res) => res.status(404).json({ error: 'Endpoint not found' }));

app.listen(PORT, () => {
  console.log(`Chat controller listening at http://localhost:${PORT}`);
});
