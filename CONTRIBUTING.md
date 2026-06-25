# Contributing to ERP SOLUTION

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ERP.git`
3. Run setup: `./scripts/setup.sh`
4. Create a branch: `git checkout -b feature/your-feature`

## Development Workflow

```bash
# Start services
docker-compose up -d postgres redis

# Terminal 1 — Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev

# Terminal 3 — Mobile (optional)
cd mobile
npx expo start
```

## Commit Convention

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `style:` — Formatting
- `refactor:` — Code restructuring
- `test:` — Tests
- `chore:` — Maintenance

Example: `feat: add inventory forecasting module`

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure CI passes
4. Request review from maintainers

## Code Standards

- Python: PEP 8, type hints, docstrings
- TypeScript: Strict mode, functional components
- Tests: 80%+ coverage target


## Contact

- Email: nyeinpyaesone273@gmail.com
- LinkedIn: https://linkedin.com/in/nyein-pyae-sone-3250501ba
- GitHub: https://github.com/nyeinpyaesone-ui/ERP
- Phone: +959699795380
