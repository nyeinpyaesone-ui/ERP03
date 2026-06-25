import React, { useState, useEffect } from 'react';
import { Receipt, DollarSign, Plus, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Finance() {
  const [invoices, setInvoices] = useState([]);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/finance/invoices`, axiosConfig).then(r => setInvoices(r.data));
  }, []);

  const statusColors = {
    draft: 'bg-gray-100 text-gray-800',
    sent: 'bg-blue-100 text-blue-800',
    paid: 'bg-green-100 text-green-800',
    overdue: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-500',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Finance</h1>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> New Invoice</button>
      </div>
      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50"><tr>
            <th className="px-4 py-3 text-left font-medium">Invoice #</th>
            <th className="px-4 py-3 text-left font-medium">Date</th>
            <th className="px-4 py-3 text-left font-medium">Due</th>
            <th className="px-4 py-3 text-left font-medium">Total</th>
            <th className="px-4 py-3 text-left font-medium">Paid</th>
            <th className="px-4 py-3 text-left font-medium">Status</th>
          </tr></thead>
          <tbody className="divide-y">
            {invoices.map(inv => (
              <tr key={inv.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-medium text-indigo-600">{inv.invoice_number}</td>
                <td className="px-4 py-3 text-gray-600">{inv.issue_date}</td>
                <td className="px-4 py-3 text-gray-600">{inv.due_date}</td>
                <td className="px-4 py-3 font-medium">${Number(inv.total).toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-600">${Number(inv.amount_paid || 0).toFixed(2)}</td>
                <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[inv.status] || 'bg-gray-100'}`}>{inv.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

