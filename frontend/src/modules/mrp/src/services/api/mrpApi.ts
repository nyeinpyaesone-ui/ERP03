import axios from 'axios';
import { env } from '../config/env';
import {
  BillOfMaterials,
  WorkOrder,
  ProductionPlan,
  MRPCalculation,
  ManufacturingKPI,
  WorkCenter,
  Routing,
} from '../types/mrp';

const api = axios.create({
  baseURL: `${env.apiUrl}/manufacturing`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use(async (config) => {
  const token = await getAuthToken(); // Your existing auth utility
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh or logout
    }
    return Promise.reject(error);
  }
);

// BOM APIs
export const bomAPI = {
  getAll: () => api.get<BillOfMaterials[]>('/boms').then((r) => r.data),
  getById: (id: string) => api.get<BillOfMaterials>(`/boms/${id}`).then((r) => r.data),
  create: (data: Omit<BillOfMaterials, 'id' | 'createdAt' | 'updatedAt'>) =>
    api.post<BillOfMaterials>('/boms', data).then((r) => r.data),
  update: (id: string, data: Partial<BillOfMaterials>) =>
    api.put<BillOfMaterials>(`/boms/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/boms/${id}`),
  getByProduct: (productId: string) =>
    api.get<BillOfMaterials[]>(`/boms/product/${productId}`).then((r) => r.data),
  getVersions: (productId: string) =>
    api.get<BillOfMaterials[]>(`/boms/product/${productId}/versions`).then((r) => r.data),
};

// Work Order APIs
export const workOrderAPI = {
  getAll: (params?: { status?: string; priority?: string; startDate?: string; endDate?: string }) =>
    api.get<WorkOrder[]>('/work-orders', { params }).then((r) => r.data),
  getById: (id: string) => api.get<WorkOrder>(`/work-orders/${id}`).then((r) => r.data),
  create: (data: Omit<WorkOrder, 'id' | 'orderNumber' | 'createdAt' | 'updatedAt' | 'progress'>) =>
    api.post<WorkOrder>('/work-orders', data).then((r) => r.data),
  update: (id: string, data: Partial<WorkOrder>) =>
    api.put<WorkOrder>(`/work-orders/${id}`, data).then((r) => r.data),
  updateStatus: (id: string, status: WorkOrder['status'], progress: number) =>
    api.patch<WorkOrder>(`/work-orders/${id}/status`, { status, progress }).then((r) => r.data),
  delete: (id: string) => api.delete(`/work-orders/${id}`),
  consumeMaterial: (id: string, consumption: { bomItemId: string; actualQuantity: number }) =>
    api.post(`/work-orders/${id}/consume`, consumption).then((r) => r.data),
  getByPlan: (planId: string) =>
    api.get<WorkOrder[]>(`/work-orders/plan/${planId}`).then((r) => r.data),
};

// Production Plan APIs
export const productionPlanAPI = {
  getAll: () => api.get<ProductionPlan[]>('/production-plans').then((r) => r.data),
  getById: (id: string) => api.get<ProductionPlan>(`/production-plans/${id}`).then((r) => r.data),
  create: (data: Omit<ProductionPlan, 'id' | 'planNumber' | 'createdAt' | 'updatedAt' | 'progress' | 'completedQuantity'>) =>
    api.post<ProductionPlan>('/production-plans', data).then((r) => r.data),
  update: (id: string, data: Partial<ProductionPlan>) =>
    api.put<ProductionPlan>(`/production-plans/${id}`, data).then((r) => r.data),
  approve: (id: string) =>
    api.patch<ProductionPlan>(`/production-plans/${id}/approve`).then((r) => r.data),
  delete: (id: string) => api.delete(`/production-plans/${id}`),
};

// MRP Calculation APIs
export const mrpAPI = {
  calculate: (params: { productIds?: string[]; period?: string; horizon?: number }) =>
    api.post<MRPCalculation[]>('/mrp/calculate', params).then((r) => r.data),
  getByProduct: (productId: string, period: string) =>
    api.get<MRPCalculation>(`/mrp/product/${productId}`, { params: { period } }).then((r) => r.data),
  getExplosion: (productId: string, quantity: number) =>
    api.post('/mrp/explosion', { productId, quantity }).then((r) => r.data),
};

// KPI APIs
export const manufacturingKPIAPI = {
  getDashboard: (period?: string) =>
    api.get<ManufacturingKPI>('/kpi/dashboard', { params: { period } }).then((r) => r.data),
  getEfficiency: (workCenterId?: string, period?: string) =>
    api.get('/kpi/efficiency', { params: { workCenterId, period } }).then((r) => r.data),
  getVariance: (period?: string) =>
    api.get('/kpi/variance', { params: { period } }).then((r) => r.data),
};

// Work Center APIs
export const workCenterAPI = {
  getAll: () => api.get<WorkCenter[]>('/work-centers').then((r) => r.data),
  getById: (id: string) => api.get<WorkCenter>(`/work-centers/${id}`).then((r) => r.data),
  updateLoad: (id: string, load: number) =>
    api.patch<WorkCenter>(`/work-centers/${id}/load`, { load }).then((r) => r.data),
};

// Routing APIs
export const routingAPI = {
  getAll: () => api.get<Routing[]>('/routings').then((r) => r.data),
  getByProduct: (productId: string) =>
    api.get<Routing>(`/routings/product/${productId}`).then((r) => r.data),
  create: (data: Omit<Routing, 'id'>) =>
    api.post<Routing>('/routings', data).then((r) => r.data),
};

// Helper function - replace with your actual auth token retrieval
async function getAuthToken(): Promise<string | null> {
  // Import from your existing auth utility
  return null;
}

