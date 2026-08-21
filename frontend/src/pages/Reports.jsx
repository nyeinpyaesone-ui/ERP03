import React, { useState, useEffect } from 'react';
import { FileText, BarChart3, Download, TrendingUp, PieChart, Activity } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Reports() {
  const [revenue, setRevenue] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [activeReport, setActiveReport] = useState('revenue');
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    if (activeReport === 'revenue') axios.get(`${API_URL}/api/v1/reports/revenue`, axiosConfig).then(r => setRevenue(r.data));
    if (activeReport === 'pipeline') axios.get(`${API_URL}/api/v1/reports/pipeline`, axiosConfig).then(r => setPipeline(r.data));
    if (activeReport === 'inventory') axios.get(`${API_URL}/api/v1/reports/inventory`, axiosConfig).then(r => setInventory(r.data));
  }, [activeReport]);

  const reports = [
    { id: 'revenue', label: 'Revenue Report', icon: TrendingUp },
    { id: 'pipeline', label: 'Sales Pipeline', icon: PieChart },
    { id: 'inventory', label: 'Inventory Status', icon: Activity },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Reports</h1>
      <div className="flex gap-2 mb-6">
        {reports.map(r => (
          <button key={r.id} onClick={() => setActiveReport(r.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${activeReport === r.id ? 'bg-indigo-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'}`}>
            <r.icon className="w-4 h-4" />{r.label}
          </button>
        ))}
      </div>
      <div className="card p-6">
        {activeReport === 'revenue' && revenue && (
          <div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Total Revenue</p><p className="text-2xl font-bold">${Number(revenue.total_revenue).toLocaleString()}</p></div>
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Total Paid</p><p className="text-2xl font-bold">${Number(revenue.total_paid).toLocaleString()}</p></div>
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Outstanding</p><p className="text-2xl font-bold">${Number(revenue.outstanding).toLocaleString()}</p></div>
            </div>
            <h3 className="font-semibold mb-3">Monthly Breakdown</h3>
            <div className="space-y-2">
              {revenue.monthly_breakdown?.map((m, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">{m.month}</span>
                  <span className="text-gray-900">${Number(m.revenue).toLocaleString()} ({m.count} invoices)</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {activeReport === 'pipeline' && pipeline && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(pipeline).map(([stage, data]) => (
              <div key={stage} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 capitalize">{stage.replace(/_/g, ' ')}</p>
                <p className="text-2xl font-bold">{data.count}</p>
                <p className="text-sm text-gray-600">${Number(data.value).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
        {activeReport === 'inventory' && inventory && (
          <div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Total Products</p><p className="text-2xl font-bold">{inventory.total_products}</p></div>
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Stock Value</p><p className="text-2xl font-bold">${Number(inventory.total_stock_value).toLocaleString()}</p></div>
              <div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-500">Low Stock</p><p className="text-2xl font-bold text-red-600">{inventory.low_stock_count}</p></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

