/**
 * API Client — ERP JWT remains supported; a linked Supabase session may also
 * authenticate requests. The backend maps Supabase subjects to ERP users.
 */
import {
  getActiveAuthProvider,
  getSupabaseAccessToken,
  hasSupabaseSession,
} from './supabaseAuth';

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
  const { authToken, preferErpToken = false, ...fetchOptions } = options;
  let token = authToken || null;
  if (!token && !preferErpToken) {
    const activeProvider = getActiveAuthProvider();
    const useSupabase = activeProvider === 'supabase'
      || (!activeProvider && hasSupabaseSession());

    if (useSupabase) {
      // Keep the selected provider even after explicit rejection clears its
      // session, so no unrelated ERP credential can silently take over.
      token = await getSupabaseAccessToken();
    } else if (typeof localStorage !== 'undefined') {
      token = localStorage.getItem('erp03_token');
    }
  } else if (!token && preferErpToken && typeof localStorage !== 'undefined') {
    token = localStorage.getItem('erp03_token');
  }

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...fetchOptions.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await res.json()
    : { message: await res.text() };

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
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload), preferErpToken: true }),
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload), preferErpToken: true }),
  me: (options = {}) => request('/auth/me', options),
  linkSupabase: (accessToken) => request('/auth/supabase/link', {
    method: 'POST',
    preferErpToken: true,
    body: JSON.stringify({ access_token: accessToken }),
  }),
  createBusiness: (payload) => request('/businesses', { method: 'POST', body: JSON.stringify(payload) }),
  listBusinesses: () => request('/businesses'),
  createSale: (payload) => request('/sales', { method: 'POST', body: JSON.stringify(payload) }),
  listSales: (params) => request(`/sales?${new URLSearchParams(params)}`),
  listProducts: (params) => request(`/products?${new URLSearchParams(params)}`),
  createProduct: (payload) => request('/products', { method: 'POST', body: JSON.stringify(payload) }),
  listCustomers: (params) => request(`/customers?${new URLSearchParams(params)}`),
  createCustomer: (payload) => request('/customers', { method: 'POST', body: JSON.stringify(payload) }),
  health: () => request('/healthz'),
};

export { ApiError };
