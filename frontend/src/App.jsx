import { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function App() {
  const [health, setHealth] = useState('checking');

  useEffect(() => {
    fetch(`${API_BASE}/healthz`)
      .then((response) => {
        if (!response.ok) throw new Error('unhealthy');
        setHealth('online');
      })
      .catch(() => setHealth('offline'));
  }, []);

  return (
    <main className="shell">
      <section className="card" aria-labelledby="title">
        <p className="eyebrow">ERP03 · CONTROL PLANE</p>
        <h1 id="title">Enterprise Resource Planning</h1>
        <p className="subtitle">Production-focused modular ERP foundation.</p>
        <div className={`status ${health}`} role="status">
          <span aria-hidden="true" /> API {health}
        </div>
      </section>
    </main>
  );
}
