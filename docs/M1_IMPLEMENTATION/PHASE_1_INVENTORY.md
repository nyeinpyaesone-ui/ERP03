# Phase 1.1: Route & Module Inventory Audit

## Objective
Create a comprehensive inventory of all ERP backend routes, modules, and their dependencies.

## Status
- [ ] Route inventory completed
- [ ] Module mapping completed
- [ ] Dependency graph created
- [ ] Architecture diagram created

## Route Inventory Template

### Module: Finance

```yaml
module_name: Finance
responsibility: "Financial transaction management, ledger, and reporting"
routes:
  - path: /api/v1/finance/invoices
    method: GET
    description: "List all invoices"
    auth: "REQUIRES: finance.read"
    dependencies:
      - database: invoice, invoice_line_items
      - services: auth, audit
    
  - path: /api/v1/finance/invoices
    method: POST
    description: "Create new invoice"
    auth: "REQUIRES: finance.write"
    idempotency: "REQUIRED (idempotency_key header)"
    dependencies:
      - database: invoice, invoice_line_items, company, customer
      - services: auth, audit, validation
      - external: accounting_system

  - path: /api/v1/finance/invoices/{id}
    method: GET
    description: "Retrieve single invoice"
    auth: "REQUIRES: finance.read"
    dependencies:
      - database: invoice, invoice_line_items

  - path: /api/v1/finance/invoices/{id}/approve
    method: POST
    description: "Approve invoice (workflow state change)"
    auth: "REQUIRES: finance.approve"
    idempotency: "REQUIRED"
    state_machine: "draft -> pending -> approved -> paid"
    dependencies:
      - database: invoice, invoice_approval_log
      - services: auth, audit, notifications
```

### Module: Inventory

```yaml
module_name: Inventory
responsibility: "Stock tracking, warehouse operations, and fulfillment"
routes:
  - path: /api/v1/inventory/stock
    method: GET
    description: "List current stock levels"
    auth: "REQUIRES: inventory.read"
    caching: "Redis (TTL: 5min)"
    dependencies:
      - database: stock_levels, warehouse_locations
      - cache: redis

  - path: /api/v1/inventory/stock/{sku}/adjust
    method: POST
    description: "Adjust stock quantity"
    auth: "REQUIRES: inventory.write"
    idempotency: "REQUIRED"
    dependencies:
      - database: stock_levels, stock_movement_log
      - services: auth, audit, notifications
      - external: barcode_scanner_api

  - path: /api/v1/inventory/shipments
    method: POST
    description: "Create shipment"
    auth: "REQUIRES: inventory.ship"
    idempotency: "REQUIRED"
    saga_pattern: "Required for multi-step fulfillment"
    dependencies:
      - database: shipment, shipment_items, stock_levels
      - services: auth, audit, notifications, erp_finance
      - external: shipping_provider_api
```

### Module: Sales/CRM

```yaml
module_name: Sales
responsibility: "Customer management, orders, and sales pipeline"
routes:
  - path: /api/v1/sales/customers
    method: GET
    description: "List customers with filters and pagination"
    auth: "REQUIRES: sales.read"
    dependencies:
      - database: customer, customer_contacts, customer_addresses

  - path: /api/v1/sales/orders
    method: POST
    description: "Create sales order"
    auth: "REQUIRES: sales.create_order"
    idempotency: "REQUIRED"
    saga_pattern: "Required - inventory reservation -> payment -> fulfillment"
    dependencies:
      - database: sales_order, sales_order_line, customer
      - services: auth, audit, inventory, finance, notifications
      - external: payment_processor, shipping_provider
```

## Dependency Graph Structure

```
Core Services (Used by all):
├── Authentication Service
├── Authorization Service
├── Audit Service
└── Notification Service

Business Modules:
├── Finance Module
│   └── depends_on: Audit, Auth, Notifications
├── Inventory Module
│   ├── depends_on: Audit, Auth, Notifications, Redis Cache
│   └── called_by: Sales, Procurement, Manufacturing
├── Sales Module
│   ├── depends_on: Audit, Auth, Inventory, Finance, Notifications
│   └── called_by: Analytics
├── Procurement Module
│   ├── depends_on: Audit, Auth, Inventory, Finance
│   └── called_by: Inventory, Finance
└── HR/Payroll Module
    └── depends_on: Audit, Auth, Finance, Notifications

External Integrations:
├── Payment Processor API (Finance, Sales)
├── Shipping Provider API (Inventory, Sales)
├── Accounting System (Finance)
└── Barcode Scanner API (Inventory)
```

## Acceptance Criteria Checklist

- [ ] All REST endpoints documented with method, path, auth requirement
- [ ] Every endpoint has identified dependencies (database, services, external)
- [ ] State machines documented for workflow endpoints (approve, reject, etc.)
- [ ] Idempotency requirements marked for all write operations
- [ ] External integrations catalogued
- [ ] Module responsibility statements are non-overlapping
- [ ] Data ownership clear for each module
- [ ] No circular dependencies documented
- [ ] Caching strategy defined where applicable
- [ ] Database tables/models mapped to each endpoint

## Tools & Scripts

Run the automated inventory scanner:

```bash
python scripts/inventory_scanner.py \
  --source ERP-BACKEND/app/api/routes \
  --output docs/M1_IMPLEMENTATION/inventory_report.json
```

Generate dependency graph visualization:

```bash
python scripts/dependency_graph.py \
  --input docs/M1_IMPLEMENTATION/inventory_report.json \
  --output docs/M1_IMPLEMENTATION/dependency_graph.dot

dot -Tsvg dependency_graph.dot > dependency_graph.svg
```
