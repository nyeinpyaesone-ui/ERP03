import { useState } from 'react';
import { Users, Search, UserPlus, CreditCard } from 'lucide-react';

export default function CustomersPage() {
  const [search, setSearch] = useState('');

  const customers = [
    { id: 1, name: 'Aung Aung', email: 'aung@example.com', phone: '09-1234567', customerType: 'Walk-in', totalSpent: 125000, lastVisit: '2 hours ago' },
    { id: 2, name: 'Hla Hla', email: 'hla@example.com', phone: '09-2345678', customerType: 'Regular', totalSpent: 450000, lastVisit: '1 day ago' },
    { id: 3, name: 'Kyaw Kyaw', email: 'kyaw@example.com', phone: '09-3456789', customerType: 'VIP', totalSpent: 1200000, lastVisit: '3 days ago' },
    { id: 4, name: 'Su Su', email: 'su@example.com', phone: '09-4567890', customerType: 'Regular', totalSpent: 320000, lastVisit: '1 week ago' },
  ];

  const filtered = customers.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-600">Manage customer records and loyalty</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium">
          <UserPlus size={16} /> Add Customer
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search customers by name or email..."
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Spent</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Visit</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                      <Users className="w-4 h-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{c.name}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">{c.email}</td>
                <td className="px-4 py-3 text-gray-600">{c.phone}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    c.customerType === 'VIP' ? 'bg-purple-100 text-purple-600' :
                    c.customerType === 'Regular' ? 'bg-blue-100 text-blue-600' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {c.customerType}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  {c.totalSpent.toLocaleString()} MMK
                </td>
                <td className="px-4 py-3 text-gray-600">{c.lastVisit}</td>
                <td className="px-4 py-3 text-right">
                  <button className="text-gray-400 hover:text-blue-600 transition">
                    <CreditCard className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
