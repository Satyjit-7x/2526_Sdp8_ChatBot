import { useState } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import ChatPage from './components/ChatPage';
import AdminPanel from './components/AdminPanel';

function AppContent() {
  const { isAuthenticated, loading, login, isAdmin } = useAuth();
  const [showChat, setShowChat] = useState(false);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={(user, token) => login(user, token)} />;
  }

  // Admin gets toggle between admin panel and chat
  if (isAdmin && !showChat) {
    return (
      <div className="root-app">
        <AdminPanel onSwitchToChat={() => setShowChat(true)} />
      </div>
    );
  }

  return (
    <div className="root-app">
      <ChatPage onSwitchToAdmin={isAdmin ? () => setShowChat(false) : null} />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
