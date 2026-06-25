# ERP SOLUTION Manufacturing / MRP Module (v2.7)

## Overview
Complete Manufacturing Resource Planning module with Bill of Materials (BOM), Work Orders, Production Planning, and MRP calculations.

## Features

### 1. Bill of Materials (BOM)
- Multi-level BOM support with versioning
- Material cost rollup with labor & overhead
- Product-to-BOM linking
- Active/Inactive status management

### 2. Work Orders
- Full lifecycle: Draft → Planned → Released → In Progress → Completed
- Material consumption tracking with variance analysis
- Progress tracking with visual indicators
- Priority management (Low/Medium/High/Urgent)
- Assignment to workers/departments
- Overdue detection and alerts

### 3. Production Planning
- Period-based planning (weekly/monthly/quarterly)
- Work order grouping under plans
- Approval workflow (Draft → Approved → Active)
- Progress tracking against targets
- Capacity planning integration

### 4. MRP Calculation
- Gross/Net requirements calculation
- Planned order receipts & releases
- Lead time consideration
- Reorder point alerts
- Multi-period horizon support

### 5. Work Centers & Routing
- Work center capacity tracking
- Load balancing
- Routing step management
- Efficiency monitoring

## Screens

| Screen | Description |
|--------|-------------|
| MRPDashboard | KPI overview, quick actions, overdue alerts |
| BOMList | Searchable BOM catalog with cost breakdown |
| WorkOrders | Full work order management with status filters |
| ProductionPlanning | Plan creation, approval, and tracking |
| MRPCalculation | Material requirements analysis |

## Installation

### 1. Copy files to project
```bash
cp -r src/screens/mrp/* your-project/src/screens/mrp/
cp -r src/types/mrp/* your-project/src/types/mrp/
cp -r src/store/mrpStore.ts your-project/src/store/
cp -r src/services/api/mrpApi.ts your-project/src/services/api/
cp -r src/hooks/useMRP.ts your-project/src/hooks/
cp -r src/navigation/MRPNavigator.tsx your-project/src/navigation/
```

### 2. Add MRP tab to main navigation
```tsx
import { MRPNavigator } from './navigation/MRPNavigator';

// In your BottomTab.Navigator:
<Tab.Screen
  name="Manufacturing"
  component={MRPNavigator}
  options={{
    tabBarIcon: ({ color }) => (
      <MaterialCommunityIcons name="factory" size={24} color={color} />
    ),
  }}
/>
```

### 3. Backend API Endpoints Required

```
GET    /api/v1/manufacturing/boms
GET    /api/v1/manufacturing/boms/:id
POST   /api/v1/manufacturing/boms
PUT    /api/v1/manufacturing/boms/:id
DELETE /api/v1/manufacturing/boms/:id

GET    /api/v1/manufacturing/work-orders
GET    /api/v1/manufacturing/work-orders/:id
POST   /api/v1/manufacturing/work-orders
PUT    /api/v1/manufacturing/work-orders/:id
PATCH  /api/v1/manufacturing/work-orders/:id/status
POST   /api/v1/manufacturing/work-orders/:id/consume

GET    /api/v1/manufacturing/production-plans
GET    /api/v1/manufacturing/production-plans/:id
POST   /api/v1/manufacturing/production-plans
PUT    /api/v1/manufacturing/production-plans/:id
PATCH  /api/v1/manufacturing/production-plans/:id/approve
DELETE /api/v1/manufacturing/production-plans/:id

POST   /api/v1/manufacturing/mrp/calculate
GET    /api/v1/manufacturing/mrp/product/:id

GET    /api/v1/manufacturing/kpi/dashboard
GET    /api/v1/manufacturing/work-centers
GET    /api/v1/manufacturing/routings
```

## State Management

Uses Zustand for local state + TanStack Query for server state:

```tsx
import { useMRPStore } from './store/mrpStore';
import { useWorkOrders, useCreateWorkOrder } from './hooks/useMRP';

// Server state (auto-cached, refreshed)
const { data: workOrders } = useWorkOrders({ status: 'in_progress' });

// Local state (persisted)
const { selectedWorkOrder, setSelectedWorkOrder } = useMRPStore();

// Mutations (auto-invalidates queries)
const createMutation = useCreateWorkOrder();
```

## Next Steps

1. **Work Center Scheduling** - Gantt chart view for work center load
2. **Quality Control** - Inspection checkpoints in routing steps
3. **Cost Accounting** - Actual vs standard cost variance analysis
4. **Shop Floor** - Barcode scanning for material issuance
5. **Equipment Maintenance** - Preventive maintenance scheduling

