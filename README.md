# ERP03 - Enterprise Resource Planning System

**Production-ready ERP platform with strict architectural boundaries between transactional systems and AI capabilities.**

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd erp03
cp .env.example .env

# Start development environment
make dev

# Or using Docker Compose directly
docker compose up -d
```

## Access Points

| Service | URL | Port |
|---------|-----|------|
| ERP Backend API | http://localhost:8000 | 8000 |
| Frontend Web App | http://localhost:3000 | 3000 |
| PostgreSQL | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |
| Ollama LLM | http://localhost:11434 | 11434 |

## Build System Commands

```bash
make help          # Show all available commands
make dev           # Start development environment
make prod          # Start production environment
make test          # Run full test suite
make migrate       # Run database migrations
make up            # Start all services
make down          # Stop all services
make logs          # Follow service logs
make shell         # Open backend container shell
make db-shell      # Open PostgreSQL shell
make backup        # Create database backup
make health        # Check service health
make clean         # Clean all artifacts
make push          # Build and push Docker images
make seed          # Seed database with initial data
```

## Architecture

ERP03 follows strict architectural boundaries:

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   AI-BACKEND    │ ←── │ INTEGRATION  │ ←── │ ERP-BACKEND │
│  (Agent Platform)│     │  (Contracts) │     │(System of Record)│
└─────────────────┘     └──────────────┘     └─────────────┘
```

**Key Principles:**
- ERP is the authoritative System of Record
- AI operates on derived state only
- All cross-service communication via versioned contracts
- No direct database access between services

## Core Modules

- **Authentication & Authorization** - JWT-based auth with RBAC
- **CRM** - Company and contact management
- **HR** - Employee management and payroll
- **Inventory** - Stock management with GMP/FDA compliance
- **Finance** - Accounting and financial operations
- **Projects** - Project management and tracking
- **AI Integration** - LLM-powered features via isolated agent platform

## Testing

```bash
# Run all tests
make test

# Run with coverage
docker compose run --rm backend pytest -v --cov=app

# Run specific test file
docker compose run --rm backend pytest tests/test_auth.py -v
```

## Deployment

### Development
```bash
make dev
```

### Production
```bash
# Build and deploy
make prod

# Or with Kubernetes
kubectl apply -f infrastructure/kubernetes/base/
```

### Container Registry
```bash
# Push to GHCR
make push
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
POSTGRES_USER=erp
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=erp_solution
DATABASE_URL=postgresql://erp:<password>@postgres:5432/erp_solution
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<32-random-characters>
ENVIRONMENT=production
DEBUG=false
```

## Documentation

- [Architecture](docs/ARCHITECTURE_BOUNDARY.md)
- [Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)
- [API Documentation](docs/API_SUMMARY.md)
- [Onboarding](docs/ONBOARDING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## License

Proprietary - All rights reserved

## Support

For issues and questions, please refer to the documentation or contact the development team.
