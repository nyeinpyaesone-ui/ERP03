# Testing Guide

## Testing Strategy

### Unit Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=html
```

### Integration Tests
```bash
cd backend
pytest tests/integration/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### E2E Tests
```bash
cd frontend
npx playwright test
```

### Mobile Tests
```bash
cd mobile
npm test
```

## Test Coverage Targets
| Module | Target |
|--------|--------|
| Backend API | 85% |
| Frontend Components | 80% |
| Mobile Screens | 75% |
| Integration | 70% |

## CI/CD Testing
Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Before release tagging

## Manual Testing Checklist
- [ ] User registration and login
- [ ] Inventory CRUD operations
- [ ] Order creation and processing
- [ ] Report generation
- [ ] Mobile app sync
- [ ] AI chat functionality
- [ ] Multi-tenant isolation
