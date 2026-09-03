# ERP03 — Enterprise Resource Planning Platform with AI Integration

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115.6-green.svg)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/react_native-0.73-blue.svg)](https://reactnative.dev/)
[![Docker](https://img.shields.io/badge/docker--compose-ready-blue.svg)](https://docs.docker.com/compose/)
[![CodeQL](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/codeql.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/codeql.yml)

## Overview

**ERP03** is a modular enterprise resource planning (ERP) platform designed with a clear architectural boundary between the transactional ERP system of record and an external AI/agent platform. The system ensures data integrity, auditability, and secure integration patterns for enterprise deployments.

### Key Features

- **System of Record Architecture**: Authoritative transactional database with ACID compliance
- **AI Integration Boundary**: Clean separation between ERP core and AI/agent systems
- **Modular Design**: Independent modules for CRM, HR, Inventory, Finance, Projects, Analytics
- **Real-time Communication**: WebSocket support for live updates
- **Multi-platform Frontend**: React Native mobile app + React web dashboard
- **Production Ready**: Docker Compose, Nginx reverse proxy, Prometheus metrics
- **Security First**: RBAC, JWT authentication, audit logging, structured JSON logs

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Git
- (Optional) Node.js 18+ for frontend development
- (Optional) Python 3.12 for backend development

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/nyeinpyaesone-ui/ERP03.git
cd ERP03

# 2. Configure environment
cp .env.example .env
# Edit .env with your secrets (SECRET_KEY, DATABASE_URL, etc.)

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec erp-backend alembic upgrade head

# 5. Verify health
./scripts/health-check.sh
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **ERP API** | http://localhost:8000 | FastAPI REST backend |
| **Frontend** | http://localhost:3000 | React web dashboard |
| **PostgreSQL** | localhost:5432 | Primary database |
| **Redis** | localhost:6379 | Cache & session store |
| **Ollama** | http://localhost:11434 | Local LLM runtime |
| **Metrics** | http://localhost:8000/metrics | Prometheus endpoint |

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Mobile     │  │     Web      │  │  External    │          │
│  │  (React Nat) │  │  (React.js)  │  │   Systems    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                             │
│         (Authentication, Contracts, Event Bus)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     ERP-BACKEND         │     │      AI-BACKEND         │
│  (System of Record)     │     │   (AI / Agents)         │
│                         │     │                         │
│ • Transactions          │     │ • Inference             │
│ • Validation            │     │ • Predictions           │
│ • Authorization (RBAC)  │◄────│ • Recommendations       │
│ • Audit Logging         │     │ • Pattern Detection     │
│ • PostgreSQL + Redis    │     │ • Separate State        │
└─────────────────────────┘     └─────────────────────────┘
```

### Core Principles

1. **ERP owns truth**: All authoritative writes flow through ERP-BACKEND
2. **No direct DB access**: AI systems interact via authenticated contracts only
3. **Audit everything**: Every transaction logged with correlation IDs
4. **Fail safely**: Rollback on errors, no partial state
5. **Independent deployability**: ERP can run without AI, and vice versa

### Directory Structure

```
ERP03/
├── ERP-BACKEND/          # Core ERP system (FastAPI + PostgreSQL)
│   ├── app/
│   │   ├── routers/      # API endpoints (auth, crm, hr, inventory...)
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic layer
│   │   └── config.py     # Settings management
│   ├── alembic/          # Database migrations
│   └── requirements.txt
│
├── AI-BACKEND/           # AI agents and ML services
│   ├── agents/           # Autonomous agent implementations
│   ├── api/              # AI service endpoints
│   ├── models/           # ML model definitions
│   └── orchestrator/     # Agent coordination
│
├── INTEGRATION/          # ERP ↔ AI bridge layer
│   ├── contracts/        # API contracts (OpenAPI/YAML)
│   ├── authentication/   # Auth middleware
│   ├── event-bus/        # Async event streaming
│   └── erp-client/       # ERP API client library
│
├── INFRASTRUCTURE/       # Platform services
│   ├── docker/           # Container configurations
│   └── nginx/            # Reverse proxy configs
│
├── frontend/             # React web dashboard
├── mobile/               # React Native mobile app
├── docs/                 # Architecture & developer docs
├── scripts/              # DevOps utilities
└── tests/                # Integration & E2E tests
```

---

## Technology Stack

### Backend (ERP-BACKEND)

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.115.6 |
| Language | Python | 3.12 |
| ORM | SQLAlchemy | 2.0.37 |
| Database | PostgreSQL | 15.18 |
| Cache | Redis | 7.4.9 |
| Migrations | Alembic | 1.14.0 |
| Auth | python-jose + passlib | Latest |
| Validation | Pydantic | 2.13.4 |
| Metrics | Prometheus Client | 0.26.0 |
| Payments | Stripe SDK | 15.4.0 |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Mobile | React Native + Expo | 0.73 / 57.0 |
| Web | React.js | 18+ |
| Navigation | React Navigation | 7.x |
| State | Zustand + TanStack Query | Latest |
| UI | React Native Paper | 5.11.0 |
| Charts | react-native-chart-kit | 7.0.1 |

### Infrastructure

| Component | Technology | Version |
|-----------|------------|---------|
| Containers | Docker Compose | v2+ |
| Reverse Proxy | Nginx | Latest |
| LLM Runtime | Ollama | 0.32.5 |
| CI/CD | GitHub Actions | Latest |
| Security | CodeQL | v4 |

---

## Development

### Running Tests

```bash
# Backend unit tests
docker compose exec erp-backend pytest

# Integration tests
./tests/run-integration-tests.sh

# Frontend tests
cd mobile && npm test
```

### Code Quality

```bash
# Type checking
docker compose exec erp-backend mypy app

# Linting
docker compose exec erp-backend ruff check app

# Format
docker compose exec erp-backend black app
```

### Database Operations

```bash
# Create new migration
docker compose exec erp-backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec erp-backend alembic upgrade head

# Rollback one migration
docker compose exec erp-backend alembic downgrade -1

# View migration history
docker compose exec erp-backend alembic history
```

### Environment Variables

Key variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://erp:password@postgres:5432/erpo3
POSTGRES_USER=erp
POSTGRES_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development  # or production
DEBUG=true
```

See `.env.example` for full list.

---

## Deployment

### Production Deployment

For production setup, see [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md):

```bash
# Use production compose file
docker compose -f compose.production.yml up -d

# Run health checks
./scripts/health-check.sh

# Monitor logs
docker compose logs -f erp-backend
```

### Key Production Considerations

- ✅ Set `ENVIRONMENT=production` and `DEBUG=false`
- ✅ Use strong SECRET_KEY (min 32 chars, cryptographically random)
- ✅ Configure SSL/TLS termination at Nginx
- ✅ Enable database connection pooling
- ✅ Set up log aggregation (ELK, Loki, etc.)
- ✅ Configure backup strategy for PostgreSQL
- ✅ Monitor Prometheus metrics + alerts

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Boundary](docs/ARCHITECTURE_BOUNDARY.md) | System boundaries and dependency rules |
| [Testing Guide](docs/TESTING.md) | Test strategies and execution |
| [Production Setup](docs/PRODUCTION_SETUP.md) | Production deployment checklist |
| [Roadmap](ROADMAP.md) | Product roadmap and milestones |
| [Onboarding](docs/ONBOARDING.md) | New developer guide |
| [API Summary](docs/API_SUMMARY.md) | Endpoint reference |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |
| [FAQ](docs/FAQ.md) | Frequently asked questions |

---

## Contributing

We welcome contributions! Please see:

1. [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
2. [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community standards
3. [SECURITY.md](SECURITY.md) - Security policy

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with clear messages
4. Push to your branch
5. Open a Pull Request with description
6. Ensure CI passes (CodeQL, container build)
7. Request review from maintainers

---

## Status & Roadmap

### Current Status (M0 Complete)

- ✅ Architecture baseline established
- ✅ ERP-BACKEND runtime stabilized
- ✅ AI-BACKEND boundary enforced
- ✅ Legacy backends removed from main
- ✅ Docker & CI/CD pipelines operational

### Next Milestone (M1 - ERP Core Stabilization)

- 🔄 Inventory route/service/model audit
- 🔄 Transaction rollback testing
- 🔄 API contract tests for critical paths
- 🔄 Migration reproducibility verification

See [ROADMAP.md](ROADMAP.md) for detailed timeline.

---

## Security

### Reporting Vulnerabilities

Please report security issues responsibly:
- Email: [security contact]
- Do not open public issues for security vulnerabilities

### Security Features

- JWT-based authentication with configurable expiry
- Role-Based Access Control (RBAC)
- Password hashing with bcrypt
- CORS configuration
- Input validation via Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- Structured audit logging
- CodeQL static analysis in CI

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2026 ERP03 Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Support & Community

- 📧 Issues: [GitHub Issues](https://github.com/nyeinpyaesone-ui/ERP03/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/nyeinpyaesone-ui/ERP03/discussions)
- 📖 Docs: [/docs](/docs) directory

---

**Built with ❤️ using FastAPI, React Native, and PostgreSQL**
