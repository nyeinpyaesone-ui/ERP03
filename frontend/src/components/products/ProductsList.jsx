import { Search, Plus, RefreshCw, X, CheckCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { SearchInput } from "../ui/SearchInput";
import { Pagination } from "../ui/Pagination";
import { Table, TBody, THead, TH, TR, TD } from "../ui/Table";
import { catalogApi } from "../../api/catalog";

const STATUS_LABELS = { true: "Active", false: "Inactive" };

export function ProductsList({ token, businessId, onAdd }) {
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const abortRef = useRef(null);

  const fetchProducts = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setLoading(true);
    setError(null);
    try {
      const pageData = await catalogApi.listProducts({
        businessId,
        search,
        includeInactive,
        limit: pageSize,
        offset: (page - 1) * pageSize,
        token,
      });
      setProducts(pageData.items);
      setTotal(pageData.total);
    } catch (err) {
      if (err.name === "AbortError") return;
      setError(err.message);
      setToast({ kind: "danger", message: err.message || "Failed to load products" });
      setTimeout(() => setToast(null), 5000);
    } finally {
      setLoading(false);
    }
  }, [businessId, search, includeInactive, pageSize, page, token]);

  const handleToggleActive = async (product) => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || "/api"}/products/${product.id}/active`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            business_id: String(businessId),
          },
          body: JSON.stringify({ active: !product.active }),
        }
      );
      if (!res.ok) throw new Error("Failed to toggle product status");
      setToast({
        kind: "success",
        message: `Product marked ${!product.active ? "active" : "inactive"}`,
      });
      setTimeout(() => setToast(null), 4000);
      await fetchProducts();
    } catch (err) {
      setToast({ kind: "danger", message: err.message || "Toggle failed" });
      setTimeout(() => setToast(null), 5000);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const money = (n) =>
    n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <Card padded>
      <div className="list-header">
        <div>
          <h2 className="list-title">Products</h2>
          <p className="list-subtitle">Manage your master product catalog.</p>
        </div>
        <div className="list-actions">
          <Button variant="ghost" size="sm" onClick={fetchProducts}>
            <RefreshCw size={16} />
          </Button>
          {onAdd ? (
            <Button variant="primary" size="sm" onClick={onAdd}>
              <Plus size={16} /> Add product
            </Button>
          ) : null}
        </div>
      </div>

      {toast && (
        <div className={`toast toast--${toast.kind}`} role="alert">
          <div className="toast__icon">
            {toast.kind === "success" ? (
              <CheckCircle size={18} color="#16794c" />
            ) : (
              <X size={18} color="#b42318" />
            )}
          </div>
          <span>{toast.message}</span>
          <button className="toast__dismiss" onClick={() => setToast(null)} aria-label="Dismiss">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="list-controls">
        <SearchInput
          value={search}
          onChange={(v) => setSearch(v)}
          placeholder="Search products by SKU or name…"
        />
        <label style={{ display: "flex", alignItems: "center", gap: "var(--erp-space-2)", fontSize: "var(--erp-text-sm)", color: "var(--erp-text-muted)" }}>
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Show inactive
        </label>
      </div>

      {error && (
        <div className="alert alert--danger">{error}</div>
      )}

      <div className="table-section">
        <Table>
          <THead>
            <TR>
              <TH>SKU</TH>
              <TH>Name</TH>
              <TH>Unit</TH>
              <TH className="numeric">Sale price</TH>
              <TH className="numeric">Min stock</TH>
              <TH>Status</TH>
              <TH className="actions">Actions</TH>
            </TR>
          </THead>
          <TBody>
            {loading ? (
              <TR>
                <TD colSpan={7} className="skeleton-row">
                  <div className="skeleton skeleton-text lg" style={{ width: "55%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "35%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "15%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "20%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "20%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "18%" }} />
                  <div className="skeleton skeleton-text" style={{ width: "28%" }} />
                </TD>
              </TR>
            ) : products.length === 0 ? (
              <TR>
                <TD colSpan={7} className="empty-row">
                  {search || includeInactive ? (
                    <>
                      No products match your filters.
                      <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setIncludeInactive(false); }}>
                        Reset filters
                      </Button>
                    </>
                  ) : (
                    <>
                      No products yet.{" "}
                      <Button variant="primary" size="sm" onClick={onAdd}>
                        Add your first product
                      </Button>
                    </>
                  )}
                </TD>
              </TR>
            ) : (
              products.map((p) => (
                <TR key={p.id}>
                  <TD className="sku">{p.sku}</TD>
                  <TD>{p.name}</TD>
                  <TD>{p.unit}</TD>
                  <TD className="numeric">{money(p.sale_price)}</TD>
                  <TD className="numeric">{money(p.min_stock)}</TD>
                  <TD>
                    <Badge variant={p.active ? "success" : "neutral"}>
                      {STATUS_LABELS[p.active]}
                    </Badge>
                  </TD>
                  <TD className="actions">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleActive(p)}
                      aria-label={p.active ? "Mark inactive" : "Mark active"}
                    >
                      {p.active ? <X size={16} color="#b42318" /> : <CheckCircle size={16} color="#16794c" />}
                    </Button>
                  </TD>
                </TR>
              ))
            )}
          </TBody>
        </Table>
      </div>

      {total > 0 && (
        <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
      )}
    </Card>
  );
}
