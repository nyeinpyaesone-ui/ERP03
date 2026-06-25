# ERP SOLUTION System v2.1

Enterprise Resource Planning with AI-powered features, PWA support, Stripe payments, workflow automation, and predictive analytics.

## Features

- **Core ERP**: CRM, HR, Inventory, Finance, Projects
- **AI Chat**: Business intelligence assistant with Ollama
- **Document RAG**: Upload, chunk, embed, and search documents
- **Reports & Charts**: Revenue, pipeline, inventory analytics
- **Workflow Automation**: Trigger-based approvals and actions
- **Stripe Payments**: Invoice payments with webhooks
- **PWA**: Offline support, installable, background sync
- **AI Forecasting**: Revenue prediction, inventory risk, churn analysis
- **Bulk Import/Export**: CSV, Excel, JSON for 9 entity types
- **Alembic Migrations**: Schema evolution with version control
- **Real-time**: WebSocket notifications
- **Integrations**: Slack, Teams, Zapier, custom webhooks

## Architecture

```
erp_solution-system/
в”њв”Ђв”Ђ backend/                 # FastAPI + SQLAlchemy + PostgreSQL
в”‚   в”њв”Ђв”Ђ app/
в”‚   в”‚   в”њв”Ђв”Ђ main.py           # FastAPI app with 16 routers
в”‚   в”‚   в”њв”Ђв”Ђ config.py         # Pydantic settings
в”‚   в”‚   в”њв”Ђв”Ђ database.py       # SQLAlchemy engine & session
в”‚   в”‚   в”њв”Ђв”Ђ auth.py           # JWT, bcrypt, role guards
в”‚   в”‚   в”њв”Ђв”Ђ models.py         # 20+ SQLAlchemy models
в”‚   в”‚   в”њв”Ђв”Ђ routers/          # 16 API routers
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ auth.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ crm.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ hr.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ inventory.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ finance.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ projects.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ ai.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ documents.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ reports.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ workflows.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ payments.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ integrations.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ analytics.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ admin.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ websocket.py
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ bulk_import_export.py
в”‚   в”‚   в”‚   в””в”Ђв”Ђ migrations.py
в”‚   в”‚   в””в”Ђв”Ђ services/
в”‚   в”‚       в”њв”Ђв”Ђ activity_log.py
в”‚   в”‚       в””в”Ђв”Ђ bulk_import_export.py
в”‚   в”њв”Ђв”Ђ alembic/              # Database migrations
в”‚   в”‚   в”њв”Ђв”Ђ env.py
в”‚   в”‚   в”њв”Ђв”Ђ script.py.mako
в”‚   в”‚   в””в”Ђв”Ђ versions/
в”‚   в”‚       в””в”Ђв”Ђ 001_initial_migration.py
в”‚   в”њв”Ђв”Ђ alembic.ini
в”‚   в”њв”Ђв”Ђ requirements.txt
в”‚   в”њв”Ђв”Ђ Dockerfile
в”‚   в””в”Ђв”Ђ .env.example
в”њв”Ђв”Ђ frontend-react/           # React 18 + Vite + Tailwind
в”‚   в”њв”Ђв”Ђ src/
в”‚   в”‚   в”њв”Ђв”Ђ main.jsx
в”‚   в”‚   в”њв”Ђв”Ђ App.jsx
в”‚   в”‚   в”њв”Ђв”Ђ index.css
в”‚   в”‚   в”њв”Ђв”Ђ components/
в”‚   в”‚   в”‚   в””в”Ђв”Ђ Layout.jsx
в”‚   в”‚   в””в”Ђв”Ђ pages/
в”‚   в”‚       в”њв”Ђв”Ђ Login.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Dashboard.jsx
в”‚   в”‚       в”њв”Ђв”Ђ CRM.jsx
в”‚   в”‚       в”њв”Ђв”Ђ HR.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Inventory.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Finance.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Projects.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Reports.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Analytics.jsx
в”‚   в”‚       в”њв”Ђв”Ђ AIChat.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Documents.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Workflows.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Integrations.jsx
в”‚   в”‚       в”њв”Ђв”Ђ Settings.jsx
в”‚   в”‚       в”њв”Ђв”Ђ BulkImportExport.jsx
в”‚   в”‚       в””в”Ђв”Ђ MigrationManager.jsx
в”‚   в”њв”Ђв”Ђ public/
в”‚   в”‚   в”њв”Ђв”Ђ manifest.json
в”‚   в”‚   в””в”Ђв”Ђ sw.js
в”‚   в”њв”Ђв”Ђ package.json
в”‚   в”њв”Ђв”Ђ vite.config.js
в”‚   в”њв”Ђв”Ђ tailwind.config.js
в”‚   в”њв”Ђв”Ђ Dockerfile
в”‚   в””в”Ђв”Ђ nginx.conf
в””в”Ђв”Ђ docker-compose.yml
```

## Quick Start

### Local Development

```bash
# 1. Start PostgreSQL and Redis
docker-compose up -d db redis

# 2. Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend-react
npm install
npm run dev

# 4. Open http://localhost:3000
```

### Docker (Full Stack)

```bash
docker-compose up -d
docker-compose exec ollama ollama pull qwen3.6
```

### First Time Setup

```bash
# Create admin user via API
curl -X POST http://localhost:8000/api/v1/auth/register   -H "Content-Type: application/json"   -d '{"email":"admin@company.com","password":"admin123","full_name":"Admin User","role":"admin"}'
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2)
- `GET /api/v1/auth/me` - Current user
- `GET /api/v1/auth/users` - List users (admin)

### CRM
- `GET/POST /api/v1/crm/contacts`
- `GET/POST /api/v1/crm/companies`
- `GET/POST /api/v1/crm/deals`
- `GET /api/v1/crm/deals/pipeline`
- `GET /api/v1/crm/dashboard`

### HR
- `GET/POST /api/v1/hr/departments`
- `GET/POST /api/v1/hr/employees`
- `GET /api/v1/hr/dashboard`

### Inventory
- `GET/POST /api/v1/inventory/products`
- `GET/POST /api/v1/inventory/movements`
- `GET /api/v1/inventory/dashboard`

### Finance
- `GET/POST /api/v1/finance/invoices`
- `POST /api/v1/finance/payments`
- `GET /api/v1/finance/dashboard`

### Projects
- `GET/POST /api/v1/projects/projects`
- `GET/POST /api/v1/projects/tasks`
- `GET /api/v1/projects/dashboard`

### AI
- `POST /api/v1/ai/chat` - AI business assistant
- `GET /api/v1/ai/insights` - Executive insights
- `GET /api/v1/ai/forecast/revenue` - Revenue forecasting

### Documents
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/documents`

### Reports
- `GET /api/v1/reports/revenue`
- `GET /api/v1/reports/pipeline`
- `GET /api/v1/reports/inventory`
- `GET /api/v1/reports/chart/revenue`

### Workflows
- `GET/POST /api/v1/workflows/workflows`
- `GET/POST /api/v1/workflows/executions`

### Payments (Stripe)
- `POST /api/v1/payments/create-intent`
- `POST /api/v1/payments/webhook`

### Integrations
- `GET/POST /api/v1/integrations/integrations`
- `GET/POST /api/v1/integrations/webhooks`

### Analytics
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/monthly-trends`

### Admin
- `GET/POST /api/v1/admin/settings`
- `GET /api/v1/admin/activity-logs`
- `GET /api/v1/admin/notifications`
- `GET /api/v1/admin/stats`

### Advanced Search (`/api/v1/search`)
- `POST /` вЂ” Full-text search with filters, facets, pagination
- `GET /?q=` вЂ” GET search endpoint for browser integration
- `GET /suggestions?q=` вЂ” Autocomplete suggestions
- `GET /facets` вЂ” Facet counts for filters
- `POST /reindex` вЂ” Reindex all entities (admin)
- `POST /index/{type}/{id}` вЂ” Index specific entity (admin)
- `GET /analytics` вЂ” Search analytics dashboard
- `GET /analytics/popular-queries` вЂ” Most popular queries

### LLM Integration (`/api/v1/llm`)
- `GET /models` вЂ” List configured models with availability status
- `PUT /models/{id}` вЂ” Update model configuration
- `POST /models/{id}/pull` вЂ” Pull model from Ollama
- `DELETE /models/{id}` вЂ” Remove model configuration
- `POST /chat` вЂ” Send chat with tool support
- `POST /chat/stream` вЂ” Stream chat response (SSE)
- `GET /conversations` вЂ” List user's conversations
- `GET /conversations/{id}` вЂ” Get conversation with messages
- `POST /conversations` вЂ” Create new conversation
- `PUT /conversations/{id}/archive` вЂ” Archive conversation
- `DELETE /conversations/{id}` вЂ” Delete conversation
- `GET /templates` вЂ” List prompt templates
- `GET /templates/{name}` вЂ” Get template
- `POST /templates` вЂ” Create template (admin)
- `DELETE /templates/{id}` вЂ” Delete template (admin)
- `GET /analytics/usage` вЂ” LLM usage analytics
- `GET /analytics/conversations` вЂ” Conversation statistics

### Permissions & RBAC (`/api/v1/permissions`)
- `GET /roles` вЂ” List all roles with permissions
- `POST /roles` вЂ” Create new role
- `GET /roles/{id}` вЂ” Get role details
- `PUT /roles/{id}` вЂ” Update role
- `DELETE /roles/{id}` вЂ” Delete role (superadmin only)
- `GET /permissions` вЂ” List all permissions
- `POST /roles/{id}/permissions` вЂ” Assign permissions to role
- `GET /users/{id}/roles` вЂ” Get user's roles
- `POST /users/{id}/roles` вЂ” Assign roles to user
- `GET /field-permissions` вЂ” List field-level permissions
- `POST /field-permissions` вЂ” Create field permission
- `DELETE /field-permissions/{id}` вЂ” Delete field permission
- `GET /data-policies` вЂ” List data policies
- `POST /data-policies` вЂ” Create data policy
- `PUT /data-policies/{id}/toggle` вЂ” Toggle policy
- `DELETE /data-policies/{id}` вЂ” Delete policy
- `GET /me` вЂ” Get current user's permissions and roles

### Bulk Import/Export
- `POST /api/v1/bulk/import/{entity_type}` - Import CSV/Excel
- `POST /api/v1/bulk/import/{entity_type}/preview` - Validate preview
- `GET /api/v1/bulk/export/{entity_type}?format=` - Export CSV/XLSX/JSON
- `GET /api/v1/bulk/templates/{entity_type}` - Download templates
- `GET /api/v1/bulk/entity-configs` - Field definitions
- `GET /api/v1/bulk/import-history` - Import history

### Migrations (Admin Only)
- `GET /api/v1/migrations/status` - Migration status
- `GET /api/v1/migrations/history` - Revision history
- `GET /api/v1/migrations/versions` - Migration files
- `POST /api/v1/migrations/upgrade` - Apply migrations
- `POST /api/v1/migrations/downgrade` - Revert migrations
- `POST /api/v1/migrations/create` - Create new migration
- `POST /api/v1/migrations/stamp` - Stamp revision

### WebSocket
- `WS /api/v1/ws/{client_id}` - Real-time connection

## Database Schema

20+ tables including:
- `users`, `contacts`, `companies`, `deals`
- `departments`, `employees`
- `products`, `inventory_movements`
- `invoices`, `invoice_items`, `payments`
- `projects`, `tasks`
- `documents`
- `workflows`, `workflow_steps`, `workflow_executions`
- `webhooks`, `webhook_deliveries`
- `integrations`
- `activity_logs`, `notifications`
- `reports`, `forecasts`
- `settings`

## Build History

| Version | Feature | Files |
|---------|---------|-------|
| v1.0 | Core ERP + AI Chat | 45 |
| v1.1 | PostgreSQL, Redis, Email | 55 |
| v1.2 | Document Upload, RAG | 65 |
| v1.3 | Reports, Charts, WebSocket | 75 |
| v1.4 | Workflow Automation | 79 |
| v1.5 | React Frontend | 100 |
| v1.6 | Stripe Payments | 102 |
| v1.7 | PWA + AI Forecasting | 109 |
| v2.1 | Alembic Migrations + Bulk Import/Export | 117 |

## License

MIT

