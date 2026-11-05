/**
 * API Client — typed fetch wrapper with auth token injection.
 * All requests go through /api which Vite proxies to the backend /api/v1.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request(path, options = {}) {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('erp03_token') : null;
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  let data;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await res.json();
  } else {
    data = { message: await res.text() };
  }

  if (!res.ok) {
    throw new ApiError(
      data.detail || data.message || `Request failed (${res.status})`,
      res.status,
      data
    );
  }

  return data;
}

export const api = {
  // Auth
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request('/auth/me'),

  // Business
  createBusiness: (payload) => request('/businesses', { method: 'POST', body: JSON.stringify(payload) }),
  listBusinesses: () => request('/businesses'),

  // Sales
  createSale: (payload) => request('/sales', { method: 'POST', body: JSON.stringify(payload) }),
  listSales: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/sales?${qs}`);
  },

  // Products
  listProducts: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/products?${qs}`);
  },
  createProduct: (payload) => request('/products', { method: 'POST', body: JSON.stringify(payload) }),

  // Customers
  listCustomers: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/customers?${qs}`);
  },
  createCustomer: (payload) => request('/customers', { method: 'POST', body: JSON.stringify(payload) }),

  // Health
  health: () => request('/healthz'),
};

export { ApiError };
