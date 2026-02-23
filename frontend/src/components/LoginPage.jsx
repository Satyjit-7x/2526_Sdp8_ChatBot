import React, { useState } from 'react';
import './LoginPage.css';

function LoginPage({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:3001/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      // Pass both user and token to the auth context
      onLoginSuccess(data.user, data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:3001/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          name: formData.name || formData.email.split('@')[0]
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      // Pass both user and token to the auth context
      onLoginSuccess(data.user, data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="login-container">
      {/* Left Side - Branding */}
      <div className="login-left">
        <div className="login-brand">
          <div className="brand-icon">🤖</div>
          <h1>AI Chatbot</h1>
          <p className="brand-tagline">Smart e-commerce companion</p>
        </div>

        <div className="brand-features">
          <div className="feature-item">
            <span className="feature-icon">✨</span>
            <span>AI-Powered Chat</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🛍️</span>
            <span>Browse 69+ Products</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📦</span>
            <span>Manage Orders</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔐</span>
            <span>Secure Login</span>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="login-right">
        <div className="login-box">
          <div className="login-form">
            <h2 className="login-title">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="login-subtitle">
              {isLogin
                ? 'Sign in with your email to continue'
                : 'Create a new account to get started'}
            </p>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={isLogin ? handleLogin : handleRegister}>
              {!isLogin && (
                <div className="form-group">
                  <label htmlFor="name">Full Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="John Doe"
                    disabled={loading}
                  />
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="you@example.com"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  required
                  minLength="6"
                  disabled={loading}
                />
                {!isLogin && (
                  <small className="password-hint">Minimum 6 characters</small>
                )}
              </div>

              <button
                type="submit"
                className="login-button"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-small"></span>
                    {isLogin ? 'Signing in...' : 'Creating account...'}
                  </>
                ) : (
                  isLogin ? 'Sign In' : 'Create Account'
                )}
              </button>
            </form>

            <div className="divider"></div>

            <div className="toggle-auth">
              <p>
                {isLogin ? "Don't have an account? " : 'Already have an account? '}
                <button
                  type="button"
                  className="toggle-button"
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError('');
                    setFormData({ email: '', password: '', name: '' });
                  }}
                  disabled={loading}
                >
                  {isLogin ? 'Sign Up' : 'Sign In'}
                </button>
              </p>
            </div>

            <div className="features-section">
              <h3>What you can do</h3>
              <ul className="features-list">
                <li>✅ Browse 69+ products across 10 categories</li>
                <li>✅ Create, update, and delete orders</li>
                <li>✅ Chat with AI-powered Gemini</li>
                <li>✅ View your personalized order history</li>
                <li>✅ Secure email authentication</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="login-footer">
          <p>© 2026 AI Chatbot. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
