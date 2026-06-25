import React, { useState, useEffect } from 'react';
import { Users, Building, Briefcase, DollarSign, Plus } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function HR() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [activeTab, setActiveTab] = useState('employees');
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/hr/employees`, axiosConfig).then(r => setEmployees(r.data));
    axios.get(`${API_URL}/api/v1/hr/departments`, axiosConfig).then(r => setDepartments(r.data));
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Human Resources</h1>
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[{id:'employees',label:'Employees',icon:Users},{id:'departments',label:'Departments',icon:Building}].map(t => (
          <button key={t.id} onClick={()=>setActiveTab(t.id)} className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${activeTab===t.id?'bg-white text-indigo-600 shadow-sm':'text-gray-600'}`}><t.icon className="w-4 h-4"/>{t.label}</button>
        ))}
      </div>
      {activeTab === 'employees' && (
        <div className="card overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50"><tr>
              <th className="px-4 py-3 text-left font-medium">Code</th>
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="px-4 py-3 text-left font-medium">Title</th>
              <th className="px-4 py-3 text-left font-medium">Department</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Salary</th>
            </tr></thead>
            <tbody className="divide-y">
              {employees.map(e => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-600">{e.employee_code}</td>
                  <td className="px-4 py-3 font-medium">{e.full_name || e.employee_code}</td>
                  <td className="px-4 py-3 text-gray-600">{e.job_title}</td>
                  <td className="px-4 py-3 text-gray-600">{e.department?.name || '—'}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs ${e.status==='active'?'bg-green-100 text-green-800':'bg-gray-100 text-gray-800'}`}>{e.status}</span></td>
                  <td className="px-4 py-3 text-gray-900">{e.salary ? `$${Number(e.salary).toLocaleString()}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {activeTab === 'departments' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map(d => (
            <div key={d.id} className="card p-5">
              <h3 className="font-semibold text-gray-900">{d.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{d.description}</p>
              {d.budget && <p className="text-sm font-medium text-gray-900 mt-2">Budget: ${Number(d.budget).toLocaleString()}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

---

