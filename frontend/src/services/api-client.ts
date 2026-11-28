/**
 * TypeScript API Client SDK for ERP03 backend.
 * Typed client for all backend endpoints.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

export interface RegisterRequest {
  business_code: string;
  business_name?: string;
  email: string;
  password: string;
  display_name: string;
  default_currency?: string;
  timezone?: string;
  locale?: string;
}

export interface RegisterResponse {
  business_id: string;
  user_id: string;
  message: string;
}

export interface LoginRequest {
  business_code: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: { id: string; email: string; display_name: string; business_id: string; branch_id?: string };
}

export interface MeResponse {
  id: string;
  email: string;
  display_name: string;
  business_id: string;
  branch_id?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface CreateSaleRequest {
  customer_id?: string;
  payment_method: string;
  items: Array<{ product_id: string; quantity: number; unit_price: number }>;
  idempotency_key: string;
}

export interface SaleResponse {
  id: string;
  invoice_no: string;
  status: string;
  total_amount: string;
  payment_method: string;
  created_at: string;
}

export interface ProductResponse {
  id: string;
  name: string;
  sku: string;
  price: string;
  stock_quantity: number;
  min_stock_level: number;
  is_active: boolean;
}

export interface CreateProductRequest {
  name: string;
  sku: string;
  price: number;
  stock_quantity?: number;
  min_stock_level?: number;
}

export interface CustomerResponse {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
}

export interface CreateCustomerRequest {
  name: string;
  email: string;
  phone: string;
  address: string;
}

export class Erp03ApiClient {
  private readonly client: AxiosInstance;

  constructor(baseURL: string = import.meta.env.VITE_API_BASE_URL || '/api') {
    this.client = axios.create({
      baseURL,
      headers: { 'Content-Type': 'application/json' },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('erp03_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('erp03_token');
        }
        return Promise.reject(error);
      }
    );
  }

  async register(payload: RegisterRequest): Promise<RegisterResponse> {
    const { data } = await this.client.post<RegisterResponse>('/auth/register', payload);
    return data;
  }

  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await this.client.post<LoginResponse>('/auth/login', payload);
    return data;
  }

  async me(): Promise<MeResponse> {
    const { data } = await this.client.get<MeResponse>('/auth/me');
    return data;
  }

  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>('/healthz');
    return data;
  }

  async createSale(payload: CreateSaleRequest): Promise<SaleResponse> {
    const { data } = await this.client.post<SaleResponse>('/sales', payload);
    return data;
  }

  async listSales(params?: { limit?: number; offset?: number; branch_id?: string }) {
    const { data } = await this.client.get('/sales', { params });
    return data;
  }

  async listProducts(params?: { limit?: number; offset?: number; low_stock_only?: boolean }) {
    const { data } = await this.client.get('/products', { params });
    return data;
  }

  async createProduct(payload: CreateProductRequest): Promise<ProductResponse> {
    const { data } = await this.client.post<ProductResponse>('/products', payload);
    return data;
  }

  async listCustomers(params?: { limit?: number; offset?: number }) {
    const { data } = await this.client.get('/customers', { params });
    return data;
  }

  async createCustomer(payload: CreateCustomerRequest): Promise<CustomerResponse> {
    const { data } = await this.client.post<CustomerResponse>('/customers', payload);
    return data;
  }
}

export const api = new Erp03ApiClient();
