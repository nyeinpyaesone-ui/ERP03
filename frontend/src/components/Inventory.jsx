export default function Inventory({ token }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      // TODO: Implement inventory endpoint
      setProducts([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading inventory...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="inventory">
      <h2>Inventory Management</h2>

      <div className="inventory-actions">
        <button onClick={fetchInventory}>Refresh</button>
        <button>Add Product</button>
      </div>

      <table className="inventory-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Stock</th>
            <th>Price</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {products.length === 0 ? (
            <tr>
              <td colSpan={5}>No products in inventory</td>
            </tr>
          ) : (
            products.map((p) => (
              <tr key={p.id}>
                <td>{p.sku}</td>
                <td>{p.name}</td>
                <td>{p.quantity}</td>
                <td>{p.sale_price} MMK</td>
                <td>
                  {p.quantity > p.min_stock ? 'In Stock' : 'Low Stock'}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
