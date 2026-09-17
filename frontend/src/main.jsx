import React from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  return <main><h1>ERP03</h1><p>Production ERP control plane</p></main>;
}

createRoot(document.getElementById('root')).render(<App />);
