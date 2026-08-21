# Developer Onboarding Guide

Welcome to the ERP SOLUTION! This guide will get you productive in under 30 minutes.

## Day 1: Setup (15 minutes)

### 1. Clone and Install
```bash
git clone https://github.com/nyeinpyaesone-ui/ERP.git
cd ERP
./scripts/setup.sh
```

### 2. Start Infrastructure
```bash
docker-compose up -d postgres redis ollama
```

### 3. Verify Setup
```bash
./scripts/gh-manager.sh verify
```

## Day 1: First Contribution (15 minutes)

### 1. Create a Branch
```bash
git checkout -b feature/your-first-feature
```

### 2. Make a Change
Edit any file (e.g., add a comment to `backend/app/main.py`)

### 3. Commit
```bash
git add .
git commit -m "feat: add my first contribution"
```

### 4. Push and PR
```bash
git push origin feature/your-first-feature
# Open PR on GitHub
```

## Project Structure Deep Dive

```
ERP/
├── backend/              # Python FastAPI API
│   ├── app/
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic
│   │   └── ai/           # AI/ML features
│   ├── alembic/          # Database migrations
│   └── tests/            # Pytest tests
│
├── frontend/             # React web app
│   ├── src/
│   │   ├── components/   # Reusable UI
│   │   ├── pages/        # Screen pages
│   │   ├── hooks/        # Custom hooks
│   │   └── modules/      # ERP modules
│   │       ├── bi-dashboard/
│   │       ├── pos/
│   │       ├── mrp/
│   │       └── ecommerce/
│   └── public/
│
├── mobile/               # React Native app
│   ├── src/
│   │   ├── screens/      # App screens
│   │   ├── components/   # Mobile UI
│   │   └── navigation/   # Navigation
│   └── assets/
│
├── infra/                # Kubernetes & Docker
│   └── k8s/              # K8s manifests
│
├── docs/                 # Documentation
│   ├── PRODUCTION_DEPLOYMENT.md
│   ├── API_SUMMARY.md
│   ├── GITHUB_SECRETS.md
│   ├── TESTING.md
│   ├── DATABASE_MIGRATIONS.md
│   ├── TROUBLESHOOTING.md
│   ├── FAQ.md
│   └── ARCHITECTURE_DECISIONS.md
│
├── scripts/              # Management tools
│   ├── gh-manager.sh     # GitHub manager
│   ├── setup.sh          # Environment setup
│   └── verify-push.sh    # Verification
│
├── .github/              # GitHub config
│   ├── workflows/          # CI/CD
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docker-compose.yml    # Full stack
├── Makefile              # Common commands
├── README.md             # Main docs
├── CONTRIBUTING.md       # Team workflow
├── CHANGELOG.md          # Version history
├── CODE_OF_CONDUCT.md    # Community standards
├── SECURITY.md           # Security policy
├── ROADMAP.md            # Future plans
├── LICENSE               # MIT License
└── .env.example          # Config template
```

## Development Workflow

### Daily Workflow
```bash
# 1. Sync with main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Develop and test
make dev        # Start services
make test       # Run tests

# 4. Commit and push
git add .
git commit -m "feat: my feature"
git push origin feature/my-feature

# 5. Open PR on GitHub
```

### Code Review Checklist
- [ ] Code follows style guide (PEP 8, TypeScript strict)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.log or print statements
- [ ] Error handling implemented
- [ ] Security considerations addressed

## Key Commands

| Command | Purpose |
|---------|---------|
| `make dev` | Start development environment |
| `make test` | Run all tests |
| `make build` | Build production images |
| `make push` | Quick push to GitHub |
| `make clean` | Clean build artifacts |
| `./scripts/gh-manager.sh status` | Show repo status |
| `./scripts/gh-manager.sh verify` | Full verification |
| `./scripts/gh-manager.sh log` | Show commit history |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend API | Python 3.11, FastAPI, SQLAlchemy |
| Frontend | React 18, TypeScript, Vite, Tailwind |
| Mobile | React Native, Expo |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| AI/ML | Ollama, OpenAI API |
| DevOps | Docker, Kubernetes, GitHub Actions |
| Testing | Pytest, Jest, Playwright |

## Getting Help

1. **Documentation**: Check `docs/` directory
2. **FAQ**: See `docs/FAQ.md`
3. **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
4. **GitHub Issues**: https://github.com/nyeinpyaesone-ui/ERP/issues
5. **Team Chat**: [Your team chat link]
6. **Email**: nyeinpyaesone273@gmail.com

## First Week Goals

- [ ] Complete setup and verify all services run
- [ ] Make first contribution (documentation fix counts!)
- [ ] Review `docs/ARCHITECTURE_DECISIONS.md`
- [ ] Attend team standup
- [ ] Pick up first real task from backlog

Welcome aboard! 🚀
