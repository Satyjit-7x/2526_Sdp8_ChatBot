import { useEffect, useMemo, useState } from 'react';
import '../App.css';

const dummyOrders = [
  { orderId: 'ORD001', product: 'Mobile', date: '2023-10-03', status: 'Delivered' },
  { orderId: 'ORD002', product: 'Headphones', date: '2023-09-15', status: 'Shipped' },
  { orderId: 'ORD003', product: 'Wireless Charger', date: '2023-08-21', status: 'Returned' },
  { orderId: 'ORD004', product: 'Smartwatch', date: '2023-07-02', status: 'Delivered' },
];

const apiUrl =
  import.meta.env.VITE_CHAT_API_URL || 'http://localhost:3001/api/chat';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'Hi there! Ask me about your orders or anything else.' },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);

  // SAME logic: only formatting data
  const orderSummary = useMemo(() => {
    return dummyOrders
      .map(
        (order) =>
          `${order.orderId} • ${order.product} (${order.date}, ${order.status})`
      )
      .join(' | ');
  }, []);

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
        body: JSON.stringify({ message: userMessage.text }),
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
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'Unable to reach the chat service. Please try again later.',
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
