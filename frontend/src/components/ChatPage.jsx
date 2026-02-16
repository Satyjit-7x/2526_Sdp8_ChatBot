import { useEffect, useMemo, useState } from 'react';
import '../App.css';

const apiUrl =
  import.meta.env.VITE_CHAT_API_URL || 'http://localhost:3001/api/chat';
const ordersApiUrl = 'http://localhost:5001/api/orders';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'Hi there! Ask me about your orders or anything else.' },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [orders, setOrders] = useState([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);

  // Fetch orders from database
  const fetchOrders = async () => {
    try {
      const response = await fetch(ordersApiUrl);
      const data = await response.json();
      if (data.orders) {
        setOrders(data.orders);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
      setOrders([]);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  // Fetch orders on mount
  useEffect(() => {
    fetchOrders();
  }, []);

  // Dynamic order summary
  const orderSummary = useMemo(() => {
    if (orders.length === 0) {
      return 'No orders found';
    }
    return orders
      .map(
        (order) =>
          `${order.orderId} • ${order.product} (${order.date}, ${order.status})`
      )
      .join(' | ');
  }, [orders]);

  // useEffect kept but does NOT change behavior
  useEffect(() => {
    // reserved for future side-effects (analytics, logging, etc.)
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsSending(true);

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputValue.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const payload = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: payload.reply || 'I am still thinking...',
        },
      ]);

      // Refresh orders list after bot response (shows deleted/added/updated orders)
      fetchOrders();

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'Oops! Bad network or server issue.',
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div>
          <h1>Customer Support</h1>
          <p>Only one test user; backend maintains the same order list.</p>
        </div>

        <div className="order-summary">
          <p className="summary-label">Current Orders</p>
          <p>{orderSummary}</p>
        </div>
      </header>

      <section className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            <span className="sender">
              {msg.sender === 'user' ? 'You' : 'Bot'}
            </span>
            <p>{msg.text}</p>
          </div>
        ))}

        {isSending && (
          <div className="message bot">
            <span className="sender">Bot</span>
            <p>Typing...</p>
          </div>
        )}
      </section>

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask about your orders, refunds, shipping..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isSending}
        />
        <button type="submit" disabled={isSending}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatPage;
