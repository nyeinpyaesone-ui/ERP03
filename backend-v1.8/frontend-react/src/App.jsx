import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CRM from './pages/CRM';
import HR from './pages/HR';
import Inventory from './pages/Inventory';
import Finance from './pages/Finance';
import Projects from './pages/Projects';
import Reports from './pages/Reports';
import Analytics from './pages/Analytics';
import AIChat from './pages/AIChat';
import Documents from './pages/Documents';
import Workflows from './pages/Workflows';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';
import BulkImportExport from './pages/BulkImportExport';
import MigrationManager from './pages/MigrationManager';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const handleStorage = () => {
      setToken(localStorage.getItem('token'));
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  if (!token) {
    return <Login onLogin={(t) => { localStorage.setItem('token', t); setToken(t); }} />;
  }

  return (
    <Layout onLogout={() => { localStorage.removeItem('token'); setToken(null); }}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/crm" element={<CRM />} />
        <Route path="/hr" element={<HR />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/finance" element={<Finance />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/ai-chat" element={<AIChat />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/bulk-import" element={<BulkImportExport />} />
        <Route path="/migrations" element={<MigrationManager />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;

