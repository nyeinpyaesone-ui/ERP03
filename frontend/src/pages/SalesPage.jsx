import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../services/api';

const money = (value, currency) => Number(value || 0).toLocaleString() + ' ' + (currency || 'MMK');

export default function SalesPage() {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [branchId, setBranchId] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [currency, setCurrency] = useState('MMK');
  const [productId, setProductId] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [paymentAmount, setPaymentAmount] = useState('0');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [refresh, setRefresh] = useState(0);
  const idempotencyKey = useRef(window.crypto.randomUUID());

  useEffect(() => {
    let active = true;
    Promise.all([
      api.getBusinessContext(),
      api.listProducts({ limit: 200, offset: 0 }),
      api.listCustomers({ limit: 200, offset: 0 }),
    ]).then(([context, productResult, customerResult]) => {
      if (!active) return;
      setBranches(context.branches || []);
      setWarehouses(context.warehouses || []);
      setBranchId(context.branches?.[0]?.id || '');
      setCurrency(context.business?.currency || 'MMK');
      setProducts(productResult.items || []);
      setCustomers(customerResult.items || []);
    }).catch((err) => {
      if (active) setError(err.message || 'Unable to load POS data.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    if (!branchId) {
      setSales([]);
      return () => { active = false; };
    }
    api.listSales({ limit: 30, offset: 0, branch_id: branchId }).then((result) => {
      if (active) setSales(result.items || []);
    }).catch((err) => {
      if (active) setError(err.message || 'Unable to load sales history.');
    });
    return () => { active = false; };
  }, [branchId, refresh]);

  const branchWarehouses = warehouses.filter((item) => item.branch_id === branchId);
  const branchProducts = products.filter((item) => item.branch_id === branchId && item.active);
  const branchCustomers = customers.filter((item) => item.branch_id === branchId && item.active);
  const selectedProduct = branchProducts.find((item) => item.id === productId);
  const total = useMemo(() => Number(selectedProduct?.sale_price || 0) * Number(quantity || 0), [selectedProduct, quantity]);

  const submitSale = async (event) => {
    event.preventDefault();
    setError('');
    setNotice('');
    if (!branchId || !warehouseId || !selectedProduct) {
      setError('Select a branch, warehouse and product before completing the sale.');
      return;
    }
    const qty = Number(quantity);
    const paid = Number(paymentAmount || 0);
    if (!Number.isFinite(qty) || qty <= 0 || !Number.isFinite(paid) || paid < 0) {
      setError('Enter a valid quantity and payment amount.');
      return;
    }
    if (paid > total) {
      setError('Payment cannot exceed the sale total.');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        branch_id: branchId,
        warehouse_id: warehouseId,
        customer_id: customerId || null,
        currency,
        lines: [{ product_id: productId, quantity: String(qty), unit_price: String(selectedProduct.sale_price) }],
        payments: paid > 0 ? [{ method: paymentMethod, amount: String(paid), currency }] : [],
      };
      const result = await api.createSale(payload, idempotencyKey.current);
      setNotice('Sale committed. Invoice ' + result.invoice_id + ' · Total ' + money(result.total, currency) + ' · Balance ' + money(result.balance, currency));
      idempotencyKey.current = window.crypto.randomUUID();
      setQuantity('1');
      setPaymentAmount('0');
      setProductId('');
      setCustomerId('');
      setRefresh((value) => value + 1);
    } catch (err) {
      setError(err.message || 'Sale was not committed. Retry safely with the same request key.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">POS Sales</h1>
        <p className="text-gray-600">Sales are committed through the transactional ERP service</p>
      </header>

      {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {notice && <div role="status" className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">{notice}</div>}

      {loading ? <div className="rounded-lg border bg-white p-8 text-center text-gray-500">Loading POS workspace…</div> : (
        <div className="grid gap-6 xl:grid-cols-5">
          <form onSubmit={submitSale} className="space-y-4 rounded-lg border bg-white p-5 xl:col-span-2">
            <h2 className="font-semibold">New sale</h2>
            <label className="block text-sm">Branch
              <select value={branchId} onChange={(e) => { setBranchId(e.target.value); setWarehouseId(''); setProductId(''); setCustomerId(''); }} required className="mt-1 w-full rounded-md border p-2">
                {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
              </select>
            </label>
            <label className="block text-sm">Warehouse
              <select value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required className="mt-1 w-full rounded-md border p-2">
                <option value="">Select warehouse</option>
                {branchWarehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
              </select>
            </label>
            <label className="block text-sm">Product
              <select value={productId} onChange={(e) => setProductId(e.target.value)} required className="mt-1 w-full rounded-md border p-2">
                <option value="">Select product</option>
                {branchProducts.map((product) => <option key={product.id} value={product.id}>{product.sku} · {product.name} · {money(product.sale_price, currency)}</option>)}
              </select>
            </label>
            <label className="block text-sm">Customer
              <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className="mt-1 w-full rounded-md border p-2">
                <option value="">Walk-in customer</option>
                {branchCustomers.map((customer) => <option key={customer.id} value={customer.id}>{customer.code} · {customer.name}</option>)}
              </select>
            </label>
            <label className="block text-sm">Quantity
              <input type="number" min="0.001" step="0.001" value={quantity} onChange={(e) => setQuantity(e.target.value)} required className="mt-1 w-full rounded-md border p-2" />
            </label>
            <div className="rounded-md bg-gray-50 p-3">
              <div className="text-sm text-gray-500">Sale total</div>
              <div className="text-xl font-semibold">{money(total, currency)}</div>
            </div>
            <label className="block text-sm">Payment received ({currency})
              <input type="number" min="0" step="0.01" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} className="mt-1 w-full rounded-md border p-2" />
            </label>
            <label className="block text-sm">Payment method
              <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="mt-1 w-full rounded-md border p-2">
                <option value="cash">Cash</option>
                <option value="bank_transfer">Bank transfer</option>
                <option value="mobile_wallet">Mobile wallet</option>
              </select>
            </label>
            <button type="submit" disabled={saving || !selectedProduct || !warehouseId} className="w-full rounded-md bg-green-600 px-4 py-3 font-medium text-white disabled:opacity-50">
              {saving ? 'Committing sale…' : 'Complete sale'}
            </button>
          </form>

          <div className="space-y-4 rounded-lg border bg-white p-5 xl:col-span-3">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">Recent invoices</h2>
              <button type="button" onClick={() => setRefresh((value) => value + 1)} className="rounded-md border px-3 py-2 text-sm">Refresh</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <tr><th className="px-3 py-3">Invoice</th><th className="px-3 py-3">Customer</th><th className="px-3 py-3 text-right">Total</th><th className="px-3 py-3 text-right">Paid</th><th className="px-3 py-3 text-right">Balance</th></tr>
                </thead>
                <tbody className="divide-y">
                  {sales.length === 0 ? <tr><td colSpan="5" className="p-8 text-center text-gray-500">No sales recorded for this branch.</td></tr>
                    : sales.map((sale) => (
                      <tr key={sale.id}>
                        <td className="px-3 py-3 font-medium">{sale.invoice_no}</td>
                        <td className="px-3 py-3">{sale.customer_name}</td>
                        <td className="px-3 py-3 text-right">{money(sale.total, sale.currency)}</td>
                        <td className="px-3 py-3 text-right">{money(sale.paid, sale.currency)}</td>
                        <td className="px-3 py-3 text-right">{money(sale.balance, sale.currency)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
