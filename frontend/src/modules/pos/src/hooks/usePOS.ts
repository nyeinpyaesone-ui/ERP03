import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  posProductAPI,
  posCategoryAPI,
  posSaleAPI,
  posShiftAPI,
  posRegisterAPI,
  posKPIAPI,
} from '../services/api/posApi';
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

// Product Hooks
export const usePOSProducts = (params?: Parameters<typeof posProductAPI.getAll>[0]) =>
  useQuery<POSProduct[]>({
    queryKey: ['posProducts', params],
    queryFn: () => posProductAPI.getAll(params),
  });

export const usePOSProductByBarcode = (barcode: string) =>
  useQuery<POSProduct>({
    queryKey: ['posProduct', barcode],
    queryFn: () => posProductAPI.getByBarcode(barcode),
    enabled: !!barcode,
  });

// Category Hooks
export const usePOSCategories = () =>
  useQuery<POSCategory[]>({
    queryKey: ['posCategories'],
    queryFn: () => posCategoryAPI.getAll(),
  });

// Sale Hooks
export const useCreateSale = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: posSaleAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posSales'] });
      queryClient.invalidateQueries({ queryKey: ['posKPI'] });
      queryClient.invalidateQueries({ queryKey: ['shiftHistory'] });
    },
  });
};

export const useSales = (params?: Parameters<typeof posSaleAPI.getAll>[0]) =>
  useQuery<POSSale[]>({
    queryKey: ['posSales', params],
    queryFn: () => posSaleAPI.getAll(params),
  });

export const useRefundSale = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ saleId, data }: { saleId: string; data: Parameters<typeof posSaleAPI.refund>[1] }) =>
      posSaleAPI.refund(saleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posSales'] });
      queryClient.invalidateQueries({ queryKey: ['posKPI'] });
    },
  });
};

// Shift Hooks
export const useOpenShift = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: posShiftAPI.open,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shiftHistory'] });
      queryClient.invalidateQueries({ queryKey: ['posKPI'] });
    },
  });
};

export const useCloseShift = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ shiftId, data }: { shiftId: string; data: Parameters<typeof posShiftAPI.close>[1] }) =>
      posShiftAPI.close(shiftId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shiftHistory'] });
      queryClient.invalidateQueries({ queryKey: ['posKPI'] });
    },
  });
};

export const useCurrentShift = (registerId: string) =>
  useQuery<POSShift>({
    queryKey: ['currentShift', registerId],
    queryFn: () => posShiftAPI.getCurrent(registerId),
    enabled: !!registerId,
  });

export const useShiftHistory = (params?: Parameters<typeof posShiftAPI.getHistory>[0]) =>
  useQuery<POSShift[]>({
    queryKey: ['shiftHistory', params],
    queryFn: () => posShiftAPI.getHistory(params),
  });

// Register Hooks
export const usePOSRegisters = () =>
  useQuery<POSRegister[]>({
    queryKey: ['posRegisters'],
    queryFn: () => posRegisterAPI.getAll(),
  });

// KPI Hooks
export const usePOSKPI = (registerId?: string, shiftId?: string) =>
  useQuery<POSKPI>({
    queryKey: ['posKPI', registerId, shiftId],
    queryFn: () => posKPIAPI.getDashboard(registerId, shiftId),
  });

