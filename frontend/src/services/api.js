/**
 * API Client — ERP JWT remains supported; a linked Supabase session may also
 * authenticate requests. The backend maps Supabase subjects to ERP users.
 */
import {
  getActiveAuthProvider,
  getSupabaseAccessToken,
  hasSupabaseSession,
  selectSupabaseProvider,
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
      // Persist legacy session provider choice before refresh can reject and
      // clear its credentials; never switch silently to a stored ERP token.
      if (activeProvider !== 'supabase') selectSupabaseProvider();
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
  createSale: (payload, idempotencyKey) => request('/sales', { method: 'POST', headers: { 'X-Idempotency-Key': idempotencyKey }, body: JSON.stringify(payload) }),
  listSales: (params = {}) => request(`/sales?${new URLSearchParams(params)}`),
  listOutstandingReceivables: (params = {}) => request(`/receivables/outstanding?${new URLSearchParams(params)}`),
  collectReceivable: (payload, idempotencyKey) => request('/receivables/collect', { method: 'POST', headers: { 'X-Idempotency-Key': idempotencyKey }, body: JSON.stringify(payload) }),
  getBusinessContext: () => request('/context'),
  getStockBalances: (params = {}) => request(`/inventory/stock?${new URLSearchParams(params)}`),
  getDashboardSummary: () => request('/dashboard/summary'),
  listProducts: (params) => request(`/products?${new URLSearchParams(params)}`),
  createProduct: (payload) => request('/products', { method: 'POST', body: JSON.stringify(payload) }),
  listCustomers: (params) => request(`/customers?${new URLSearchParams(params)}`),
  createCustomer: (payload) => request('/customers', { method: 'POST', body: JSON.stringify(payload) }),
  health: () => request('/healthz'),
};

export { ApiError };
