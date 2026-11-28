import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const navItems = [
    { name: 'Dashboard', href: '/' },
    { name: 'POS Sales', href: '/sales' },
    { name: 'Products', href: '/products' },
    { name: 'Customers', href: '/customers' },
    { name: 'Inventory', href: '/inventory' },
    { name: 'Authentication', href: '/settings/authentication' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="flex items-center justify-between px-6 py-3">
          <Link to="/" className="font-bold text-xl tracking-tight text-blue-700">ERP03 Control Plane</Link>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium">{user?.email}</p>
              <p className="text-xs text-gray-500">{user?.business_id}</p>
            </div>
            <button onClick={logout} className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600">Sign out</button>
          </div>
        </div>
      </header>
      <div className="flex">
        <aside className="hidden lg:flex lg:w-64 shrink-0 flex-col border-r border-gray-200 bg-white min-h-[calc(100vh-57px)]">
          <nav className="p-6 space-y-1">
            {navItems.map((item) => (
              <Link key={item.name} to={item.href} className="block px-4 py-3 rounded-lg font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-700">
                {item.name}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1 p-6"><Outlet /></main>
      </div>
    </div>
  );
}
