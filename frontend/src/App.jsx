import { useState, useEffect } from 'react';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import Sales from './components/Sales.jsx';
import Inventory from './components/Inventory.jsx';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('erp03_token'));
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState('dashboard');

  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('erp03_token');
          setToken(null);
        });
    }
  }, [token]);

  if (!token) {
    return (
      <Login
        onLogin={(t, u) => {
          localStorage.setItem('erp03_token', t);
          setToken(t);
          setUser(u);
        }}
      />
    );
  }

  return (
    <div className="erp-layout">
      <nav className="sidebar">
        <h2>ERP03</h2>
        <button onClick={() => setActiveView('dashboard')}>Dashboard</button>
        <button onClick={() => setActiveView('sales')}>Sales</button>
        <button onClick={() => setActiveView('inventory')}>Inventory</button>
        <button
          onClick={() => {
            localStorage.removeItem('erp03_token');
            setToken(null);
            setUser(null);
          }}
        >
          Logout
        </button>
      </nav>
      <main className="content">
        {activeView === 'dashboard' && <Dashboard user={user} />}
        {activeView === 'sales' && <Sales token={token} />}
        {activeView === 'inventory' && <Inventory token={token} />}
      </main>
    </div>
  );
}
