import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  bomAPI,
  workOrderAPI,
  productionPlanAPI,
  mrpAPI,
  manufacturingKPIAPI,
  workCenterAPI,
} from '../services/api/mrpApi';
import {
  BillOfMaterials,
  WorkOrder,
  ProductionPlan,
  MRPCalculation,
  ManufacturingKPI,
  WorkCenter,
} from '../types/mrp';

// BOM Hooks
export const useBOMs = () =>
  useQuery<BillOfMaterials[]>({
    queryKey: ['boms'],
    queryFn: () => bomAPI.getAll(),
  });

export const useBOM = (id: string) =>
  useQuery<BillOfMaterials>({
    queryKey: ['bom', id],
    queryFn: () => bomAPI.getById(id),
    enabled: !!id,
  });

export const useCreateBOM = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: bomAPI.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['boms'] }),
  });
};

export const useUpdateBOM = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BillOfMaterials> }) =>
      bomAPI.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['boms'] });
      queryClient.invalidateQueries({ queryKey: ['bom', id] });
    },
  });
};

// Work Order Hooks
export const useWorkOrders = (filters?: Parameters<typeof workOrderAPI.getAll>[0]) =>
  useQuery<WorkOrder[]>({
    queryKey: ['workOrders', filters],
    queryFn: () => workOrderAPI.getAll(filters),
  });

export const useWorkOrder = (id: string) =>
  useQuery<WorkOrder>({
    queryKey: ['workOrder', id],
    queryFn: () => workOrderAPI.getById(id),
    enabled: !!id,
  });

export const useCreateWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: workOrderAPI.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workOrders'] }),
  });
};

export const useUpdateWorkOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, progress }: { id: string; status: WorkOrder['status']; progress: number }) =>
      workOrderAPI.updateStatus(id, status, progress),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] });
      queryClient.invalidateQueries({ queryKey: ['workOrder', id] });
    },
  });
};

// Production Plan Hooks
export const useProductionPlans = () =>
  useQuery<ProductionPlan[]>({
    queryKey: ['productionPlans'],
    queryFn: () => productionPlanAPI.getAll(),
  });

export const useApprovePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: productionPlanAPI.approve,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['productionPlans'] }),
  });
};

// MRP Hooks
export const useMRPCalculation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: mrpAPI.calculate,
    onSuccess: (data) => {
      queryClient.setQueryData(['mrpCalculations'], data);
    },
  });
};

// KPI Hooks
export const useManufacturingKPI = (period?: string) =>
  useQuery<ManufacturingKPI>({
    queryKey: ['manufacturingKPI', period],
    queryFn: () => manufacturingKPIAPI.getDashboard(period),
  });

// Work Center Hooks
export const useWorkCenters = () =>
  useQuery<WorkCenter[]>({
    queryKey: ['workCenters'],
    queryFn: () => workCenterAPI.getAll(),
  });

