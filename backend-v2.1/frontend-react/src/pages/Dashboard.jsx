import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users, Building2, Package, Receipt, FolderKanban,
  TrendingUp, TrendingDown, AlertTriangle, Activity,
  DollarSign, BarChart3, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const statCards = [
  { label: 'Contacts', icon: Users, color: 'bg-blue-500', path: '/crm', key: 'total_contacts' },
  { label: 'Companies', icon: Building2, color: 'bg-indigo-500', path: '/crm', key: 'total_companies' },
  { label: 'Products', icon: Package, color: 'bg-emerald-500', path: '/inventory', key: 'total_products' },
  { label: 'Revenue', icon: DollarSign, color: 'bg-amber-500', path: '/finance', key: 'total_revenue', format: 'currency' },
];

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const [analytics, crm, hr, inventory, finance, projects] = await Promise.all([
        axios.get(`${API_URL}/api/v1/analytics/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/crm/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/hr/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/inventory/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/finance/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/projects/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
      ]);

      setStats({
        ...analytics.data,
        ...crm.data,
        ...hr.data,
        ...inventory.data,
        ...finance.data,
        ...projects.data,
      });
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value, format) => {
    if (value === undefined || value === null) return '—';
    if (format === 'currency') return `$${Number(value).toLocaleString()}`;
    return Number(value).toLocaleString();
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your business operations</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <Link
            key={card.label}
            to={card.path}
            className="card p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {loading ? '...' : formatValue(stats[card.key], card.format)}
                </p>
              </div>
              <div className={`${card.color} p-3 rounded-lg`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart Placeholder */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Business Overview
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Active Employees</p>
              <p className="text-xl font-bold text-gray-900">{stats.active_employees || 0}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Active Projects</p>
              <p className="text-xl font-bold text-gray-900">{stats.active_projects || 0}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Pipeline Value</p>
              <p className="text-xl font-bold text-gray-900">${Number(stats.pipeline_value || 0).toLocaleString()}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Outstanding</p>
              <p className="text-xl font-bold text-gray-900">${Number(stats.outstanding || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Alerts */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Alerts
          </h2>
          <div className="space-y-3">
            {(stats.low_stock || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                <Package className="w-4 h-4 text-red-600" />
                <div>
                  <p className="text-sm font-medium text-red-900">{stats.low_stock} products low on stock</p>
                  <Link to="/inventory" className="text-xs text-red-600 hover:underline">View inventory →</Link>
                </div>
              </div>
            )}
            {(stats.overdue_count || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg">
                <Receipt className="w-4 h-4 text-amber-600" />
                <div>
                  <p className="text-sm font-medium text-amber-900">{stats.overdue_count} overdue invoices</p>
                  <Link to="/finance" className="text-xs text-amber-600 hover:underline">View finance →</Link>
                </div>
              </div>
            )}
            {(stats.overdue_tasks || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <FolderKanban className="w-4 h-4 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-900">{stats.overdue_tasks} overdue tasks</p>
                  <Link to="/projects" className="text-xs text-blue-600 hover:underline">View projects →</Link>
                </div>
              </div>
            )}
            {(!stats.low_stock && !stats.overdue_count && !stats.overdue_tasks) && (
              <div className="text-center py-8 text-gray-400">
                <Activity className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">No alerts at this time</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card p-6 mt-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {(stats.recent_activity || []).slice(0, 5).map((activity, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-indigo-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm text-gray-900 capitalize">{activity.action.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-500">{activity.entity_type} • {activity.created_at ? new Date(activity.created_at).toLocaleString() : ''}</p>
              </div>
            </div>
          ))}
          {(!stats.recent_activity || stats.recent_activity.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
}

