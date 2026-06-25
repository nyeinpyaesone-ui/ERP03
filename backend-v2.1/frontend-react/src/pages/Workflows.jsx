import React, { useState, useEffect } from 'react';
import { Workflow, Plus, ToggleLeft, ToggleRight, Trash2, Play, GitBranch, Settings2 } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [activeTab, setActiveTab] = useState('workflows');
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/workflows/workflows`, axiosConfig).then(r => setWorkflows(r.data));
    axios.get(`${API_URL}/api/v1/workflows/executions`, axiosConfig).then(r => setExecutions(r.data));
  }, []);

  const toggleWorkflow = async (id) => {
    try {
      await axios.put(`${API_URL}/api/v1/workflows/workflows/${id}/toggle`, {}, axiosConfig);
      setWorkflows(workflows.map(w => w.id === id ? { ...w, is_active: !w.is_active } : w));
    } catch (e) { console.error(e); }
  };

  const deleteWorkflow = async (id) => {
    if (!confirm('Delete this workflow?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/workflows/workflows/${id}`, axiosConfig);
      setWorkflows(workflows.filter(w => w.id !== id));
    } catch (e) { console.error(e); }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Workflow className="w-8 h-8 text-indigo-600" /> Workflow Automation
        </h1>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Workflow
        </button>
      </div>

      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[{id:'workflows',label:'Workflows',icon:GitBranch},{id:'executions',label:'Executions',icon:Play}].map(t => (
          <button key={t.id} onClick={()=>setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${activeTab===t.id?'bg-white text-indigo-600 shadow-sm':'text-gray-600'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {activeTab === 'workflows' && (
        <div className="space-y-4">
          {workflows.map(w => (
            <div key={w.id} className="card p-5">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-gray-900">{w.name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${w.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                      {w.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{w.description}</p>
                  <div className="flex gap-2 mt-2">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 capitalize">{w.entity_type}</span>
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 capitalize">{w.trigger_type}</span>
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">{w.steps?.length || 0} steps</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => toggleWorkflow(w.id)} className="p-2 hover:bg-gray-100 rounded-lg">
                    {w.is_active ? <ToggleRight className="w-6 h-6 text-green-600" /> : <ToggleLeft className="w-6 h-6 text-gray-400" />}
                  </button>
                  <button onClick={() => deleteWorkflow(w.id)} className="p-2 hover:bg-red-50 text-red-500 rounded-lg">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
          {workflows.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Workflow className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No workflows yet. Create your first automation.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'executions' && (
        <div className="card overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50"><tr>
              <th className="px-4 py-3 text-left font-medium">Workflow</th>
              <th className="px-4 py-3 text-left font-medium">Entity</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Step</th>
              <th className="px-4 py-3 text-left font-medium">Started</th>
            </tr></thead>
            <tbody className="divide-y">
              {executions.map(e => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{e.workflow?.name || e.workflow_id}</td>
                  <td className="px-4 py-3 text-gray-600">{e.entity_type} #{e.entity_id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${e.status === 'completed' ? 'bg-green-100 text-green-800' : e.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                      {e.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">Step {e.current_step}</td>
                  <td className="px-4 py-3 text-gray-500">{e.started_at ? new Date(e.started_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

