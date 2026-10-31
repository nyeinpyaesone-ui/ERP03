import { useState, useCallback } from "react";
import { ArrowLeft, Minus, CheckCircle, X } from "lucide-react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Card } from "../ui/Card";
import { catalogApi } from "../../api/catalog";

const INITIAL = {
  sku: "",
  barcode: "",
  name: "",
  unit: "pcs",
  sale_price: "",
  cost_price: "",
  min_stock: "",
};

const money = (n) =>
  n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function ProductsCreate({ token, branchId, onCancel, onSuccess }) {
  const [form, setForm] = useState({ ...INITIAL });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  const setField = useCallback((name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => { const next = { ...prev }; delete next[name]; return next; });
    }
  }, [errors]);

  const validate = useCallback(() => {
    const next = {};
    if (!form.sku.trim()) next.sku = "SKU is required";
    else if (form.sku.length > 80) next.sku = "SKU too long (max 80)";
    if (!form.name.trim()) next.name = "Product name is required";
    else if (form.name.length > 240) next.name = "Name too long (max 240)";
    const sale = Number(form.sale_price);
    if (form.sale_price === "" || Number.isNaN(sale) || sale < 0)
      next.sale_price = "Enter a valid sale price (≥ 0)";
    const cost = Number(form.cost_price);
    if (form.cost_price !== "" && (Number.isNaN(cost) || cost < 0))
      next.cost_price = "Enter a valid cost (≥ 0)";
    const min = Number(form.min_stock);
    if (form.min_stock !== "" && (Number.isNaN(min) || min < 0))
      next.min_stock = "Enter a valid min stock (≥ 0)";
    setErrors(next);
    return Object.keys(next).length === 0;
  }, [form]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      await catalogApi.createProduct({
        branchId,
        sku: form.sku.trim(),
        barcode: form.barcode.trim() || null,
        name: form.name.trim(),
        unit: form.unit,
        salePrice: Number(form.sale_price),
        costPrice: form.cost_price === "" ? 0 : Number(form.cost_price),
        minStock: form.min_stock === "" ? 0 : Number(form.min_stock),
        token,
      });
      setToast({ kind: "success", message: "Product created successfully" });
      setTimeout(() => setToast(null), 4000);
      setForm({ ...INITIAL });
      setErrors({});
      onSuccess?.();
    } catch (err) {
      if (err.code === "CONFLICT") {
        setErrors((prev) => ({ ...prev, sku: "SKU already exists for this business" }));
      } else {
        setToast({ kind: "danger", message: err.message || "Failed to create product" });
        setTimeout(() => setToast(null), 5000);
      }
    } finally {
      setSubmitting(false);
    }
  }, [form, validate, branchId, token, onSuccess]);

  return (
    <Card padded>
      <div className="list-header">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          <ArrowLeft size={16} /> Back to products
        </Button>
      </div>

      <div className="create-form">
        <h2 className="list-title">New product</h2>
        <p className="list-subtitle">Register a product in the master catalog.</p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--erp-space-5)" }}>
          <div className="field">
            <label>SKU <span style={{ color: "var(--erp-danger)" }}>*</span></label>
            <Input
              value={form.sku}
              onChange={(e) => setField("sku", e.target.value)}
              error={errors.sku}
              placeholder="e.g. SKU-1001"
            />
          </div>
          <div className="field">
            <label>Barcode</label>
            <Input
              value={form.barcode}
              onChange={(e) => setField("barcode", e.target.value)}
              placeholder="e.g. 8901234567890"
            />
          </div>
          <div className="field">
            <label>Product name <span style={{ color: "var(--erp-danger)" }}>*</span></label>
            <Input
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
              error={errors.name}
              placeholder="e.g. Premium Basmati Rice 5kg"
            />
          </div>
          <div className="field">
            <label>Unit</label>
            <Input
              value={form.unit}
              onChange={(e) => setField("unit", e.target.value)}
              placeholder="pcs"
            />
          </div>
          <div className="field">
            <label>Sale price <span style={{ color: "var(--erp-danger)" }}>*</span></label>
            <div className="price-input">
              <span className="price-prefix">MMK</span>
              <Input
                value={form.sale_price}
                onChange={(e) => setField("sale_price", e.target.value)}
                error={errors.sale_price}
                placeholder="0.00"
              />
            </div>
          </div>
          <div className="field">
            <label>Cost price</label>
            <div className="price-input">
              <span className="price-prefix">MMK</span>
              <Input
                value={form.cost_price}
                onChange={(e) => setField("cost_price", e.target.value)}
                error={errors.cost_price}
                placeholder="0.00"
              />
            </div>
          </div>
          <div className="field">
            <label>Minimum stock</label>
            <div className="price-input">
              <Minus size={16} className="input-icon" />
              <Input
                value={form.min_stock}
                onChange={(e) => setField("min_stock", e.target.value)}
                error={errors.min_stock}
                placeholder="0"
              />
            </div>
          </div>
          <div style={{ gridColumn: "1 / -1", display: "flex", gap: "var(--erp-space-3)", justifyContent: "flex-end" }}>
            <Button variant="ghost" type="button" onClick={() => setForm({ ...INITIAL })}>
              Reset
            </Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? (
                <span style={{ display: "flex", alignItems: "center", gap: "var(--erp-space-2)" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
                  Creating…
                </span>
              ) : "Create product"}
            </Button>
          </div>
        </form>

        {toast && (
          <div className={`toast toast--${toast.kind}`} role="alert" style={{ marginTop: "var(--erp-space-5)" }}>
            {toast.kind === "success" ? <CheckCircle size={18} color="#16794c" /> : <X size={18} color="#b42318" />}
            <span>{toast.message}</span>
            <button className="toast__dismiss" onClick={() => setToast(null)} aria-label="Dismiss">
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </Card>
  );
}
