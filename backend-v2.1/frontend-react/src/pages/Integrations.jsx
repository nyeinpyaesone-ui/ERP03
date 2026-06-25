import React, { useState, useEffect } from 'react';
import { Plug, Webhook, Plus, Trash2, Send, CheckCircle, Slack, MessageCircle, Zap } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [activeTab, setActiveTab] = useState('integrations');
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/integrations/integrations`, axiosConfig).then(r => setIntegrations(r.data));
    axios.get(`${API_URL}/api/v1/integrations/webhooks`, axiosConfig).then(r => setWebhooks(r.data));
  }, []);

  const testWebhook = async (id) => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/integrations/webhooks/${id}/test`, {}, axiosConfig);
      alert(`Webhook test: ${res.data.status}`);
    } catch (e) { alert('Test failed'); }
  };

  const getProviderIcon = (provider) => {
    if (provider === 'slack') return <Slack className="w-5 h-5" />;
    if (provider === 'teams') return <MessageCircle className="w-5 h-5" />;
    if (provider === 'zapier') return <Zap className="w-5 h-5" />;
    return <Plug className="w-5 h-5" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
        <Plug className="w-8 h-8 text-indigo-600" /> Integrations
      </h1>

      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[{id:'integrations',label:'Services',icon:Plug},{id:'webhooks',label:'Webhooks',icon:Webhook}].map(t => (
          <button key={t.id} onClick={()=>setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${activeTab===t.id?'bg-white text-indigo-600 shadow-sm':'text-gray-600'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {activeTab === 'integrations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {integrations.map(i => (
            <div key={i.id} className="card p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600">
                  {getProviderIcon(i.provider)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{i.name}</h3>
                  <p className="text-xs text-gray-500 capitalize">{i.provider}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${i.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                  {i.is_active ? 'Connected' : 'Disconnected'}
                </span>
                {i.last_sync && <p className="text-xs text-gray-400">Last sync: {new Date(i.last_sync).toLocaleDateString()}</p>}
              </div>
            </div>
          ))}
          {integrations.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              <Plug className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No integrations configured yet.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'webhooks' && (
        <div className="space-y-4">
          {webhooks.map(w => (
            <div key={w.id} className="card p-5">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Webhook className="w-5 h-5 text-indigo-600" />
                    <h3 className="font-semibold text-gray-900">{w.name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${w.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                      {w.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 font-mono mt-1 truncate">{w.url}</p>
                  <div className="flex gap-2 mt-2">
                    {w.events?.map((evt, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">{evt}</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => testWebhook(w.id)} className="p-2 hover:bg-gray-100 rounded-lg text-indigo-600">
                    <Send className="w-4 h-4" />
                  </button>
                  <button className="p-2 hover:bg-red-50 text-red-500 rounded-lg">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

