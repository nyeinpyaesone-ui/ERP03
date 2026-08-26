/**
 * Enterprise MRP Store
 * Uses standardized store factory with async action tracking
 * 
 * @module modules/mrp/store/mrpStore
 */

import { createStore, createSlice } from '../../../core/store';
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

  // Work Orders
  workOrders: WorkOrder[];
  selectedWorkOrder: WorkOrder | null;

  // Production Plans
  productionPlans: ProductionPlan[];
  selectedPlan: ProductionPlan | null;

  // MRP Calculations
  mrpCalculations: MRPCalculation[];

  // Work Centers
  workCenters: WorkCenter[];

  // Routings
  routings: Routing[];

  // Filters
  workOrderFilter: {
    status: string | null;
    priority: string | null;
    dateRange: { start: string | null; end: string | null };
  };

  // Required base state for async tracking
  _actions: Record<string, 'idle' | 'loading' | 'success' | 'error'>;
  _errors: Record<string, string | null>;
}

interface MRPActions {
  // BOM actions
  setBOMs: (boms: BillOfMaterials[]) => void;
  setSelectedBOM: (bom: BillOfMaterials | null) => void;
  addBOM: (bom: BillOfMaterials) => void;
  updateBOM: (bom: BillOfMaterials) => void;
  deleteBOM: (id: string) => void;

  // Work Order actions
  setWorkOrders: (orders: WorkOrder[]) => void;
  setSelectedWorkOrder: (order: WorkOrder | null) => void;
  addWorkOrder: (order: WorkOrder) => void;
  updateWorkOrder: (order: WorkOrder) => void;
  updateWorkOrderStatus: (id: string, status: WorkOrder['status'], progress: number) => void;
  deleteWorkOrder: (id: string) => void;

  // Production Plan actions
  setProductionPlans: (plans: ProductionPlan[]) => void;
  setSelectedPlan: (plan: ProductionPlan | null) => void;

  // MRP Calculation actions
  setMRPCalculations: (calculations: MRPCalculation[]) => void;

  // Work Center actions
  setWorkCenters: (centers: WorkCenter[]) => void;

  // Routing actions
  setRoutings: (routings: Routing[]) => void;

  // Filter actions
  setWorkOrderFilter: (filter: Partial<MRPState['workOrderFilter']>) => void;
  resetFilters: () => void;
}

const mrpSlice = createSlice<MRPState, MRPActions>({
  name: 'mrp',
  initialState: {
    // BOMs
    boms: [],
    selectedBOM: null,

    // Work Orders
    workOrders: [],
    selectedWorkOrder: null,

    // Production Plans
    productionPlans: [],
    selectedPlan: null,

    // MRP Calculations
    mrpCalculations: [],

    // Work Centers
    workCenters: [],

    // Routings
    routings: [],

    // Filters
    workOrderFilter: {
      status: null,
      priority: null,
      dateRange: { start: null, end: null },
    },

    // Required base state
    _actions: {},
    _errors: {},
  },
  actions: (set, get) => ({
    // BOM actions
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

    // Work Order actions
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

    // Production Plan actions
    setProductionPlans: (productionPlans) => set({ productionPlans }),
    setSelectedPlan: (selectedPlan) => set({ selectedPlan }),

    // MRP Calculation actions
    setMRPCalculations: (mrpCalculations) => set({ mrpCalculations }),

    // Work Center actions
    setWorkCenters: (workCenters) => set({ workCenters }),

    // Routing actions
    setRoutings: (routings) => set({ routings }),

    // Filter actions
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
  }),
});

export const useMRPStore = createStore({
  name: 'mrp',
  initialState: mrpSlice.initialState,
  actions: mrpSlice.actions,
  persist: {
    enabled: true,
    key: 'mrp-storage',
    partialize: (state) => ({
      workOrderFilter: state.workOrderFilter,
    }),
  },
});

