import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import SalesPage from './pages/SalesPage';
import ProductsPage from './pages/ProductsPage';
import CustomersPage from './pages/CustomersPage';
import InventoryPage from './pages/InventoryPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'sales', element: <SalesPage /> },
      { path: 'products', element: <ProductsPage /> },
      { path: 'customers', element: <CustomersPage /> },
      { path: 'inventory', element: <InventoryPage /> },
    ],
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
