import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { name: 'ပင်မစာမျက်နှာ', href: '/', icon: 'layout-dashboard' },
    { name: 'အရောင်း / POS', href: '/sales', icon: 'shopping-cart' },
    { name: 'ကုန်ပစ္စည်း', href: '/products', icon: 'package' },
    { name: 'ဖောက်သည်များ', href: '/customers', icon: 'users' },
    { name: 'လက်ကျန်ကုန်ပစ္စည်း', href: '/inventory', icon: 'box' },
  ];

  return (
    <div className="min-h-screen bg-[#F5F7F8] text-[#172B2A]">
      {/* Top Bar */}
      <header className="sticky top-0 z-10 border-b border-[#D5E0DF] bg-white">
        <div className="flex items-center justify-between px-6 py-3">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold tracking-tight text-[#087F78]">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            ERP03 Control Plane
          </Link>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 rounded-full bg-[#EAF1F0] px-3 py-2 text-xs font-medium text-[#526766]">
              <span className="h-2 w-2 rounded-full bg-[#087F78]"></span>
              <span>Online</span>
            </div>
            <div className="flex items-center gap-3 border-l border-[#D5E0DF] pl-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium">{user?.email}</p>
                <p className="text-xs text-[#526766]">{user?.business_id}</p>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-[#526766] transition hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#087F78]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="hidden min-h-[calc(100vh-61px)] flex-col border-r border-[#D5E0DF] bg-white lg:flex lg:w-64">
        <div className="p-6">
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="flex items-center gap-3 rounded-lg px-4 py-3 font-medium text-[#526766] transition-all hover:bg-[#EAF1F0] hover:text-[#087F78] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#087F78]"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64 p-6">
        <Outlet />
      </div>
    </div>
  );
}
