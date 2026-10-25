import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export default function Sales({ token }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [branchId, setBranchId] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    // TODO: Implement products endpoint
    setProducts([]);
  };

  const addToCart = (product) => {
    const existing = cart.find((item) => item.id === product.id);
    if (existing) {
      setCart(
        cart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      );
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const updateQuantity = (id, quantity) => {
    if (quantity <= 0) {
      setCart(cart.filter((item) => item.id !== id));
    } else {
      setCart(
        cart.map((item) =>
          item.id === id ? { ...item, quantity } : item
        )
      );
    }
  };

  const createSale = async () => {
    setLoading(true);
    setError('');

    try {
      const idempotencyKey = crypto.randomUUID();
      const total = cart.reduce(
        (sum, item) => sum + item.sale_price * item.quantity,
        0
      );

      const res = await fetch(`${API_BASE}/sales`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({
          branch_id: branchId,
          warehouse_id: warehouseId,
          invoice_no: `INV-${Date.now()}`,
          currency: 'MMK',
          lines: cart.map((item) => ({
            product_id: item.id,
            quantity: item.quantity,
            unit_price: item.sale_price,
          })),
          payments: [
            {
              method: 'cash',
              amount: total.toFixed(2),
              currency: 'MMK',
            },
          ],
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Sale failed');
      }

      alert('Sale created successfully!');
      setCart([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const total = cart.reduce(
    (sum, item) => sum + item.sale_price * item.quantity,
    0
  );

  return (
    <div className="sales">
      <h2>Point of Sale</h2>
      {error && <div className="error">{error}</div>}

      <div className="sale-setup">
        <label>
          Branch ID
          <input
            type="text"
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            placeholder="Enter branch UUID"
          />
        </label>
        <label>
          Warehouse ID
          <input
            type="text"
            value={warehouseId}
            onChange={(e) => setWarehouseId(e.target.value)}
            placeholder="Enter warehouse UUID"
          />
        </label>
      </div>

      <div className="pos-layout">
        <div className="product-grid">
          <h3>Products</h3>
          {products.length === 0 ? (
            <p>No products available. Add products to inventory first.</p>
          ) : (
            products.map((p) => (
              <button
                key={p.id}
                onClick={() => addToCart(p)}
                className="product-card"
              >
                <span className="product-name">{p.name}</span>
                <span className="product-price">{p.sale_price} MMK</span>
              </button>
            ))
          )}
        </div>

        <div className="cart">
          <h3>Cart</h3>
          {cart.length === 0 ? (
            <p>Cart is empty</p>
          ) : (
            <>
              {cart.map((item) => (
                <div key={item.id} className="cart-item">
                  <span>{item.name}</span>
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) =>
                      updateQuantity(item.id, parseInt(e.target.value))
                    }
                  />
                  <span>{(item.sale_price * item.quantity).toFixed(2)} MMK</span>
                </div>
              ))}
              <div className="cart-total">
                <strong>Total: {total.toFixed(2)} MMK</strong>
              </div>
              <button
                onClick={createSale}
                disabled={
                  loading ||
                  cart.length === 0 ||
                  !branchId ||
                  !warehouseId
                }
                className="checkout-btn"
              >
                {loading ? 'Processing...' : 'Complete Sale'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
