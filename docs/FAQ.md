# Frequently Asked Questions

## General

### What is ERP SOLUTION?
An enterprise-grade AI-powered ERP system with 12 modules covering inventory, orders, customers, manufacturing, POS, e-commerce, and AI features.

### Is it production-ready?
Yes! v1.0.0 is production-ready with full CI/CD, Docker support, and Kubernetes manifests.

### What technologies are used?
- Backend: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Redis
- Frontend: React 18+, TypeScript, Tailwind CSS
- Mobile: React Native, Expo
- AI: Ollama, OpenAI API
- DevOps: Docker, Kubernetes, GitHub Actions

## Development

### How do I set up locally?
```bash
git clone https://github.com/nyeinpyaesone-ui/ERP.git
cd ERP
./scripts/setup.sh
docker-compose up -d
```

### How do I contribute?
See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

### What's the commit convention?
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `style:` — Formatting
- `refactor:` — Code restructuring
- `test:` — Tests
- `chore:` — Maintenance

## Deployment

### How do I deploy to production?
See [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for Docker, Kubernetes, and cloud deployment guides.

### Can I use my own domain?
Yes! Configure DNS and SSL as described in the deployment guide.

### How do I update?
```bash
git pull origin main
docker-compose up -d --build
```

## AI Features

### What AI capabilities are included?
- Demand forecasting
- AI chat assistant
- RAG document query
- Agent orchestration
- Anomaly detection

### Do I need OpenAI API key?
Optional. The system works with Ollama (local) by default. Add OpenAI key for GPT-4 features.

## Licensing

### Is it free?
Yes, licensed under MIT. You can use, modify, and distribute freely.

### Can I use it commercially?
Yes, MIT license permits commercial use.


## Contact

- Email: nyeinpyaesone273@gmail.com
- LinkedIn: https://linkedin.com/in/nyein-pyae-sone-3250501ba
- GitHub: https://github.com/nyeinpyaesone-ui/ERP
- Phone: +959699795380
