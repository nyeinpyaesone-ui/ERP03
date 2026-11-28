import { useEffect, useState } from 'react';
import { Box, Search, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function InventoryPage() {
  const [items, setItems] = useState([]);
  const [branches, setBranches] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [branchId, setBranchId] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let active = true;
    api.getBusinessContext().then((context) => {
      if (!active) return;
      setBranches(context.branches || []);
      setWarehouses(context.warehouses || []);
      setBranchId(context.branches?.[0]?.id || '');
    }).catch((err) => {
      if (active) setError(err.message || 'Unable to load branch context.');
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    const params = {};
    if (branchId) params.branch_id = branchId;
    if (warehouseId) params.warehouse_id = warehouseId;
    if (search.trim()) params.search = search.trim();

    api.getStockBalances(params).then((result) => {
      if (active) setItems(result.items || []);
    }).catch((err) => {
      if (active) setError(err.message || 'Unable to load inventory balances.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [branchId, warehouseId, search, refresh]);

  const branchWarehouses = warehouses.filter((warehouse) => !branchId || warehouse.branch_id === branchId);

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-gray-600">Live stock balances by branch and warehouse</p>
        </div>
        <button type="button" onClick={() => setRefresh((value) => value + 1)} className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          <RefreshCw size={16} /> Refresh view
        </button>
      </header>

      {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="grid gap-3 rounded-lg border bg-white p-4 md:grid-cols-3">
        <label className="text-sm">Branch
          <select aria-label="Filter inventory by branch" value={branchId} onChange={(e) => { setBranchId(e.target.value); setWarehouseId(''); }} className="mt-1 w-full rounded-md border p-2">
            <option value="">All accessible branches</option>
            {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
          </select>
        </label>
        <label className="text-sm">Warehouse
          <select aria-label="Filter inventory by warehouse" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} className="mt-1 w-full rounded-md border p-2">
            <option value="">All warehouses</option>
            {branchWarehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
          </select>
        </label>
        <label className="text-sm">Search
          <span className="relative mt-1 block">
            <Search aria-hidden="true" className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input aria-label="Search inventory" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Product or SKU" className="w-full rounded-md border py-2 pl-9 pr-3" />
          </span>
        </label>
      </div>

      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr><th className="px-4 py-3">Product</th><th className="px-4 py-3">SKU</th><th className="px-4 py-3">Warehouse</th><th className="px-4 py-3 text-right">Quantity</th><th className="px-4 py-3">Unit</th><th className="px-4 py-3 text-right">Minimum</th><th className="px-4 py-3">Status</th></tr>
          </thead>
          <tbody className="divide-y">
            {loading ? <tr><td colSpan="7" className="p-8 text-center text-gray-500">Loading stock balances…</td></tr>
              : items.length === 0 ? <tr><td colSpan="7" className="p-8 text-center text-gray-500">No stock balances found for this selection.</td></tr>
                : items.map((item) => (
                  <tr key={item.product_id + ':' + item.warehouse_id}>
                    <td className="px-4 py-3 font-medium">{item.product}</td>
                    <td className="px-4 py-3 text-gray-600">{item.sku}</td>
                    <td className="px-4 py-3 text-gray-600">{item.warehouse}</td>
                    <td className="px-4 py-3 text-right font-semibold">{Number(item.quantity).toLocaleString()}</td>
                    <td className="px-4 py-3">{item.unit}</td>
                    <td className="px-4 py-3 text-right">{Number(item.min_stock).toLocaleString()}</td>
                    <td className="px-4 py-3"><span className={item.status === 'in_stock' ? 'text-green-700' : 'text-red-700'}>{item.status.replaceAll('_', ' ')}</span></td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-3 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
        <Box className="h-5 w-5 shrink-0" />
        <p>{items.length} stock record(s) returned from the selected ERP scope. Balances are read from the authoritative inventory tables.</p>
      </div>
    </section>
  );
}
