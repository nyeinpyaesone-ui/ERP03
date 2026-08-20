import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  BillOfMaterials,
  WorkOrder,
  ProductionPlan,
  MRPCalculation,
  WorkCenter,
  Routing,
} from '../types/mrp';

interface MRPState {
  // BOMs
  boms: BillOfMaterials[];
  selectedBOM: BillOfMaterials | null;
  setBOMs: (boms: BillOfMaterials[]) => void;
  setSelectedBOM: (bom: BillOfMaterials | null) => void;
  addBOM: (bom: BillOfMaterials) => void;
  updateBOM: (bom: BillOfMaterials) => void;
  deleteBOM: (id: string) => void;

  // Work Orders
  workOrders: WorkOrder[];
  selectedWorkOrder: WorkOrder | null;
  setWorkOrders: (orders: WorkOrder[]) => void;
  setSelectedWorkOrder: (order: WorkOrder | null) => void;
  addWorkOrder: (order: WorkOrder) => void;
  updateWorkOrder: (order: WorkOrder) => void;
  updateWorkOrderStatus: (id: string, status: WorkOrder['status'], progress: number) => void;
  deleteWorkOrder: (id: string) => void;

  // Production Plans
  productionPlans: ProductionPlan[];
  selectedPlan: ProductionPlan | null;
  setProductionPlans: (plans: ProductionPlan[]) => void;
  setSelectedPlan: (plan: ProductionPlan | null) => void;

  // MRP Calculations
  mrpCalculations: MRPCalculation[];
  setMRPCalculations: (calculations: MRPCalculation[]) => void;

  // Work Centers
  workCenters: WorkCenter[];
  setWorkCenters: (centers: WorkCenter[]) => void;

  // Routings
  routings: Routing[];
  setRoutings: (routings: Routing[]) => void;

  // Filters
  workOrderFilter: {
    status: string | null;
    priority: string | null;
    dateRange: { start: string | null; end: string | null };
  };
  setWorkOrderFilter: (filter: Partial<MRPState['workOrderFilter']>) => void;
  resetFilters: () => void;

  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

export const useMRPStore = create<MRPState>()(
  persist(
    (set, get) => ({
      // BOMs
      boms: [],
      selectedBOM: null,
      setBOMs: (boms) => set({ boms }),
      setSelectedBOM: (selectedBOM) => set({ selectedBOM }),
      addBOM: (bom) => set((state) => ({ boms: [...state.boms, bom] })),
      updateBOM: (bom) =>
        set((state) => ({
          boms: state.boms.map((b) => (b.id === bom.id ? bom : b)),
        })),
      deleteBOM: (id) =>
        set((state) => ({
          boms: state.boms.filter((b) => b.id !== id),
          selectedBOM: state.selectedBOM?.id === id ? null : state.selectedBOM,
        })),

      // Work Orders
      workOrders: [],
      selectedWorkOrder: null,
      setWorkOrders: (workOrders) => set({ workOrders }),
      setSelectedWorkOrder: (selectedWorkOrder) => set({ selectedWorkOrder }),
      addWorkOrder: (order) =>
        set((state) => ({ workOrders: [...state.workOrders, order] })),
      updateWorkOrder: (order) =>
        set((state) => ({
          workOrders: state.workOrders.map((o) => (o.id === order.id ? order : o)),
        })),
      updateWorkOrderStatus: (id, status, progress) =>
        set((state) => ({
          workOrders: state.workOrders.map((o) =>
            o.id === id ? { ...o, status, progress } : o
          ),
        })),
      deleteWorkOrder: (id) =>
        set((state) => ({
          workOrders: state.workOrders.filter((o) => o.id !== id),
          selectedWorkOrder: state.selectedWorkOrder?.id === id ? null : state.selectedWorkOrder,
        })),

      // Production Plans
      productionPlans: [],
      selectedPlan: null,
      setProductionPlans: (productionPlans) => set({ productionPlans }),
      setSelectedPlan: (selectedPlan) => set({ selectedPlan }),

      // MRP Calculations
      mrpCalculations: [],
      setMRPCalculations: (mrpCalculations) => set({ mrpCalculations }),

      // Work Centers
      workCenters: [],
      setWorkCenters: (workCenters) => set({ workCenters }),

      // Routings
      routings: [],
      setRoutings: (routings) => set({ routings }),

      // Filters
      workOrderFilter: {
        status: null,
        priority: null,
        dateRange: { start: null, end: null },
      },
      setWorkOrderFilter: (filter) =>
        set((state) => ({
          workOrderFilter: { ...state.workOrderFilter, ...filter },
        })),
      resetFilters: () =>
        set({
          workOrderFilter: {
            status: null,
            priority: null,
            dateRange: { start: null, end: null },
          },
        }),

      // Loading
      isLoading: false,
      setIsLoading: (isLoading) => set({ isLoading }),
      error: null,
      setError: (error) => set({ error }),
    }),
    {
      name: 'mrp-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        workOrderFilter: state.workOrderFilter,
      }),
    }
  )
);

