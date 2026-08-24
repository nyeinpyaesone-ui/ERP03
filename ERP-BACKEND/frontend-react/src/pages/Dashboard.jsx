import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users, Building2, Package, Receipt, FolderKanban,
  TrendingUp, TrendingDown, AlertTriangle, Activity,
  DollarSign, BarChart3, ArrowUpRight, ArrowDownRight,
  Sparkles, Zap, Clock, Target, Percent
} from 'lucide-react';
import { LineChartComponent, BarChartComponent, AreaChartComponent, Sparkline } from '../components/Charts.jsx';
import { SkeletonStats } from '../components/Skeleton.jsx';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const statCards = [
  { label: 'Contacts', icon: Users, color: 'bg-blue-500', path: '/crm', key: 'total_contacts', trend: 'contacts_trend' },
  { label: 'Companies', icon: Building2, color: 'bg-indigo-500', path: '/crm', key: 'total_companies' },
  { label: 'Products', icon: Package, color: 'bg-emerald-500', path: '/inventory', key: 'total_products', trend: 'products_trend' },
  { label: 'Revenue', icon: DollarSign, color: 'bg-amber-500', path: '/finance', key: 'total_revenue', format: 'currency', trend: 'revenue_trend' },
];

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState([]);
  const [pipelineData, setPipelineData] = useState([]);
  const [activityData, setActivityData] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const [analytics, crm, hr, inventory, finance, projects, trends] = await Promise.all([
        axios.get(`${API_URL}/api/v1/analytics/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/crm/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/hr/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/inventory/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/finance/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/projects/dashboard`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/v1/analytics/monthly-trends`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
      ]);

      setStats({
        ...analytics.data,
        ...crm.data,
        ...hr.data,
        ...inventory.data,
        ...finance.data,
        ...projects.data,
      });

      // Build chart data
      const monthlyRevenue = trends.data?.revenue?.map(r => ({
        month: r.period,
        revenue: r.amount
      })) || [];
      setRevenueData(monthlyRevenue);

      const pipeline = analytics.data?.crm?.pipeline_value || 0;
      setPipelineData([
        { name: 'Pipeline', value: pipeline, fill: '#4f46e5' },
        { name: 'Won', value: crm.data?.won_deals || 0, fill: '#10b981' },
        { name: 'Lost', value: (crm.data?.total_deals || 0) - (crm.data?.won_deals || 0), fill: '#ef4444' },
      ]);

      const activity = analytics.data?.recent_activity?.slice(0, 7).map((a, i) => ({
        day: `Day ${i + 1}`,
        actions: 1
      })) || [];
      setActivityData(activity);

    } catch (e) { console.error('Dashboard fetch error:', e); }
    finally { setLoading(false); }
  };

  const formatValue = (value, format) => {
    if (value === undefined || value === null) return '—';
    if (format === 'currency') return `$${Number(value).toLocaleString()}`;
    return Number(value).toLocaleString();
  };

  const trendData = [
    { day: 1, value: 120 }, { day: 2, value: 132 }, { day: 3, value: 101 },
    { day: 4, value: 134 }, { day: 5, value: 90 }, { day: 6, value: 230 }, { day: 7, value: 210 }
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto animate-in fade-in duration-500">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-[var(--color-text)]">Dashboard</h1>
          <span className="px-2.5 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-xs font-medium">
            v2.2 PRO MAX
          </span>
        </div>
        <p className="text-[var(--color-text-secondary)]">Overview of your business operations</p>
      </div>

      {/* Stats Grid */}
      {loading ? <SkeletonStats count={4} /> : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((card) => (
            <Link
              key={card.label}
              to={card.path}
              className="card p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 group"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-[var(--color-text-secondary)]">{card.label}</p>
                  <p className="text-2xl font-bold text-[var(--color-text)] mt-1">
                    {formatValue(stats[card.key], card.format)}
                  </p>
                </div>
                <div className={`${card.color} p-3 rounded-xl group-hover:scale-110 transition-transform duration-300`}>
                  <card.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              {card.trend && (
                <div className="flex items-center gap-2">
                  <Sparkline data={trendData} dataKey="value" color={card.color.replace('bg-', '#').replace('500', '600')} />
                  <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-0.5">
                    <TrendingUp className="w-3 h-3" /> +12%
                  </span>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Revenue Chart */}
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              Revenue Trends
            </h2>
            <Link to="/analytics" className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1">
              View All <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          {revenueData.length > 0 ? (
            <AreaChartComponent data={revenueData} xKey="month" yKey="revenue" height={280} />
          ) : (
            <div className="h-[280px] flex items-center justify-center text-[var(--color-text-secondary)]">
              <Activity className="w-8 h-8 mr-2" /> No revenue data yet
            </div>
          )}
        </div>

        {/* Quick Insights */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500" />
            Quick Insights
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <Target className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text)]">Conversion Rate</p>
                <p className="text-lg font-bold text-[var(--color-text)]">
                  {stats.conversion_rate ? `${stats.conversion_rate.toFixed(1)}%` : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                <Percent className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text)]">Collection Rate</p>
                <p className="text-lg font-bold text-[var(--color-text)]">
                  {stats.revenue?.collection_rate ? `${stats.revenue.collection_rate.toFixed(1)}%` : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text)]">Avg Task Completion</p>
                <p className="text-lg font-bold text-[var(--color-text)]">
                  {stats.projects?.completion_rate ? `${stats.projects.completion_rate.toFixed(1)}%` : '—'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Alerts
          </h2>
          <div className="space-y-3">
            {(stats.low_stock || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800/30">
                <Package className="w-5 h-5 text-red-600 dark:text-red-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800 dark:text-red-300">{stats.low_stock} products low on stock</p>
                  <Link to="/inventory" className="text-xs text-red-600 dark:text-red-400 hover:underline">View inventory →</Link>
                </div>
              </div>
            )}
            {(stats.overdue_count || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-100 dark:border-amber-800/30">
                <Receipt className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-300">{stats.overdue_count} overdue invoices</p>
                  <Link to="/finance" className="text-xs text-amber-600 dark:text-amber-400 hover:underline">View finance →</Link>
                </div>
              </div>
            )}
            {(stats.overdue_tasks || 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/30">
                <FolderKanban className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-800 dark:text-blue-300">{stats.overdue_tasks} overdue tasks</p>
                  <Link to="/projects" className="text-xs text-blue-600 dark:text-blue-400 hover:underline">View projects →</Link>
                </div>
              </div>
            )}
            {(!stats.low_stock && !stats.overdue_count && !stats.overdue_tasks) && (
              <div className="text-center py-8 text-[var(--color-text-secondary)]">
                <Activity className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                <p className="text-sm">No alerts at this time</p>
              </div>
            )}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            Recent Activity
          </h2>
          <div className="space-y-3">
            {(stats.recent_activity || []).slice(0, 8).map((activity, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <div className="w-2 h-2 bg-indigo-500 rounded-full flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[var(--color-text)] capitalize">{activity.action.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-[var(--color-text-secondary)]">{activity.entity_type} • {activity.created_at ? new Date(activity.created_at).toLocaleString() : ''}</p>
                </div>
              </div>
            ))}
            {(!stats.recent_activity || stats.recent_activity.length === 0) && (
              <p className="text-sm text-[var(--color-text-secondary)] text-center py-4">No recent activity</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

