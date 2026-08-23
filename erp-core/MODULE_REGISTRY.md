# ERP-Core Module Registry

## Completed Modules (Production Ready)

### 1. Authentication & Authorization
- **Status**: ✅ Complete
- **Files**: `routers/auth.py`, `routers/users.py`, `routers/permissions.py`
- **Features**: JWT auth, RBAC, password validation, activity logging
- **Dependencies**: None

### 2. CRM (Customer Relationship Management)
- **Status**: ✅ Complete
- **Files**: `routers/crm.py`, `models/crm.py`, `schemas/crm.py`
- **Features**: Companies, Contacts, Deals management
- **Dependencies**: Auth

### 3. Finance
- **Status**: ✅ Complete
- **Files**: `routers/finance.py`, `models/finance.py`, `routers/payments.py`
- **Features**: Invoices, Invoice Items, Payments, Stripe integration
- **Dependencies**: CRM, Auth

### 4. HR (Human Resources)
- **Status**: ✅ Complete
- **Files**: `routers/hr.py`, `models/hr.py`
- **Features**: Employees, Departments
- **Dependencies**: Auth

### 5. Inventory
- **Status**: ✅ Complete
- **Files**: `routers/inventory.py`, `models/inventory.py`, `services/inventory_service.py`
- **Features**: Stock management, async support, validation
- **Dependencies**: Auth

### 6. Regulated Inventory
- **Status**: ✅ Complete
- **Files**: `models/regulated_inventory.py`, `services/regulated_inventory_service.py`
- **Features**: Compliance tracking, audit trails
- **Dependencies**: Inventory, Auth

### 7. Projects
- **Status**: ✅ Complete
- **Files**: `routers/projects.py`, `models/project.py`
- **Features**: Projects, Tasks with hierarchy
- **Dependencies**: CRM, HR, Auth

### 8. Workflows
- **Status**: ✅ Complete
- **Files**: `routers/workflows.py`, `models/workflow.py`
- **Features**: Workflow definitions, steps, executions
- **Dependencies**: Auth, Admin

### 9. Documents
- **Status**: ✅ Complete
- **Files**: `routers/documents.py`, `models/documents.py`
- **Features**: File upload, validation, secure storage
- **Dependencies**: Auth

### 10. Analytics
- **Status**: ✅ Complete
- **Files**: `routers/analytics.py`, `services/analytics_service.py`, `models/analytics.py`
- **Features**: Dashboard metrics, monthly trends
- **Dependencies**: All domains (read-only)

### 11. Search
- **Status**: ✅ Complete
- **Files**: `routers/search.py`, `models/search.py`, `services/search_service.py`
- **Features**: Full-text search, facets, suggestions, analytics
- **Dependencies**: All domains (read-only)

### 12. Admin
- **Status**: ✅ Complete
- **Files**: `routers/admin.py`, `models/system.py`
- **Features**: Settings, Activity Logs, Notifications
- **Dependencies**: Auth (admin role)

### 13. Integrations
- **Status**: ✅ Complete
- **Files**: `routers/integrations.py`, `routers/integration_v1.py`
- **Features**: External integrations, webhooks, versioned API contracts
- **Dependencies**: Auth

### 14. Reports
- **Status**: ✅ Complete
- **Files**: `routers/reports.py`
- **Features**: Revenue reports, pipeline reports
- **Dependencies**: Finance, CRM, Projects

### 15. WebSocket
- **Status**: ✅ Complete
- **Files**: `routers/websocket.py`
- **Features**: Real-time messaging, channels, ping/pong
- **Dependencies**: None

### 16. Health
- **Status**: ✅ Complete
- **Files**: `routers/health.py`
- **Features**: Database health check, version info
- **Dependencies**: None

### 17. Permissions (RBAC)
- **Status**: ✅ Complete
- **Files**: `routers/permissions.py`, `models/permissions.py`
- **Features**: Roles, Permissions, Field-level access, Data policies
- **Dependencies**: Auth

---

## Pending Modules (Requires Implementation)

### 1. E-commerce Module
- **Status**: ⏳ Pending
- **Required Files**: `routers/ecommerce.py`, `models/ecommerce.py`, `services/ecommerce_service.py`
- **Features**: Products catalog, shopping cart, orders, checkout
- **Dependencies**: Inventory, Finance, CRM

### 2. MRP (Material Requirements Planning)
- **Status**: ⏳ Pending
- **Required Files**: `routers/mrp.py`, `models/mrp.py`, `services/mrp_service.py`
- **Features**: BOM, production planning, material forecasting
- **Dependencies**: Inventory, Projects, Finance

### 3. POS (Point of Sale)
- **Status**: ⏳ Pending
- **Required Files**: `routers/pos.py`, `models/pos.py`, `services/pos_service.py`
- **Features**: Register management, transactions, receipts
- **Dependencies**: Inventory, Finance, Payments

### 4. BI (Business Intelligence)
- **Status**: ⏳ Pending
- **Required Files**: `routers/bi.py`, `models/bi.py`, `services/bi_service.py`
- **Features**: Advanced analytics, dashboards, data visualization
- **Dependencies**: Analytics, All domains (read-only)

### 5. Supply Chain
- **Status**: ⏳ Pending
- **Required Files**: `routers/supply_chain.py`, `models/supply_chain.py`, `services/supply_chain_service.py`
- **Features**: Purchase orders, suppliers, logistics
- **Dependencies**: Inventory, Finance, CRM

### 6. Manufacturing
- **Status**: ⏳ Pending
- **Required Files**: `routers/manufacturing.py`, `models/manufacturing.py`, `services/manufacturing_service.py`
- **Features**: Production orders, work centers, routing
- **Dependencies**: MRP, Inventory, HR

### 7. Quality Management
- **Status**: ⏳ Pending
- **Required Files**: `routers/quality.py`, `models/quality.py`, `services/quality_service.py`
- **Features**: QC checks, non-conformance, corrective actions
- **Dependencies**: Manufacturing, Inventory

### 8. Asset Management
- **Status**: ⏳ Pending
- **Required Files**: `routers/assets.py`, `models/assets.py`, `services/assets_service.py`
- **Features**: Fixed assets, depreciation, maintenance
- **Dependencies**: Finance, Inventory

---

## Core Infrastructure (Complete)

### Services Layer
- `services/activity_log.py` ✅
- `services/analytics_service.py` ✅
- `services/inventory_service.py` ✅
- `services/regulated_inventory_service.py` ✅
- `services/search_service.py` ✅
- `services/permissions.py` ✅
- `services/security_utils.py` ✅

### Middleware
- `middleware/error_handler.py` ✅
- `middleware/rate_limiter.py` ✅

### Adapters
- `adapters/integration.py` ✅

### Models
- `models/base.py` ✅
- `models/user.py` ✅
- `models/crm.py` ✅
- `models/finance.py` ✅
- `models/hr.py` ✅
- `models/inventory.py` ✅
- `models/regulated_inventory.py` ✅
- `models/project.py` ✅
- `models/workflow.py` ✅
- `models/permissions.py` ✅
- `models/search.py` ✅
- `models/system.py` ✅
- `models/documents.py` ✅
- `models/analytics.py` ✅

### Database
- PostgreSQL with async support ✅
- Alembic migrations ✅
- Connection pooling ✅

### Security
- JWT authentication ✅
- Password hashing ✅
- CORS configuration ✅
- Rate limiting ✅
- Input validation ✅
- File upload validation ✅

---

## Cold-Start Plugin Architecture

Plugin modules can be dynamically loaded at startup using the plugin registry pattern.

### Plugin Interface
```python
from abc import ABC, abstractmethod
from typing import List
from fastapi import FastAPI

class ERPPlugin(ABC):
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def register_routes(self, app: FastAPI) -> None:
        pass
    
    @abstractmethod
    def register_models(self) -> List:
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        pass
```

### Plugin Discovery
Plugins are discovered from `/plugins/cold-start/` directory at application startup.

### Available Plugin Slots
1. **E-commerce Plugin** - Slot ready
2. **MRP Plugin** - Slot ready
3. **POS Plugin** - Slot ready
4. **BI Plugin** - Slot ready
5. **Supply Chain Plugin** - Slot ready
6. **Manufacturing Plugin** - Slot ready
7. **Quality Plugin** - Slot ready
8. **Asset Plugin** - Slot ready

### Plugin Configuration
```yaml
plugins:
  enabled:
    - ecommerce
    - pos
  disabled:
    - mrp
    - bi
  config:
    ecommerce:
      tax_provider: stripe
      shipping_provider: fedex
    pos:
      hardware_integration: true
```
