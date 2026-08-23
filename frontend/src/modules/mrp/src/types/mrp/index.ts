export interface BOMItem {
  id: string;
  productId: string;
  productName: string;
  sku: string;
  quantity: number;
  unit: string;
  unitCost: number;
  totalCost: number;
  isOptional: boolean;
  wastePercentage: number;
}

export interface BillOfMaterials {
  id: string;
  name: string;
  description: string;
  finishedGoodId: string;
  finishedGoodName: string;
  finishedGoodSku: string;
  version: number;
  isActive: boolean;
  items: BOMItem[];
  laborCost: number;
  overheadCost: number;
  totalMaterialCost: number;
  totalCost: number;
  yieldQuantity: number;
  yieldUnit: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkOrder {
  id: string;
  orderNumber: string;
  bomId: string;
  bomName: string;
  productId: string;
  productName: string;
  quantity: number;
  unit: string;
  status: WorkOrderStatus;
  priority: Priority;
  plannedStartDate: string;
  plannedEndDate: string;
  actualStartDate?: string;
  actualEndDate?: string;
  assignedTo?: string;
  assignedToName?: string;
  progress: number;
  notes: string;
  materialsConsumed: MaterialConsumption[];
  createdAt: string;
  updatedAt: string;
}

export type WorkOrderStatus =
  | 'draft'
  | 'planned'
  | 'released'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export type Priority = 'low' | 'medium' | 'high' | 'urgent';

export interface MaterialConsumption {
  bomItemId: string;
  productId: string;
  productName: string;
  plannedQuantity: number;
  actualQuantity: number;
  unit: string;
  variance: number;
  variancePercentage: number;
}

export interface ProductionPlan {
  id: string;
  planNumber: string;
  name: string;
  description: string;
  period: {
    startDate: string;
    endDate: string;
  };
  status: PlanStatus;
  workOrders: string[];
  totalQuantity: number;
  completedQuantity: number;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

export type PlanStatus = 'draft' | 'approved' | 'active' | 'completed' | 'cancelled';

export interface MRPCalculation {
  productId: string;
  productName: string;
  sku: string;
  currentStock: number;
  reservedStock: number;
  availableStock: number;
  grossRequirements: number;
  scheduledReceipts: number;
  netRequirements: number;
  plannedOrderReceipts: number;
  plannedOrderReleases: number;
  leadTime: number;
  reorderPoint: number;
  period: string;
}

export interface ManufacturingKPI {
  totalWorkOrders: number;
  inProgressOrders: number;
  completedOrders: number;
  overdueOrders: number;
  productionEfficiency: number;
  materialVariance: number;
  onTimeDeliveryRate: number;
  capacityUtilization: number;
  totalProductionCost: number;
  averageOrderLeadTime: number;
}

export interface Routing {
  id: string;
  productId: string;
  productName: string;
  steps: RoutingStep[];
  totalSetupTime: number;
  totalRunTime: number;
  totalLaborTime: number;
  isActive: boolean;
}

export interface RoutingStep {
  stepNumber: number;
  workCenterId: string;
  workCenterName: string;
  operationName: string;
  description: string;
  setupTime: number;
  runTime: number;
  laborTime: number;
  machineRequired: boolean;
  laborRequired: boolean;
  qualityCheckRequired: boolean;
}

export interface WorkCenter {
  id: string;
  name: string;
  code: string;
  department: string;
  capacity: number;
  currentLoad: number;
  utilizationRate: number;
  efficiency: number;
  status: 'active' | 'maintenance' | 'inactive';
}

---

