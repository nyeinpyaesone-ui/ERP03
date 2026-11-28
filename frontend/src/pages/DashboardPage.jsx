import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

const formatAmount = (value, currency) => Number(value || 0).toLocaleString() + ' ' + (currency || 'MMK');

export default function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api.getDashboardSummary().then((result) => {
      if (active) setSummary(result);
    }).catch((err) => {
      if (active) setError(err.message || 'Unable to load dashboard summary.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const cards = summary ? [
    { label: 'Sales this month', value: formatAmount(summary.sales_total, summary.currency), hint: 'Month to date' },
    { label: 'Orders this month', value: Number(summary.orders_count || 0).toLocaleString(), hint: 'Committed invoices' },
    { label: 'Products', value: Number(summary.products_count || 0).toLocaleString(), hint: 'Active catalog records' },
    { label: 'Customers', value: Number(summary.customers_count || 0).toLocaleString(), hint: 'Active customer accounts' },
    { label: 'Outstanding balance', value: formatAmount(summary.outstanding_balance, summary.currency), hint: 'Unpaid invoice balances' },
    { label: 'Low-stock products', value: Number(summary.low_stock_count || 0).toLocaleString(), hint: 'At or below minimum stock' },
  ] : [];

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome back, {user?.display_name || user?.email || 'team member'}.</p>
        {summary && <p className="mt-1 text-xs text-gray-500">Reporting period: month to date · {summary.timezone} · {summary.currency}</p>}
      </header>

      {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? <div className="rounded-lg border bg-white p-8 text-center text-gray-500">Loading business metrics…</div> : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {cards.map((card) => (
            <article key={card.label} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-gray-500">{card.label}</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{card.value}</p>
              <p className="mt-1 text-xs text-gray-500">{card.hint}</p>
            </article>
          ))}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Link to="/sales" className="rounded-lg border bg-white p-5 hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <h2 className="font-semibold">Point of sale</h2>
          <p className="mt-1 text-sm text-gray-600">Create a sale with transactional stock and payment handling.</p>
        </Link>
        <Link to="/products" className="rounded-lg border bg-white p-5 hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <h2 className="font-semibold">Product catalog</h2>
          <p className="mt-1 text-sm text-gray-600">Manage products, pricing and minimum stock levels.</p>
        </Link>
        <Link to="/inventory" className="rounded-lg border bg-white p-5 hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <h2 className="font-semibold">Inventory</h2>
          <p className="mt-1 text-sm text-gray-600">Review live warehouse balances and stock alerts.</p>
        </Link>
      </div>
    </section>
  );
}
