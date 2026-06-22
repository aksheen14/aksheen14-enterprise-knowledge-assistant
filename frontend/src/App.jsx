import { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('login');

  const handleLogin = (userData) => {
    setUser(userData);
    setPage('dashboard');
  };

  const handleNavigate = (pageName) => {
    setPage(pageName);
  };

  if (!user && page !== 'login') {
    setPage('login');
  }

  return (
    <div className="app-shell">
      {page === 'login' && <Login onLogin={handleLogin} />}
      {page === 'dashboard' && <Dashboard onNavigate={handleNavigate} />}
      {page === 'chat' && <Chat />}
    </div>
  );
}
