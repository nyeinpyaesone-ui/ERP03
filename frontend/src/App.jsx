import { Suspense, lazy } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { ProtectedRoute, GuestRoute } from './components/ProtectedRoute';
import SupabaseIdentityPage from './pages/SupabaseIdentityPage';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const SalesPage = lazy(() => import('./pages/SalesPage'));
const ProductsPage = lazy(() => import('./pages/ProductsPage'));
const CustomersPage = lazy(() => import('./pages/CustomersPage'));
const InventoryPage = lazy(() => import('./pages/InventoryPage'));

const router = createBrowserRouter([
  {
    element: <ProtectedRoute />,
    children: [{
      path: '/',
      element: <Layout />,
      children: [
        { index: true, element: <DashboardPage /> },
        { path: 'sales', element: <SalesPage /> },
        { path: 'products', element: <ProductsPage /> },
        { path: 'customers', element: <CustomersPage /> },
        { path: 'inventory', element: <InventoryPage /> },
        { path: 'settings/authentication', element: <SupabaseIdentityPage /> },
      ],
    }],
  },
  {
    element: <GuestRoute />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
]);

export default function App() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-gray-50">Loading…</div>}>
      <RouterProvider router={router} />
    </Suspense>
  );
}
