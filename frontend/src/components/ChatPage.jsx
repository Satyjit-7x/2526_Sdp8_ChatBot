import { useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import ProductList from './ProductList';
import '../App.css';

const chatApiUrl = 'http://localhost:3001/api/chat';
const ordersApiUrl = 'http://localhost:5001/api/orders';

const ChatPage = ({ onSwitchToAdmin }) => {
  const { user, token, logout } = useAuth();
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: `Hi ${user?.name || 'there'}! 👋 I can help you browse products, manage orders, and more. Ask me anything!` },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [orders, setOrders] = useState([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [showOrders, setShowOrders] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch orders from database
  const fetchOrders = async () => {
    try {
      const userId = user?.user_id || '';
      const url = userId ? `${ordersApiUrl}?user_id=${userId}` : ordersApiUrl;
      const response = await fetch(url);
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

  // Order count summary
  const orderCountText = useMemo(() => {
    if (isLoadingOrders) return 'Loading orders...';
    if (orders.length === 0) return 'No orders yet';
    return `${orders.length} order${orders.length > 1 ? 's' : ''}`;
  }, [orders, isLoadingOrders]);

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
      const response = await fetch(chatApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: inputValue.trim(),
          user_id: user?.user_id || 'default',
          role: user?.role || 'user',
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

      // Refresh orders list after bot response (may have created/deleted/updated)
      fetchOrders();

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'Oops! Could not connect to the server. Make sure both backends are running.',
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

  const clearChat = () => {
    setMessages([
      { id: Date.now(), sender: 'bot', text: `Chat cleared! How can I help you, ${user?.name || 'there'}?` },
    ]);
  };

  // Format message text with line breaks
  const formatMessageText = (text) => {
    if (!text) return '';
    return text.split('\n').map((line, i) => (
      <span key={i}>
        {line}
        {i < text.split('\n').length - 1 && <br />}
      </span>
    ));
  };

  return (
    <div className="app-layout">
      <ProductList />
      <div className="chat-container">
        {/* Header */}
        <header className="chat-header">
          <div className="header-left">
            <h1>🤖 AI Chatbot</h1>
            <button
              className="order-badge"
              onClick={() => setShowOrders(!showOrders)}
              title="Click to toggle order details"
            >
              📦 {orderCountText}
            </button>
          </div>
          <div className="header-right">
            <button className="clear-chat-btn" onClick={clearChat}>🗑️ Clear</button>
            {onSwitchToAdmin && (
              <button className="clear-chat-btn" onClick={onSwitchToAdmin} style={{ background: 'rgba(99,102,241,0.25)', borderColor: 'rgba(99,102,241,0.5)' }}>⚙️ Admin</button>
            )}
            <div className="user-info">
              <span className="user-name">{user?.name || 'Guest'}</span>
              <button className="logout-btn" onClick={logout}>Logout</button>
            </div>
          </div>
        </header>

        {/* Order Panel (toggleable) */}
        {showOrders && (
          <div className="order-panel">
            {isLoadingOrders ? (
              <p>Loading orders...</p>
            ) : orders.length === 0 ? (
              <p>No orders found. Try "create order for gaming mouse" in the chat!</p>
            ) : (
              <div className="order-list">
                {orders.map((order) => (
                  <div key={order.orderId} className="order-card">
                    <div className="order-card-header">
                      <span className="order-id">{order.orderId}</span>
                      <span className={`order-status status-${(order.status || '').toLowerCase()}`}>
                        {order.status}
                      </span>
                    </div>
                    <div className="order-card-body">
                      <span className="order-product">{order.productName}</span>
                      <span className="order-price">₹{order.price?.toLocaleString('en-IN') || '0'}</span>
                    </div>
                    <div className="order-card-footer">
                      <span className="order-date">{order.orderDate}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        <section className="messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.sender}`}>
              <span className="sender">
                {msg.sender === 'user' ? '👤 You' : '🤖 Bot'}
              </span>
              <div className="message-text">{formatMessageText(msg.text)}</div>
            </div>
          ))}
          {isSending && (
            <div className="message bot">
              <span className="sender">🤖 Bot</span>
              <div className="message-text typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </section>

        {/* Input */}
        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask about products, orders, or anything..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isSending}
          />
          <button type="submit" disabled={isSending || !inputValue.trim()} className="send-btn">
            {isSending ? '⏳' : '📩 Send'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPage;
