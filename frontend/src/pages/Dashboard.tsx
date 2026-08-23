import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading dashboard data
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '100px' }}>
        <span className="loading" style={{ width: '40px', height: '40px' }}></span>
      </div>
    );
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '24px' }}>Dashboard</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginBottom: '12px' }}>Inventory</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>Manage your inventory items</p>
          <Link to="/inventory" className="btn btn-primary">View Inventory</Link>
        </div>

        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginBottom: '12px' }}>Users</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>Manage system users</p>
          <button className="btn btn-primary" disabled>Coming Soon</button>
        </div>

        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginBottom: '12px' }}>Reports</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>View analytics and reports</p>
          <button className="btn btn-primary" disabled>Coming Soon</button>
        </div>
      </div>
    </div>
  );
}
