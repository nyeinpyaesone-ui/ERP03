export default function Dashboard({ user }) {
  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="user-info">
        <p>Welcome, {user.display_name}</p>
        <p>Business ID: {user.business_id}</p>
        <p>Branch ID: {user.branch_id || 'All Branches'}</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Today's Sales</h3>
          <p className="stat-value">—</p>
        </div>
        <div className="stat-card">
          <h3>Active Products</h3>
          <p className="stat-value">—</p>
        </div>
        <div className="stat-card">
          <h3>Low Stock Alerts</h3>
          <p className="stat-value">—</p>
        </div>
      </div>
    </div>
  );
}
