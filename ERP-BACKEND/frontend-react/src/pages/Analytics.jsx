import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Package, DollarSign, Activity, Calendar, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [trends, setTrends] = useState(null);
  const [forecast, setForecast] = useState(null);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/analytics/dashboard`, axiosConfig).then(r => setData(r.data));
    axios.get(`${API_URL}/api/v1/analytics/monthly-trends`, axiosConfig).then(r => setTrends(r.data));
    axios.get(`${API_URL}/api/v1/ai/forecast/revenue`, axiosConfig).then(r => setForecast(r.data)).catch(() => {});
  }, []);

  if (!data) return <div className="p-6 text-center">Loading analytics...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Analytics</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            <p className="text-sm text-gray-500">Revenue</p>
          </div>
          <p className="text-2xl font-bold">${Number(data.revenue?.total || 0).toLocaleString()}</p>
          <p className="text-xs text-gray-400 mt-1">{data.revenue?.collection_rate?.toFixed(1)}% collection rate</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-5 h-5 text-blue-600" />
            <p className="text-sm text-gray-500">Contacts</p>
          </div>
          <p className="text-2xl font-bold">{data.crm?.contacts || 0}</p>
          <p className="text-xs text-gray-400 mt-1">{data.crm?.deals || 0} deals</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Package className="w-5 h-5 text-amber-600" />
            <p className="text-sm text-gray-500">Products</p>
          </div>
          <p className="text-2xl font-bold">{data.inventory?.total_products || 0}</p>
          <p className="text-xs text-gray-400 mt-1">{data.inventory?.low_stock || 0} low stock</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-red-600" />
            <p className="text-sm text-gray-500">Projects</p>
          </div>
          <p className="text-2xl font-bold">{data.projects?.active_projects || 0}</p>
          <p className="text-xs text-gray-400 mt-1">{data.projects?.tasks?.total || 0} total tasks</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-600" /> Monthly Trends
          </h2>
          <div className="space-y-3">
            {trends?.revenue?.map((r, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">{r.period}</span>
                <span className="text-gray-900 font-medium">${Number(r.amount).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" /> AI Revenue Forecast
          </h2>
          {forecast ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${forecast.trend === 'increasing' ? 'bg-green-100 text-green-800' : forecast.trend === 'decreasing' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                  {forecast.trend} trend
                </span>
              </div>
              {forecast.forecast?.map((f, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Month +{f.month}</span>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">${Number(f.predicted_revenue).toLocaleString()}</p>
                    <p className="text-xs text-gray-500">${Number(f.confidence_low).toLocaleString()} - ${Number(f.confidence_high).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">Forecast data unavailable</p>
          )}
        </div>
      </div>

      <div className="card p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {data.recent_activity?.slice(0, 10).map((a, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-indigo-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm text-gray-900 capitalize">{a.action.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-500">{a.entity_type} • {a.created_at ? new Date(a.created_at).toLocaleString() : ''}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

