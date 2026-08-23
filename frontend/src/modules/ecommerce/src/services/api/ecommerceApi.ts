import axios from 'axios';
import { env } from '../config/env';
import {
  StoreProduct,
  StoreCategory,
  StoreCart,
  StoreOrder,
  Customer,
  CustomerAddress,
  ProductReview,
  WishlistItem,
  StoreCoupon,
  EcommerceKPI,
  ShippingMethod,
  SearchFilters,
} from '../types/ecommerce';

const api = axios.create({
  baseURL: `${env.apiUrl}/ecommerce`,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Product APIs
export const ecommerceProductAPI = {
  getAll: (params?: { category?: string; featured?: boolean; new?: boolean; search?: string; page?: number; limit?: number }) =>
    api.get<{ products: StoreProduct[]; total: number; page: number; totalPages: number }>('/products', { params }).then((r) => r.data),
  getBySlug: (slug: string) =>
    api.get<StoreProduct>(`/products/slug/${slug}`).then((r) => r.data),
  getById: (id: string) =>
    api.get<StoreProduct>(`/products/${id}`).then((r) => r.data),
  getRelated: (productId: string, limit?: number) =>
    api.get<StoreProduct[]>(`/products/${productId}/related`, { params: { limit } }).then((r) => r.data),
  getReviews: (productId: string, params?: { page?: number; limit?: number; status?: string }) =>
    api.get<{ reviews: ProductReview[]; total: number; averageRating: number }>(`/products/${productId}/reviews`, { params }).then((r) => r.data),
  addReview: (productId: string, data: Omit<ProductReview, 'id' | 'isVerifiedPurchase' | 'helpfulCount' | 'notHelpfulCount' | 'status' | 'reply' | 'createdAt' | 'updatedAt'>) =>
    api.post<ProductReview>(`/products/${productId}/reviews`, data).then((r) => r.data),
};

// Category APIs
export const ecommerceCategoryAPI = {
  getAll: () => api.get<StoreCategory[]>('/categories').then((r) => r.data),
  getBySlug: (slug: string) =>
    api.get<StoreCategory>(`/categories/slug/${slug}`).then((r) => r.data),
  getById: (id: string) =>
    api.get<StoreCategory>(`/categories/${id}`).then((r) => r.data),
  getProducts: (categoryId: string, params?: { page?: number; limit?: number; sort?: string }) =>
    api.get<{ products: StoreProduct[]; total: number; page: number }>(`/categories/${categoryId}/products`, { params }).then((r) => r.data),
};

// Cart APIs
export const ecommerceCartAPI = {
  get: (sessionId: string) =>
    api.get<StoreCart>(`/cart`, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  addItem: (sessionId: string, data: { productId: string; variantId?: string; quantity: number }) =>
    api.post<StoreCart>(`/cart/items`, data, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  updateItem: (sessionId: string, itemId: string, quantity: number) =>
    api.put<StoreCart>(`/cart/items/${itemId}`, { quantity }, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  removeItem: (sessionId: string, itemId: string) =>
    api.delete<StoreCart>(`/cart/items/${itemId}`, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  clear: (sessionId: string) =>
    api.delete<StoreCart>(`/cart`, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  applyCoupon: (sessionId: string, couponCode: string) =>
    api.post<StoreCart>(`/cart/coupon`, { code: couponCode }, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  removeCoupon: (sessionId: string) =>
    api.delete<StoreCart>(`/cart/coupon`, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  setShipping: (sessionId: string, methodId: string) =>
    api.post<StoreCart>(`/cart/shipping`, { methodId }, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
};

// Order APIs
export const ecommerceOrderAPI = {
  create: (sessionId: string, data: {
    shippingAddress: CustomerAddress;
    billingAddress: CustomerAddress;
    shippingMethodId: string;
    paymentMethod: string;
    customerNotes?: string;
    customerId?: string;
  }) =>
    api.post<StoreOrder>(`/orders`, data, { headers: { 'X-Session-Id': sessionId } }).then((r) => r.data),
  getAll: (params?: { status?: string; customerId?: string; page?: number; limit?: number }) =>
    api.get<{ orders: StoreOrder[]; total: number; page: number }>('/orders', { params }).then((r) => r.data),
  getById: (id: string) =>
    api.get<StoreOrder>(`/orders/${id}`).then((r) => r.data),
  getByNumber: (number: string) =>
    api.get<StoreOrder>(`/orders/number/${number}`).then((r) => r.data),
  cancel: (id: string, reason: string) =>
    api.patch<StoreOrder>(`/orders/${id}/cancel`, { reason }).then((r) => r.data),
  requestRefund: (id: string, data: { items: string[]; reason: string }) =>
    api.post<StoreOrder>(`/orders/${id}/refund`, data).then((r) => r.data),
  track: (id: string) =>
    api.get(`/orders/${id}/tracking`).then((r) => r.data),
};

// Customer APIs
export const ecommerceCustomerAPI = {
  getProfile: () => api.get<Customer>('/customers/me').then((r) => r.data),
  updateProfile: (data: Partial<Customer>) =>
    api.put<Customer>('/customers/me', data).then((r) => r.data),
  getOrders: (params?: { page?: number; limit?: number }) =>
    api.get<{ orders: StoreOrder[]; total: number; page: number }>('/customers/me/orders', { params }).then((r) => r.data),
  getAddresses: () =>
    api.get<CustomerAddress[]>('/customers/me/addresses').then((r) => r.data),
  addAddress: (data: Omit<CustomerAddress, 'id'>) =>
    api.post<CustomerAddress>('/customers/me/addresses', data).then((r) => r.data),
  updateAddress: (id: string, data: Partial<CustomerAddress>) =>
    api.put<CustomerAddress>(`/customers/me/addresses/${id}`, data).then((r) => r.data),
  deleteAddress: (id: string) =>
    api.delete(`/customers/me/addresses/${id}`),
  setDefaultAddress: (id: string, type: 'shipping' | 'billing') =>
    api.patch(`/customers/me/addresses/${id}/default`, { type }).then((r) => r.data),
};

// Wishlist APIs
export const ecommerceWishlistAPI = {
  get: () => api.get<WishlistItem[]>('/wishlist').then((r) => r.data),
  add: (productId: string) =>
    api.post<WishlistItem>('/wishlist', { productId }).then((r) => r.data),
  remove: (itemId: string) =>
    api.delete(`/wishlist/${itemId}`),
  clear: () => api.delete('/wishlist'),
};

// Coupon APIs
export const ecommerceCouponAPI = {
  validate: (code: string, cartTotal: number) =>
    api.post<StoreCoupon>('/coupons/validate', { code, cartTotal }).then((r) => r.data),
};

// Shipping APIs
export const ecommerceShippingAPI = {
  getMethods: (params?: { country?: string; postalCode?: string; weight?: number }) =>
    api.get<ShippingMethod[]>('/shipping/methods', { params }).then((r) => r.data),
  calculate: (data: { items: { productId: string; quantity: number }[]; shippingAddress: CustomerAddress; methodId: string }) =>
    api.post('/shipping/calculate', data).then((r) => r.data),
};

// Search API
export const ecommerceSearchAPI = {
  search: (query: string, filters?: SearchFilters, page?: number, limit?: number) =>
    api.get<{ products: StoreProduct[]; total: number; page: number; facets: any }>('/search', {
      params: { q: query, ...filters, page, limit },
    }).then((r) => r.data),
};

// KPI APIs
export const ecommerceKPIAPI = {
  getDashboard: (period?: 'today' | 'week' | 'month') =>
    api.get<EcommerceKPI>('/kpi/dashboard', { params: { period } }).then((r) => r.data),
  getSalesReport: (params: { dateFrom: string; dateTo: string; groupBy?: 'day' | 'week' | 'month' | 'product' | 'category' }) =>
    api.get('/reports/sales', { params }).then((r) => r.data),
};

async function getAuthToken(): Promise<string | null> {
  return null;
}

