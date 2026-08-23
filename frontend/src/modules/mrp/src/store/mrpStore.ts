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

// Extracted reducer functions for better testability and reusability
const bomReducers = {
  setBOMs: (_state: MRPState, boms: BillOfMaterials[]) => ({ boms }),
  setSelectedBOM: (_state: MRPState, selectedBOM: BillOfMaterials | null) => ({ selectedBOM }),
  addBOM: (state: MRPState, bom: BillOfMaterials) => ({ boms: [...state.boms, bom] }),
  updateBOM: (state: MRPState, bom: BillOfMaterials) => ({
    boms: state.boms.map((b) => (b.id === bom.id ? bom : b)),
  }),
  deleteBOM: (state: MRPState, id: string) => ({
    boms: state.boms.filter((b) => b.id !== id),
    selectedBOM: state.selectedBOM?.id === id ? null : state.selectedBOM,
  }),
};

const workOrderReducers = {
  setWorkOrders: (_state: MRPState, workOrders: WorkOrder[]) => ({ workOrders }),
  setSelectedWorkOrder: (_state: MRPState, selectedWorkOrder: WorkOrder | null) => ({ selectedWorkOrder }),
  addWorkOrder: (state: MRPState, order: WorkOrder) => ({ workOrders: [...state.workOrders, order] }),
  updateWorkOrder: (state: MRPState, order: WorkOrder) => ({
    workOrders: state.workOrders.map((o) => (o.id === order.id ? order : o)),
  }),
  updateWorkOrderStatus: (state: MRPState, id: string, status: WorkOrder['status'], progress: number) => ({
    workOrders: state.workOrders.map((o) =>
      o.id === id ? { ...o, status, progress } : o
    ),
  }),
  deleteWorkOrder: (state: MRPState, id: string) => ({
    workOrders: state.workOrders.filter((o) => o.id !== id),
    selectedWorkOrder: state.selectedWorkOrder?.id === id ? null : state.selectedWorkOrder,
  }),
};

const filterReducers = {
  setWorkOrderFilter: (state: MRPState, filter: Partial<MRPState['workOrderFilter']>) => ({
    workOrderFilter: { ...state.workOrderFilter, ...filter },
  }),
  resetFilters: () => ({
    workOrderFilter: {
      status: null,
      priority: null,
      dateRange: { start: null, end: null },
    },
  }),
};

export const useMRPStore = create<MRPState>()(
  persist(
    (set, get) => ({
      // BOMs
      boms: [],
      selectedBOM: null,
      setBOMs: (boms) => set(bomReducers.setBOMs(get(), boms)),
      setSelectedBOM: (selectedBOM) => set(bomReducers.setSelectedBOM(get(), selectedBOM)),
      addBOM: (bom) => set((state) => bomReducers.addBOM(state, bom)),
      updateBOM: (bom) => set((state) => bomReducers.updateBOM(state, bom)),
      deleteBOM: (id) => set((state) => bomReducers.deleteBOM(state, id)),

      // Work Orders
      workOrders: [],
      selectedWorkOrder: null,
      setWorkOrders: (workOrders) => set(workOrderReducers.setWorkOrders(get(), workOrders)),
      setSelectedWorkOrder: (selectedWorkOrder) => set(workOrderReducers.setSelectedWorkOrder(get(), selectedWorkOrder)),
      addWorkOrder: (order) => set((state) => workOrderReducers.addWorkOrder(state, order)),
      updateWorkOrder: (order) => set((state) => workOrderReducers.updateWorkOrder(state, order)),
      updateWorkOrderStatus: (id, status, progress) =>
        set((state) => workOrderReducers.updateWorkOrderStatus(state, id, status, progress)),
      deleteWorkOrder: (id) => set((state) => workOrderReducers.deleteWorkOrder(state, id)),

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
      setWorkOrderFilter: (filter) => set((state) => filterReducers.setWorkOrderFilter(state, filter)),
      resetFilters: () => set(filterReducers.resetFilters()),

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

