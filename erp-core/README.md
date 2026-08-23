# ERP-CORE System

Enterprise Resource Planning Core System with Domain-Driven Design architecture.

## Architecture

### Core Business Domains
1. **Identity & Access Management (IAM)** - Users, Roles, Permissions, Authentication
2. **Finance & Accounting** - Chart of Accounts, Journal Entries, Invoices, Payments
3. **Human Capital Management (HCM)** - Employees, Payroll, Leave (planned)
4. **Supply Chain Management** - Inventory, Products, Warehouses (planned)
5. **Customer Relationship Management (CRM)** - Companies, Contacts, Deals (planned)

### Technical Features
- FastAPI backend with async support
- PostgreSQL database with SQLAlchemy ORM
- Redis caching
- JWT authentication with RBAC
- Plugin system for extensibility
- Docker Compose for local development

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose
```bash
cd erp-core
docker compose up -d
```

Access the API at http://localhost:8000

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the application
uvicorn app.main:app --reload
```

## API Endpoints

### Identity & Access
- `POST /api/v1/identity/register` - Register new user
- `POST /api/v1/identity/login` - Authenticate user
- `GET /api/v1/identity/me` - Get current user profile
- `PUT /api/v1/identity/me` - Update current user
- `GET /api/v1/identity/roles` - List all roles
- `POST /api/v1/identity/roles` - Create role
- `GET /api/v1/identity/permissions` - List all permissions

### Health Check
- `GET /api/v1/health` - System health status

## Project Structure

```
erp-core/
├── app/
│   ├── core/              # Configuration, database
│   ├── domain/            # Business domains
│   │   ├── identity/      # IAM domain
│   │   │   ├── model/     # SQLAlchemy models
│   │   │   ├── schema/    # Pydantic schemas
│   │   │   ├── service/   # Business logic
│   │   │   ├── repository/# Data access layer
│   │   │   └── api/       # FastAPI routers
│   │   └── finance/       # Finance domain
│   ├── plugins/           # Plugin system
│   └── main.py            # Application entry point
├── seeds/                 # Initial data seeds
├── alembic/               # Database migrations
├── tests/                 # Test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

Proprietary - All rights reserved
