import React, { useState, useEffect } from 'react';
import { FolderKanban, CheckCircle, Clock, AlertCircle, Plus, Calendar, BarChart3 } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/projects/projects`, axiosConfig).then(r => setProjects(r.data));
  }, []);

  const statusColors = {
    planning: 'bg-gray-100 text-gray-800',
    active: 'bg-blue-100 text-blue-800',
    on_hold: 'bg-amber-100 text-amber-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> New Project</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map(p => (
          <div key={p.id} className="card p-5">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{p.name}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[p.status] || 'bg-gray-100'}`}>{p.status}</span>
            </div>
            <p className="text-sm text-gray-500 mb-4 line-clamp-2">{p.description}</p>
            <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
              <div className="flex items-center gap-1"><Calendar className="w-4 h-4" />{p.start_date || 'No date'}</div>
              <div className="flex items-center gap-1"><BarChart3 className="w-4 h-4" />{p.priority}</div>
            </div>
            {p.budget && <p className="text-sm font-medium text-gray-900">Budget: ${Number(p.budget).toLocaleString()}</p>}
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-indigo-600 h-2 rounded-full" style={{width: `${p.progress || 0}%`}}></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">{p.progress || 0}% complete</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

