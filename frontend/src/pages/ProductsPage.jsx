import { useState } from 'react';
import { Plus, Search, Box, Tag, Package } from 'lucide-react';

export default function ProductsPage() {
  const [search, setSearch] = useState('');

  const products = [
    { id: 1, sku: 'SKU-001', name: 'Rice 5kg', category: 'Groceries', price: 4500, stock: 120, minStock: 10 },
    { id: 2, sku: 'SKU-002', name: 'Cooking Oil 1L', category: 'Groceries', price: 3200, stock: 85, minStock: 20 },
    { id: 3, sku: 'SKU-003', name: 'Soap Bar', category: 'Household', price: 600, stock: 300, minStock: 50 },
    { id: 4, sku: 'SKU-004', name: 'Toothpaste', category: 'Personal Care', price: 1200, stock: 60, minStock: 15 },
    { id: 5, sku: 'SKU-005', name: 'Notebook A4', category: 'Stationery', price: 800, stock: 45, minStock: 25 },
  ];

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600">Manage product catalog and inventory</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium">
          <Plus size={16} /> Add Product
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search products by name or SKU..."
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Stock</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Min Stock</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-900 font-medium">{p.sku}</td>
                <td className="px-4 py-3 text-gray-700">{p.name}</td>
                <td className="px-4 py-3 text-gray-600">
                  <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-600 text-xs">
                    {p.category}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  {p.price.toLocaleString()} MMK
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-medium ${p.stock <= p.minStock ? 'text-red-600' : 'text-gray-900'}`}>
                    {p.stock}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-gray-600">{p.minStock}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    p.stock <= p.minStock ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                  }`}>
                    {p.stock <= p.minStock ? 'Low Stock' : 'In Stock'}
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
            <p className="text-sm font-medium text-blue-900">Low Stock Alert</p>
            <p className="text-sm text-blue-600">
              {filtered.filter(p => p.stock <= p.minStock).length} product(s) running below minimum stock level
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
