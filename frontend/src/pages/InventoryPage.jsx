import { useState } from 'react';
import { Box, Search, ArrowLeft } from 'lucide-react';

export default function InventoryPage() {
  const [search, setSearch] = useState('');

  const inventory = [
    { id: 1, product: 'Rice 5kg', sku: 'SKU-001', warehouse: 'Main Warehouse', quantity: 120, unit: 'pcs', movement: '+120' },
    { id: 2, product: 'Cooking Oil 1L', sku: 'SKU-002', warehouse: 'Main Warehouse', quantity: 85, unit: 'bottle', movement: '-15' },
    { id: 3, product: 'Soap Bar', sku: 'SKU-003', warehouse: 'Main Warehouse', quantity: 300, unit: 'pcs', movement: '+50' },
    { id: 4, product: 'Toothpaste', sku: 'SKU-004', warehouse: 'Main Warehouse', quantity: 60, unit: 'pcs', movement: '-5' },
    { id: 5, product: 'Notebook A4', sku: 'SKU-005', warehouse: 'Main Warehouse', quantity: 45, unit: 'pcs', movement: '+20' },
  ];

  const filtered = inventory.filter(i =>
    i.product.toLowerCase().includes(search.toLowerCase()) ||
    i.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-gray-600">Track stock movements and balances</p>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search inventory by product or SKU..."
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Warehouse</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Unit</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Last Movement</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-900 font-medium">{item.product}</td>
                <td className="px-4 py-3 text-gray-600">{item.sku}</td>
                <td className="px-4 py-3 text-gray-600">{item.warehouse}</td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">{item.quantity}</td>
                <td className="px-4 py-3 text-center text-gray-600">{item.unit}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    item.movement.startsWith('+') ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    {item.movement} {item.unit}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
        <div className="flex items-center gap-3">
          <Box className="w-4 h-4 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-900">Inventory Summary</p>
            <p className="text-sm text-blue-600">
              {filtered.length} product(s) tracked across {new Set(filtered.map(i => i.warehouse)).size} warehouse(s)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
