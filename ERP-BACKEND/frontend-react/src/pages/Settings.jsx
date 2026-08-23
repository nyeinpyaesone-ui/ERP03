import React, { useState, useEffect } from 'react';
import { Settings, Save, Key, Mail, Database, CreditCard, Shield, Bell, Globe, Trash2 } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function SettingsPage() {
  const [settings, setSettings] = useState([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newCategory, setNewCategory] = useState('general');
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/admin/settings`, axiosConfig);
      setSettings(res.data);
    } catch (e) { console.error(e); }
  };

  const addSetting = async () => {
    if (!newKey || !newValue) return;
    try {
      await axios.post(`${API_URL}/api/v1/admin/settings`, {
        key: newKey,
        value: newValue,
        category: newCategory
      }, axiosConfig);
      setNewKey(''); setNewValue(''); setNewCategory('general');
      fetchSettings();
    } catch (e) { console.error(e); }
  };

  const deleteSetting = async (key) => {
    if (!confirm(`Delete setting "${key}"?`)) return;
    try {
      await axios.delete(`${API_URL}/api/v1/admin/settings/${key}`, axiosConfig);
      fetchSettings();
    } catch (e) { console.error(e); }
  };

  const categories = ['general', 'email', 'stripe', 'ai', 'security', 'notifications'];

  const getCategoryIcon = (cat) => {
    if (cat === 'email') return <Mail className="w-4 h-4" />;
    if (cat === 'stripe') return <CreditCard className="w-4 h-4" />;
    if (cat === 'security') return <Shield className="w-4 h-4" />;
    if (cat === 'notifications') return <Bell className="w-4 h-4" />;
    if (cat === 'ai') return <Key className="w-4 h-4" />;
    return <Settings className="w-4 h-4" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
        <Settings className="w-8 h-8 text-indigo-600" /> Settings
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Add New Setting</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input type="text" value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="Key (e.g., app.name)" className="input-field" />
              <input type="text" value={newValue} onChange={e => setNewValue(e.target.value)} placeholder="Value" className="input-field" />
              <select value={newCategory} onChange={e => setNewCategory(e.target.value)} className="input-field">
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <button onClick={addSetting} className="mt-3 btn-primary flex items-center gap-2">
              <Save className="w-4 h-4" /> Save Setting
            </button>
          </div>

          <div className="card overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50"><tr>
                <th className="px-4 py-3 text-left font-medium">Key</th>
                <th className="px-4 py-3 text-left font-medium">Value</th>
                <th className="px-4 py-3 text-left font-medium">Category</th>
                <th className="px-4 py-3 text-left font-medium"></th>
              </tr></thead>
              <tbody className="divide-y">
                {settings.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-indigo-600">{s.key}</td>
                    <td className="px-4 py-3 text-gray-600">{s.value}</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 w-fit">
                        {getCategoryIcon(s.category)} {s.category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteSetting(s.key)} className="p-1.5 text-red-500 hover:bg-red-50 rounded">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" /> System Info
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Version</span><span className="font-medium">v1.8.0</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Environment</span><span className="font-medium">Production</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Database</span><span className="font-medium">PostgreSQL</span></div>
            </div>
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-600" /> Security
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">2FA Required</span>
                <button className="relative inline-flex h-5 w-9 items-center rounded-full bg-gray-200">
                  <span className="inline-block h-3 w-3 transform rounded-full bg-white translate-x-1" />
                </button>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Rate Limiting</span>
                <button className="relative inline-flex h-5 w-9 items-center rounded-full bg-indigo-600">
                  <span className="inline-block h-3 w-3 transform rounded-full bg-white translate-x-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

