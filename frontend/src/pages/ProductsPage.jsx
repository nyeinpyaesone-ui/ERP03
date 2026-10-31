import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { ProductsList } from "../components/products/ProductsList";
import { ProductsCreate } from "../components/products/ProductsCreate";

export default function ProductsPage() {
  const { token, isAuthenticated, logout } = useAuth();
  const [showCreate, setShowCreate] = useState(false);

  // Demo token — replace with real login flow in production.
  // In production, obtain this from /api/v1/auth/login and store it.
  const DEMO_TOKEN = import.meta.env.VITE_DEMO_TOKEN || null;

  if (!isAuthenticated && !DEMO_TOKEN) {
    return (
      <div style={{ padding: "var(--erp-space-10)", maxWidth: 420, margin: "0 auto" }}>
        <h2>Authentication required</h2>
        <p>Set VITE_DEMO_TOKEN env var or sign in to access the product catalog.</p>
        <button onClick={logout} style={{ marginTop: "var(--erp-space-4)" }}>
          Sign out
        </button>
      </div>
    );
  }

  const authToken = token || DEMO_TOKEN;

  return (
    <div className="products-page">
      <header className="page-header">
        <div className="page-header__brand">
          <span className="brand-mark">E</span>
          <div>
            <span className="brand-name">ERP03</span>
            <span className="brand-sub">Product Catalog · Production Control Plane</span>
          </div>
        </div>
        <div className="page-header__actions">
          <button onClick={logout} className="header-signout">
            Sign out
          </button>
        </div>
      </header>

      <main className="page-main">
        {showCreate ? (
          <ProductsCreate
            token={authToken}
            branchId={import.meta.env.VITE_DEMO_BRANCH_ID || "00000000-0000-0000-0000-000000000000"}
            onCancel={() => setShowCreate(false)}
            onSuccess={() => setShowCreate(false)}
          />
        ) : (
          <ProductsList
            token={authToken}
            businessId={import.meta.env.VITE_DEMO_BUSINESS_ID || "00000000-0000-0000-0000-000000000000"}
            onAdd={() => setShowCreate(true)}
          />
        )}
      </main>
    </div>
  );
}
