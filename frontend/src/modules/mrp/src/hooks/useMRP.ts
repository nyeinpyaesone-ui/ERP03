/**
 * Enterprise MRP Hooks
 * Uses standardized hook factories for consistent query/mutation patterns
 * 
 * @module modules/mrp/hooks/useMRP
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createQueryHooks, createMutationHooks } from '../../../core/hooks';
import {
  bomAPI,
  workOrderAPI,
  productionPlanAPI,
  mrpAPI,
  manufacturingKPIAPI,
  workCenterAPI,
  routingAPI,
} from '../services/api/mrpApi';
import type {
  BillOfMaterials,
  WorkOrder,
  ProductionPlan,
  MRPCalculation,
  ManufacturingKPI,
  WorkCenter,
  Routing,
} from '../types/mrp';

// BOM Hooks - using factory pattern
export const {
  useList: useBOMs,
  useItem: useBOM,
} = createQueryHooks<BillOfMaterials[], BillOfMaterials>({
  queryKeyPrefix: 'boms',
  queryFn: {
    list: bomAPI.getAll,
    item: bomAPI.getById,
    byField: (field, value) => {
      if (field === 'productId') return bomAPI.getByProduct(value);
      throw new Error(`Unknown field: ${field}`);
    },
  },
});

export const {
  useCreate: useCreateBOM,
  useUpdate: useUpdateBOM,
  useDelete: useDeleteBOM,
} = createMutationHooks<BillOfMaterials, Omit<BillOfMaterials, 'id' | 'createdAt' | 'updatedAt'>, Partial<BillOfMaterials>>({
  queryKeyPrefix: 'boms',
  mutationFn: {
    create: bomAPI.create,
    update: bomAPI.update,
    delete: bomAPI.delete,
  },
  invalidateOnSuccess: ['list'],
});

// Work Order Hooks - using factory pattern
export const {
  useList: useWorkOrders,
  useItem: useWorkOrder,
} = createQueryHooks<WorkOrder[], WorkOrder>({
  queryKeyPrefix: 'workOrders',
  queryFn: {
    list: workOrderAPI.getAll,
    item: workOrderAPI.getById,
    byField: (field, value) => {
      if (field === 'planId') return workOrderAPI.getByPlan(value);
      throw new Error(`Unknown field: ${field}`);
    },
  },
});

export const {
  useCreate: useCreateWorkOrder,
  useUpdate: useUpdateWorkOrder,
  useDelete: useDeleteWorkOrder,
} = createMutationHooks<WorkOrder, Omit<WorkOrder, 'id' | 'orderNumber' | 'createdAt' | 'updatedAt' | 'progress'>, Partial<WorkOrder>>({
  queryKeyPrefix: 'workOrders',
  mutationFn: {
    create: workOrderAPI.create,
    update: workOrderAPI.update,
    delete: workOrderAPI.delete,
  },
  invalidateOnSuccess: ['list', 'item'],
});

// Specialized work order status update hook
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

// Production Plan Hooks - using factory pattern
export const {
  useList: useProductionPlans,
  useItem: useProductionPlan,
} = createQueryHooks<ProductionPlan[], ProductionPlan>({
  queryKeyPrefix: 'productionPlans',
  queryFn: {
    list: productionPlanAPI.getAll,
    item: productionPlanAPI.getById,
  },
});

export const {
  useCreate: useCreateProductionPlan,
  useUpdate: useUpdateProductionPlan,
  useDelete: useDeleteProductionPlan,
} = createMutationHooks<ProductionPlan, Omit<ProductionPlan, 'id' | 'planNumber' | 'createdAt' | 'updatedAt' | 'progress' | 'completedQuantity'>, Partial<ProductionPlan>>({
  queryKeyPrefix: 'productionPlans',
  mutationFn: {
    create: productionPlanAPI.create,
    update: productionPlanAPI.update,
    delete: productionPlanAPI.delete,
  },
  invalidateOnSuccess: ['list'],
});

// Specialized plan approval hook
export const useApprovePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: productionPlanAPI.approve,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['productionPlans'] }),
  });
};

// MRP Calculation Hooks
export const useMRPCalculation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: mrpAPI.calculate,
    onSuccess: (data) => {
      queryClient.setQueryData(['mrpCalculations'], data);
    },
  });
};

export const useMRPExplosion = () => {
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      mrpAPI.getExplosion(productId, quantity),
  });
};

// KPI Hooks
export const useManufacturingKPI = (period?: string) =>
  useQuery<ManufacturingKPI>({
    queryKey: ['manufacturingKPI', period],
    queryFn: () => manufacturingKPIAPI.getDashboard(period),
  });

export const useManufacturingEfficiency = (workCenterId?: string, period?: string) =>
  useQuery({
    queryKey: ['manufacturingEfficiency', workCenterId, period],
    queryFn: () => manufacturingKPIAPI.getEfficiency(workCenterId, period),
  });

export const useManufacturingVariance = (period?: string) =>
  useQuery({
    queryKey: ['manufacturingVariance', period],
    queryFn: () => manufacturingKPIAPI.getVariance(period),
  });

// Work Center Hooks - using factory pattern
export const {
  useList: useWorkCenters,
  useItem: useWorkCenter,
} = createQueryHooks<WorkCenter[], WorkCenter>({
  queryKeyPrefix: 'workCenters',
  queryFn: {
    list: workCenterAPI.getAll,
    item: workCenterAPI.getById,
  },
});

// Routing Hooks - using factory pattern
export const {
  useList: useRoutings,
  useByField: useRoutingByProduct,
} = createQueryHooks<Routing[], Routing>({
  queryKeyPrefix: 'routings',
  queryFn: {
    list: routingAPI.getAll,
    byField: (field, value) => {
      if (field === 'productId') return routingAPI.getByProduct(value);
      throw new Error(`Unknown field: ${field}`);
    },
  },
});

