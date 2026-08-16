import React, { useState, useEffect } from 'react';
import { Package, AlertTriangle, Plus, ArrowDown, ArrowUp } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Inventory() {
  const [products, setProducts] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/inventory/products`, axiosConfig).then(r => setProducts(r.data));
    axios.get(`${API_URL}/api/v1/inventory/products?low_stock=true`, axiosConfig).then(r => setLowStock(r.data));
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Inventory</h1>
      {lowStock.length > 0 && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-700">{lowStock.length} products are below reorder level</p>
        </div>
      )}
      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50"><tr>
            <th className="px-4 py-3 text-left font-medium">SKU</th>
            <th className="px-4 py-3 text-left font-medium">Product</th>
            <th className="px-4 py-3 text-left font-medium">Stock</th>
            <th className="px-4 py-3 text-left font-medium">Reorder</th>
            <th className="px-4 py-3 text-left font-medium">Price</th>
            <th className="px-4 py-3 text-left font-medium">Status</th>
          </tr></thead>
          <tbody className="divide-y">
            {products.map(p => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-600">{p.sku}</td>
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3"><span className={`font-medium ${p.quantity_in_stock <= p.reorder_level ? 'text-red-600' : 'text-green-600'}`}>{p.quantity_in_stock}</span></td>
                <td className="px-4 py-3 text-gray-500">{p.reorder_level}</td>
                <td className="px-4 py-3">${Number(p.unit_price).toFixed(2)}</td>
                <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs ${p.status==='active'?'bg-green-100 text-green-800':'bg-gray-100'}`}>{p.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

