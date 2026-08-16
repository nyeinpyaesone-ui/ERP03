import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Building2, DollarSign, Plus, Search, Filter, Phone, Mail } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CRM() {
  const [activeTab, setActiveTab] = useState('contacts');
  const [contacts, setContacts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [deals, setDeals] = useState([]);
  const [pipeline, setPipeline] = useState({});
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => { fetchData(); }, [activeTab]);
  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'contacts') {
        const res = await axios.get(`${API_URL}/api/v1/crm/contacts`, axiosConfig);
        setContacts(res.data);
      } else if (activeTab === 'companies') {
        const res = await axios.get(`${API_URL}/api/v1/crm/companies`, axiosConfig);
        setCompanies(res.data);
      } else if (activeTab === 'deals') {
        const res = await axios.get(`${API_URL}/api/v1/crm/deals`, axiosConfig);
        setDeals(res.data);
      } else if (activeTab === 'pipeline') {
        const res = await axios.get(`${API_URL}/api/v1/crm/deals/pipeline`, axiosConfig);
        setPipeline(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const tabs = [
    { id: 'contacts', label: 'Contacts', icon: Users },
    { id: 'companies', label: 'Companies', icon: Building2 },
    { id: 'deals', label: 'Deals', icon: DollarSign },
    { id: 'pipeline', label: 'Pipeline', icon: Filter },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">CRM</h1>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> New</button>
      </div>
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${activeTab === t.id ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-600'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>
      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> : (
        <>
          {activeTab === 'contacts' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {contacts.map(c => (
                <div key={c.id} className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{c.first_name} {c.last_name}</h3>
                      <p className="text-sm text-gray-500">{c.title}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.status === 'customer' ? 'bg-green-100 text-green-800' : c.status === 'lead' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>{c.status}</span>
                  </div>
                  <div className="mt-3 space-y-1">
                    {c.email && <div className="flex items-center gap-2 text-sm text-gray-600"><Mail className="w-4 h-4" />{c.email}</div>}
                    {c.phone && <div className="flex items-center gap-2 text-sm text-gray-600"><Phone className="w-4 h-4" />{c.phone}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'pipeline' && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(pipeline).map(([stage, data]) => (
                <div key={stage} className="card p-4">
                  <h3 className="text-sm font-medium text-gray-500 capitalize mb-2">{stage.replace(/_/g, ' ')}</h3>
                  <p className="text-2xl font-bold text-gray-900">{data.count}</p>
                  <p className="text-sm text-gray-600">${Number(data.total_value || 0).toLocaleString()}</p>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'companies' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {companies.map(c => (
                <div key={c.id} className="card p-5">
                  <h3 className="font-semibold text-gray-900">{c.name}</h3>
                  <p className="text-sm text-gray-500">{c.industry}</p>
                  <p className="text-sm text-gray-400 mt-1">{c.size} employees</p>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'deals' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {deals.map(d => (
                <div key={d.id} className="card p-5">
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-gray-900">{d.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${d.stage === 'closed_won' ? 'bg-green-100 text-green-800' : d.stage === 'closed_lost' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>{d.stage}</span>
                  </div>
                  <p className="text-lg font-bold text-indigo-600 mt-2">${Number(d.value || 0).toLocaleString()}</p>
                  <p className="text-sm text-gray-500">{d.probability}% probability</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

