# API Documentation Summary

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

## Authentication
All endpoints require JWT token in header:
```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/register` | User registration |
| POST | `/auth/refresh` | Refresh token |
| POST | `/auth/logout` | User logout |

### ERP Modules
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory` | Inventory list |
| POST | `/api/v1/inventory` | Create item |
| GET | `/api/v1/orders` | Orders list |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/customers` | Customers list |
| GET | `/api/v1/reports/sales` | Sales report |
| GET | `/api/v1/reports/inventory` | Inventory report |

### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/forecast` | Demand forecasting |
| POST | `/ai/chat` | AI assistant chat |
| POST | `/ai/rag/query` | RAG document query |
| GET | `/ai/agents/status` | Agent orchestrator status |

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('wss://api.yourdomain.com/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

### Multi-Tenant
All endpoints support tenant isolation via:
- Header: `X-Tenant-ID: tenant-123`
- JWT claim: `tenant_id`

## OpenAPI Spec
Full documentation available at:
- Swagger UI: `https://api.yourdomain.com/docs`
- ReDoc: `https://api.yourdomain.com/redoc`
- OpenAPI JSON: `https://api.yourdomain.com/openapi.json`

## Rate Limits
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Premium: 10000 requests/hour

## Error Codes
| Code | Meaning |
|------|---------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (tenant access) |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |
