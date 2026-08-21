import axios from 'axios';
import { env } from '../config/env';
import {
  POSProduct,
  POSCategory,
  POSSale,
  POSShift,
  POSRegister,
  POSKPI,
  Cart,
  Payment,
} from '../types/pos';

const api = axios.create({
  baseURL: `${env.apiUrl}/pos`,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Product APIs
export const posProductAPI = {
  getAll: (params?: { category?: string; search?: string; active?: boolean }) =>
    api.get<POSProduct[]>('/products', { params }).then((r) => r.data),
  getByBarcode: (barcode: string) =>
    api.get<POSProduct>(`/products/barcode/${barcode}`).then((r) => r.data),
  getById: (id: string) => api.get<POSProduct>(`/products/${id}`).then((r) => r.data),
  checkStock: (productId: string, quantity: number, variantId?: string) =>
    api.get(`/products/${productId}/stock`, { params: { quantity, variantId } }).then((r) => r.data),
};

// Category APIs
export const posCategoryAPI = {
  getAll: () => api.get<POSCategory[]>('/categories').then((r) => r.data),
  getById: (id: string) => api.get<POSCategory>(`/categories/${id}`).then((r) => r.data),
};

// Sale APIs
export const posSaleAPI = {
  create: (data: { cart: Cart; registerId: string; shiftId: string; customerId?: string }) =>
    api.post<POSSale>('/sales', data).then((r) => r.data),
  getAll: (params?: { shiftId?: string; registerId?: string; status?: string; dateFrom?: string; dateTo?: string }) =>
    api.get<POSSale[]>('/sales', { params }).then((r) => r.data),
  getById: (id: string) => api.get<POSSale>(`/sales/${id}`).then((r) => r.data),
  addPayment: (saleId: string, payment: Omit<Payment, 'id' | 'status' | 'processedAt'>) =>
    api.post<POSSale>(`/sales/${saleId}/payments`, payment).then((r) => r.data),
  completeSale: (saleId: string) =>
    api.patch<POSSale>(`/sales/${saleId}/complete`).then((r) => r.data),
  refund: (saleId: string, data: { amount: number; reason: string; items?: string[] }) =>
    api.post<POSSale>(`/sales/${saleId}/refund`, data).then((r) => r.data),
  cancel: (saleId: string, reason: string) =>
    api.patch<POSSale>(`/sales/${saleId}/cancel`, { reason }).then((r) => r.data),
  getReceipt: (saleId: string) =>
    api.get(`/sales/${saleId}/receipt`).then((r) => r.data),
  printReceipt: (saleId: string) =>
    api.post(`/sales/${saleId}/print-receipt`).then((r) => r.data),
};

// Shift APIs
export const posShiftAPI = {
  open: (data: { registerId: string; cashierId: string; openingAmount: number; notes?: string }) =>
    api.post<POSShift>('/shifts/open', data).then((r) => r.data),
  close: (shiftId: string, data: { closingAmount: number; countedAmount: number; notes?: string }) =>
    api.patch<POSShift>(`/shifts/${shiftId}/close`, data).then((r) => r.data),
  getCurrent: (registerId: string) =>
    api.get<POSShift>(`/shifts/current/${registerId}`).then((r) => r.data),
  getHistory: (params?: { cashierId?: string; registerId?: string; dateFrom?: string; dateTo?: string }) =>
    api.get<POSShift[]>('/shifts', { params }).then((r) => r.data),
  getById: (id: string) => api.get<POSShift>(`/shifts/${id}`).then((r) => r.data),
};

// Register APIs
export const posRegisterAPI = {
  getAll: () => api.get<POSRegister[]>('/registers').then((r) => r.data),
  getById: (id: string) => api.get<POSRegister>(`/registers/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<POSRegister>) =>
    api.put<POSRegister>(`/registers/${id}`, data).then((r) => r.data),
};

// KPI APIs
export const posKPIAPI = {
  getDashboard: (registerId?: string, shiftId?: string) =>
    api.get<POSKPI>('/kpi/dashboard', { params: { registerId, shiftId } }).then((r) => r.data),
  getDailyReport: (date: string, registerId?: string) =>
    api.get('/reports/daily', { params: { date, registerId } }).then((r) => r.data),
  getSalesReport: (params: { dateFrom: string; dateTo: string; groupBy?: 'day' | 'week' | 'month' | 'product' | 'category' }) =>
    api.get('/reports/sales', { params }).then((r) => r.data),
};

async function getAuthToken(): Promise<string | null> {
  return null;
}

