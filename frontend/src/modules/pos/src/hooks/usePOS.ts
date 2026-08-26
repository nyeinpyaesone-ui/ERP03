import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  posProductAPI,
  posCategoryAPI,
  posSaleAPI,
  posShiftAPI,
  posRegisterAPI,
  posKPIAPI,
} from '../services/api/posApi';
import type {
  POSProduct,
  POSCategory,
  POSSale,
  POSShift,
  POSRegister,
  POSKPI,
  Cart,
  Payment,
} from '../types/pos';

/**
 * POS Module Query Hooks
 * Enterprise-grade hooks using React Query with standardized patterns
 */

// Product Hooks
export const usePOSProducts = (params?: Parameters<typeof posProductAPI.getAll>[0]) =>
  useQuery<POSProduct[]>({
    queryKey: ['pos', 'products', params],
    queryFn: () => posProductAPI.getAll(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });

export const usePOSProductByBarcode = (barcode: string) =>
  useQuery<POSProduct>({
    queryKey: ['pos', 'product', barcode],
    queryFn: () => posProductAPI.getByBarcode(barcode),
    enabled: !!barcode,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });

// Category Hooks
export const usePOSCategories = () =>
  useQuery<POSCategory[]>({
    queryKey: ['pos', 'categories'],
    queryFn: () => posCategoryAPI.getAll(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 3,
  });

// Sale Hooks
export const useCreateSale = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: posSaleAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pos', 'sales'] });
      queryClient.invalidateQueries({ queryKey: ['pos', 'kpi'] });
      queryClient.invalidateQueries({ queryKey: ['pos', 'shifts', 'history'] });
    },
    retry: 1,
  });
};

export const useSales = (params?: Parameters<typeof posSaleAPI.getAll>[0]) =>
  useQuery<POSSale[]>({
    queryKey: ['pos', 'sales', params],
    queryFn: () => posSaleAPI.getAll(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
  });

export const useRefundSale = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ saleId, data }: { saleId: string; data: Parameters<typeof posSaleAPI.refund>[1] }) =>
      posSaleAPI.refund(saleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pos', 'sales'] });
      queryClient.invalidateQueries({ queryKey: ['pos', 'kpi'] });
    },
    retry: 1,
  });
};

// Shift Hooks
export const useOpenShift = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: posShiftAPI.open,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pos', 'shifts', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['pos', 'kpi'] });
    },
    retry: 1,
  });
};

export const useCloseShift = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ shiftId, data }: { shiftId: string; data: Parameters<typeof posShiftAPI.close>[1] }) =>
      posShiftAPI.close(shiftId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pos', 'shifts', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['pos', 'kpi'] });
    },
    retry: 1,
  });
};

export const useCurrentShift = (registerId: string) =>
  useQuery<POSShift>({
    queryKey: ['pos', 'shifts', 'current', registerId],
    queryFn: () => posShiftAPI.getCurrent(registerId),
    enabled: !!registerId,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    retry: 3,
  });

export const useShiftHistory = (params?: Parameters<typeof posShiftAPI.getHistory>[0]) =>
  useQuery<POSShift[]>({
    queryKey: ['pos', 'shifts', 'history', params],
    queryFn: () => posShiftAPI.getHistory(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });

// Register Hooks
export const usePOSRegisters = () =>
  useQuery<POSRegister[]>({
    queryKey: ['pos', 'registers'],
    queryFn: () => posRegisterAPI.getAll(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 3,
  });

// KPI Hooks
export const usePOSKPI = (registerId?: string, shiftId?: string) =>
  useQuery<POSKPI>({
    queryKey: ['pos', 'kpi', registerId, shiftId],
    queryFn: () => posKPIAPI.getDashboard(registerId, shiftId),
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    retry: 3,
  });

