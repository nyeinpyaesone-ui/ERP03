import { Link, NavLink, Outlet } from 'react-router-dom';
import {
  Box,
  LayoutDashboard,
  LogOut,
  Package,
  ShoppingCart,
  Users,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { name: 'ပင်မစာမျက်နှာ', href: '/', Icon: LayoutDashboard },
  { name: 'အရောင်း / POS', href: '/sales', Icon: ShoppingCart },
  { name: 'ကုန်ပစ္စည်း', href: '/products', Icon: Package },
  { name: 'ဖောက်သည်များ', href: '/customers', Icon: Users },
  { name: 'လက်ကျန်ကုန်ပစ္စည်း', href: '/inventory', Icon: Box },
];

const navLinkClass = ({ isActive }) =>
  [
    'flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary',
    isActive
      ? 'bg-erp-surfaceMuted text-erp-primary'
      : 'text-erp-foregroundMuted hover:bg-erp-surfaceMuted hover:text-erp-primary',
  ].join(' ');

function PrimaryNavigation({ mobile = false }) {
  return (
    <nav
      aria-label="Primary navigation"
      className={mobile ? 'flex gap-2 overflow-x-auto pb-2 lg:hidden' : 'flex flex-col gap-1'}
    >
      {navItems.map(({ name, href, Icon }) => (
        <NavLink
          key={href}
          to={href}
          end={href === '/'}
          className={({ isActive }) =>
            [
              navLinkClass({ isActive }),
              mobile ? 'shrink-0 whitespace-nowrap px-3 py-2' : '',
            ].join(' ')
          }
        >
          <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
          <span>{name}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-erp-background text-erp-foreground">
      <header className="sticky top-0 z-20 border-b border-erp-border bg-erp-surface">
        <div className="flex min-h-16 items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="flex min-w-0 items-center gap-2 text-lg font-bold tracking-tight text-erp-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-erp-primary sm:text-xl"
          >
            <LayoutDashboard aria-hidden="true" size={22} />
            <span className="truncate">ERP03 Control Plane</span>
          </Link>

          <div className="flex shrink-0 items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="max-w-56 truncate text-sm font-medium">{user?.email}</p>
              <p className="max-w-56 truncate text-xs text-erp-foregroundMuted">
                {user?.business_id}
              </p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-erp-foregroundMuted transition-colors hover:bg-erp-surfaceMuted hover:text-erp-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary"
              aria-label="Sign out"
            >
              <LogOut aria-hidden="true" size={17} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-screen-2xl">
        <aside className="hidden min-h-[calc(100vh-4rem)] w-64 shrink-0 border-r border-erp-border bg-erp-surface p-4 lg:block">
          <PrimaryNavigation />
        </aside>

        <main id="main-content" className="min-w-0 flex-1 p-4 sm:p-6">
          <PrimaryNavigation mobile />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
