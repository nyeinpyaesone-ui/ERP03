import { useEffect, useState } from 'react';
import { Plus, Search, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

const emptyForm = { code: '', name: '', phone: '', credit_limit: '0' };
const money = (value, currency) => Number(value || 0).toLocaleString() + ' ' + (currency || 'MMK');

export default function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [receivables, setReceivables] = useState([]);
  const [collection, setCollection] = useState(null);
  const [collectionAmount, setCollectionAmount] = useState('');
  const [collectionMethod, setCollectionMethod] = useState('cash');
  const [collectionSaving, setCollectionSaving] = useState(false);
  const [branches, setBranches] = useState([]);
  const [branchId, setBranchId] = useState('');
  const [currency, setCurrency] = useState('MMK');
  const [search, setSearch] = useState('');
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [context, result, debt] = await Promise.all([
        api.getBusinessContext(),
        api.listCustomers({ limit: 200, offset: 0 }),
        api.listOutstandingReceivables({ limit: 200, offset: 0 }),
      ]);
      setBranches(context.branches || []);
      setBranchId((current) => current || context.branches?.[0]?.id || '');
      setCurrency(context.business?.currency || 'MMK');
      setCustomers(result.items || []);
      setReceivables(debt.items || []);
    } catch (err) {
      setError(err.message || 'Unable to load customers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const visible = customers.filter((item) => {
    const term = search.trim().toLowerCase();
    return (!branchId || item.branch_id === branchId)
      && (!term || item.name.toLowerCase().includes(term) || item.code.toLowerCase().includes(term) || (item.phone || '').toLowerCase().includes(term));
  });

  const updateForm = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));

  const collectPayment = async (event) => {
    event.preventDefault();
    if (!collection) return;
    setCollectionSaving(true);
    setError('');
    setNotice('');
    try {
      await api.collectReceivable(
        {
          invoice_id: collection.invoice_id,
          amount: collectionAmount,
          method: collectionMethod,
          currency: collection.currency,
        },
        crypto.randomUUID(),
      );
      setCollection(null);
      setCollectionAmount('');
      setNotice('Customer payment recorded.');
      await load();
    } catch (err) {
      setError(err.message || 'Payment could not be recorded.');
    } finally {
      setCollectionSaving(false);
    }
  };

  const createCustomer = async (event) => {
    event.preventDefault();
    if (!branchId) {
      setError('This account has no accessible branch. Ask an administrator to assign one.');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await api.createCustomer({
        branch_id: branchId,
        code: form.code.trim(),
        name: form.name.trim(),
        phone: form.phone.trim() || null,
        credit_limit: form.credit_limit || '0',
      });
      setForm(emptyForm);
      setShowForm(false);
      setNotice('Customer saved.');
      await load();
    } catch (err) {
      setError(err.message || 'Customer could not be saved.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-600">Customer accounts and credit limits</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm"><RefreshCw size={16} /> Refresh</button>
          <button type="button" onClick={() => setShowForm((value) => !value)} className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"><Plus size={16} /> Add customer</button>
        </div>
      </header>

      {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {notice && <div role="status" className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">{notice}</div>}

      {showForm && (
        <form onSubmit={createCustomer} className="grid gap-3 rounded-lg border bg-white p-5 md:grid-cols-2">
          <h2 className="font-semibold md:col-span-2">Create customer</h2>
          <label className="text-sm">Branch
            <select value={branchId} onChange={(e) => setBranchId(e.target.value)} required className="mt-1 w-full rounded-md border p-2">
              {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
            </select>
          </label>
          <label className="text-sm">Customer code
            <input name="code" value={form.code} onChange={updateForm} required maxLength={64} className="mt-1 w-full rounded-md border p-2" />
          </label>
          <label className="text-sm">Customer name
            <input name="name" value={form.name} onChange={updateForm} required maxLength={200} className="mt-1 w-full rounded-md border p-2" />
          </label>
          <label className="text-sm">Phone
            <input name="phone" value={form.phone} onChange={updateForm} maxLength={32} className="mt-1 w-full rounded-md border p-2" />
          </label>
          <label className="text-sm">Credit limit ({currency})
            <input name="credit_limit" type="number" min="0" step="0.01" value={form.credit_limit} onChange={updateForm} className="mt-1 w-full rounded-md border p-2" />
          </label>
          <div className="flex justify-end gap-2 md:col-span-2">
            <button type="button" onClick={() => setShowForm(false)} className="rounded-md border px-4 py-2 text-sm">Cancel</button>
            <button disabled={saving} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{saving ? 'Saving…' : 'Save customer'}</button>
          </div>
        </form>
      )}

      <div className="flex flex-wrap gap-3">
        <label className="relative min-w-[220px] flex-1">
          <Search aria-hidden="true" className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <input aria-label="Search customers" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name, code or phone" className="w-full rounded-md border py-2 pl-9 pr-3" />
        </label>
        <label className="text-sm">Branch
          <select aria-label="Filter branch" value={branchId} onChange={(e) => setBranchId(e.target.value)} className="ml-2 rounded-md border p-2">
            <option value="">All accessible branches</option>
            {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
          </select>
        </label>
      </div>

      <section className="space-y-3 rounded-lg border bg-white p-5">
        <div>
          <h2 className="font-semibold text-gray-900">Outstanding customer balances</h2>
          <p className="text-sm text-gray-600">Collect payments against existing customer invoices.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr><th className="px-3 py-2">Invoice</th><th className="px-3 py-2">Customer</th><th className="px-3 py-2 text-right">Outstanding</th><th className="px-3 py-2">Action</th></tr>
            </thead>
            <tbody className="divide-y">
              {loading ? <tr><td colSpan="4" className="p-5 text-center text-gray-500">Loading balances…</td></tr>
                : receivables.filter((item) => !branchId || item.branch_id === branchId).length === 0
                  ? <tr><td colSpan="4" className="p-5 text-center text-gray-500">No outstanding customer invoices.</td></tr>
                  : receivables.filter((item) => !branchId || item.branch_id === branchId).map((item) => (
                    <tr key={item.invoice_id}>
                      <td className="px-3 py-3 font-medium">{item.invoice_no}</td>
                      <td className="px-3 py-3">{item.customer_name}</td>
                      <td className="px-3 py-3 text-right tabular-nums">{money(item.balance, item.currency)}</td>
                      <td className="px-3 py-3">
                        <button type="button" onClick={() => { setCollection(item); setCollectionAmount(item.balance); }} className="rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-gray-50">Collect</button>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </section>

      {collection && (
        <div role="dialog" aria-modal="true" aria-labelledby="collect-title" className="rounded-lg border border-blue-200 bg-blue-50 p-5">
          <form onSubmit={collectPayment} className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <h2 id="collect-title" className="font-semibold">Collect payment · {collection.invoice_no}</h2>
              <p className="text-sm text-gray-600">{collection.customer_name} · Balance {money(collection.balance, collection.currency)}</p>
            </div>
            <label className="text-sm">Amount ({collection.currency})
              <input aria-label="Collection amount" type="number" min="0.01" max={collection.balance} step="0.01" required value={collectionAmount} onChange={(e) => setCollectionAmount(e.target.value)} className="mt-1 w-full rounded-md border p-2" />
            </label>
            <label className="text-sm">Payment method
              <select value={collectionMethod} onChange={(e) => setCollectionMethod(e.target.value)} className="mt-1 w-full rounded-md border p-2">
                <option value="cash">Cash</option>
                <option value="mobile_wallet">Mobile wallet</option>
                <option value="bank_transfer">Bank transfer</option>
              </select>
            </label>
            <div className="flex justify-end gap-2 md:col-span-2">
              <button type="button" onClick={() => setCollection(null)} className="rounded-md border px-4 py-2 text-sm">Cancel</button>
              <button disabled={collectionSaving} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{collectionSaving ? 'Recording…' : 'Record payment'}</button>
            </div>
          </form>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr><th className="px-4 py-3">Code</th><th className="px-4 py-3">Customer</th><th className="px-4 py-3">Phone</th><th className="px-4 py-3 text-right">Credit limit</th><th className="px-4 py-3">Status</th></tr>
          </thead>
          <tbody className="divide-y">
            {loading ? <tr><td colSpan="5" className="p-8 text-center text-gray-500">Loading customers…</td></tr>
              : visible.length === 0 ? <tr><td colSpan="5" className="p-8 text-center text-gray-500">No customers found.</td></tr>
                : visible.map((customer) => (
                  <tr key={customer.id}>
                    <td className="px-4 py-3 font-medium">{customer.code}</td>
                    <td className="px-4 py-3">{customer.name}</td>
                    <td className="px-4 py-3 text-gray-600">{customer.phone || '—'}</td>
                    <td className="px-4 py-3 text-right">{money(customer.credit_limit, currency)}</td>
                    <td className="px-4 py-3"><span className={customer.active ? 'text-green-700' : 'text-gray-500'}>{customer.active ? 'Active' : 'Inactive'}</span></td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
