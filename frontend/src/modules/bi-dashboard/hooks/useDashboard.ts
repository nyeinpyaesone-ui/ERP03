import { useState, useEffect, useCallback, useRef } from 'react';
import {
  DashboardSummary,
  RevenueAnalytics,
  KPIMetrics,
  ChartData,
  ActivityItem,
  TopProduct,
  TopCustomer,
  DashboardFilter,
  ForecastData,
  AIInsight,
  InventoryStats,
} from '../types/dashboard';

const API_BASE = 'https://api.erp03.com/v1';

const useApi = <T>(endpoint: string, params?: Record<string, string>) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const queryParams = params ? new URLSearchParams(params).toString() : '';
      const url = `${API_BASE}${endpoint}${queryParams ? `?${queryParams}` : ''}`;

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${getToken()}`,
          'Content-Type': 'application/json',
        },
        signal: abortRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      setData(result);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [endpoint, JSON.stringify(params)]);

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

const getToken = (): string => {
  // Replace with your actual token retrieval logic
  return (globalThis as any).__ERP_TOKEN__ || '';
};

export const useDashboardSummary = (filter: DashboardFilter) => {
  return useApi<DashboardSummary>('/dashboard/summary', {
    period: filter.period,
    compareWith: filter.compareWith,
  });
};

export const useRevenueAnalytics = (period: string) => {
  return useApi<RevenueAnalytics>('/dashboard/revenue', {
    period,
    groupBy: 'daily',
  });
};

export const useKPIMetrics = (period: string) => {
  return useApi<KPIMetrics>('/dashboard/kpis', { period });
};

export const useSalesChart = (period: string = '30d') => {
  return useApi<ChartData>('/dashboard/charts/sales', { period });
};

export const useInventoryChart = () => {
  return useApi<ChartData>('/dashboard/charts/inventory');
};

export const useCustomerChart = (period: string = '30d') => {
  return useApi<ChartData>('/dashboard/charts/customers', { period });
};

export const useActivities = (limit: number = 20, type: string = 'all') => {
  return useApi<ActivityItem[]>('/dashboard/activities', {
    limit: String(limit),
    type,
  });
};

export const useTopProducts = (period: string = 'this_month', limit: number = 10) => {
  return useApi<TopProduct[]>('/dashboard/top-products', {
    period,
    limit: String(limit),
  });
};

export const useTopCustomers = (period: string = 'this_month', limit: number = 10) => {
  return useApi<TopCustomer[]>('/dashboard/top-customers', {
    period,
    limit: String(limit),
  });
};

export const useSalesForecast = (horizon: string = '30d') => {
  return useApi<ForecastData>('/ai/forecast', {
    type: 'sales',
    horizon,
  });
};

export const useAIInsights = (limit: number = 5) => {
  return useApi<AIInsight[]>('/ai/insights', {
    type: 'all',
    limit: String(limit),
  });
};

export const useInventoryStats = () => {
  return useApi<InventoryStats>('/inventory/stats');
};

export const useAnomalyDetection = () => {
  return useApi<Array<{ id: string; module: string; metric: string; severity: string; description: string }>>(
    '/ai/anomaly-detection',
    { module: 'all', sensitivity: 'medium' }
  );
};

export const useDashboardRefresh = (interval: number = 300000) => {
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setLastRefresh(new Date());
    }, interval);

    return () => clearInterval(timer);
  }, [interval]);

  return lastRefresh;
};

export const usePeriodFilter = () => {
  const [filter, setFilter] = useState<DashboardFilter>({
    period: 'this_month',
    compareWith: 'previous_period',
  });

  const setPeriod = useCallback((period: string) => {
    setFilter(prev => ({ ...prev, period }));
  }, []);

  const setCompareWith = useCallback((compareWith: 'previous_period' | 'previous_year') => {
    setFilter(prev => ({ ...prev, compareWith }));
  }, []);

  return { filter, setPeriod, setCompareWith, setFilter };
};
