# Integration Compatibility Layer

## Overview

This document describes the integration compatibility layer implemented to ensure seamless communication between ERP-BACKEND and AI-BACKEND systems through standardized contracts.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   AI-BACKEND    │────────▶│  INTEGRATION     │◀────────│   ERP-BACKEND   │
│                 │         │  /contracts      │         │                 │
│  (ERP Client)   │         │  (Schemas)       │         │  (Adapters)     │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Components

### 1. Integration Contracts (`INTEGRATION/contracts/schemas/`)

Standardized Pydantic schemas that define the API contract between systems:

- **CRM Schemas**: Customer, Contact, Opportunity, Interaction
- **Inventory Schemas**: Product, Category, StockMovement, Location
- **Base Schemas**: User, Role, Permission, EventEnvelope, HealthStatus

**Key Principle**: AI systems MUST only use these schemas. Never import ERP ORM models directly.

### 2. ERP Client Adapter (`INTEGRATION/erp-client/client.py`)

HTTP client for AI-BACKEND to communicate with ERP-BACKEND:

- Async and sync clients (`ERPClient`, `ERPSyncClient`)
- Retry logic with exponential backoff
- Circuit breaker pattern
- JWT authentication
- Request/response validation

### 3. Integration Adapters (`ERP-BACKEND/app/adapters/`)

Adapter layer that converts between internal ERP models and integration contracts:

- **CRMAdapter**: Converts Company → Customer, Contact → Contact, Deal → Opportunity
- **InventoryAdapter**: Converts Product → Product, Category → Category

### 4. Integration v1 API (`ERP-BACKEND/app/routers/integration_v1.py`)

Versioned API endpoints that expose contract-compatible responses:

#### CRM Endpoints
- `GET /integration/v1/crm/customers` - List customers
- `GET /integration/v1/crm/customers/{customer_id}` - Get customer
- `GET /integration/v1/crm/contacts` - List contacts
- `GET /integration/v1/crm/opportunities` - List opportunities

#### Inventory Endpoints
- `GET /integration/v1/inventory/products` - List products
- `GET /integration/v1/inventory/products/{product_id}` - Get product
- `GET /integration/v1/inventory/products/sku/{sku}` - Get product by SKU

#### Command Endpoints
- `POST /integration/v1/erp/commands` - Submit commands (purchase order approvals)

All endpoints require service-to-service authentication via JWT tokens.

## Usage Examples

### AI-BACKEND: Fetching Customers

```python
from integration.erp_client import ERPClient

client = ERPClient(
    base_url="http://erp-backend:8000",
    jwt_token="your_service_token"
)

# List customers using integration contract
customers = await client.list_customers(page=1, page_size=20, search="Acme")
for customer in customers:
    print(f"{customer.name} - {customer.email}")

await client.close()
```

### ERP-BACKEND: Using Adapters

```python
from app.adapters.integration import CRMAdapter, InventoryAdapter

# Convert internal model to contract schema
customer = db.query(Company).filter(Company.id == 1).first()
contract_customer = CRMAdapter.company_to_customer(customer)

# Now contract_customer matches INTEGRATION/contracts/schemas/crm.py
```

## Schema Mapping

### CRM Mappings

| Internal Model | Contract Schema | Adapter Method |
|---------------|----------------|----------------|
| `Company` | `CustomerSchema` | `CRMAdapter.company_to_customer()` |
| `Contact` | `ContactSchema` | `CRMAdapter.contact_to_contract()` |
| `Deal` | `OpportunitySchema` | `CRMAdapter.deal_to_opportunity()` |

### Inventory Mappings

| Internal Model | Contract Schema | Adapter Method |
|---------------|----------------|----------------|
| `Product` | `ProductSchema` | `InventoryAdapter.product_to_contract()` |
| `Category` | `CategorySchema` | `InventoryAdapter.category_to_contract()` |

## Authentication

All integration endpoints require service-to-service authentication:

1. **JWT Token**: Issued by the integration service issuer
2. **Service Principal**: Token must have `service: true` claim
3. **Audience Verification**: Token audience must match `INTEGRATION_SERVICE_AUDIENCE`

Example token payload:
```json
{
  "sub": "ai-backend-service",
  "iss": "erp-integration-issuer",
  "aud": "erp-backend",
  "service": true,
  "actor_id": 1,
  "exp": 1234567890
}
```

## Error Handling

The integration layer provides standardized error responses:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request payload",
  "details": {...}
}
```

Common error codes:
- `AUTHENTICATION_FAILED` (401)
- `AUTHORIZATION_DENIED` (403)
- `NOT_FOUND` (404)
- `VALIDATION_ERROR` (400)
- `RATE_LIMIT_EXCEEDED` (429)
- `SERVICE_UNAVAILABLE` (503)

## Testing

### Unit Tests

```bash
cd ERP-BACKEND
pytest tests/test_integration_adapters.py
```

### Integration Tests

```bash
cd INTEGRATION/contracts/v1
python test_contract.py
```

## Migration Guide

### For Existing ERP Endpoints

To migrate existing endpoints to use integration contracts:

1. Import adapters: `from app.adapters.integration import CRMAdapter`
2. Convert response: `return CRMAdapter.company_to_customer(company)`
3. Update response_model to use contract schema

### For AI-BACKEND

To use the new integration layer:

1. Replace direct DB access with `ERPClient`
2. Use contract schemas for type hints
3. Handle circuit breaker exceptions

## Benefits

✅ **Decoupling**: AI systems don't depend on ERP internal models  
✅ **Versioning**: API contracts can evolve independently  
✅ **Validation**: Request/response validation at boundaries  
✅ **Resilience**: Circuit breaker prevents cascading failures  
✅ **Type Safety**: Pydantic schemas ensure data consistency  

## Future Enhancements

- [ ] Add POST/PUT/PATCH endpoints for CRM operations
- [ ] Implement event publishing to INTEGRATION/event-bus
- [ ] Add GraphQL interface for complex queries
- [ ] Support webhook subscriptions for real-time updates
- [ ] Add rate limiting per service consumer

---

**Related Documentation:**
- [Integration README](../../INTEGRATION/README.md)
- [Contract Schemas](../../INTEGRATION/contracts/schemas/)
- [ERP Client](../../INTEGRATION/erp-client/client.py)
- [Architecture Decisions](../../docs/ARCHITECTURE_DECISIONS.md)
