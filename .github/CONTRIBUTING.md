# Contributing to ERP03

Thank you for contributing to ERP03! This document provides guidelines and processes for contributors.

## 🏗️ Architecture Principles

Before contributing, understand our core architectural rules:

1. **ERP is Authoritative**: All writes, auth, workflows, and audit trails flow through ERP-BACKEND
2. **AI is Isolated**: AI never imports ERP ORM models or connects directly to ERP database
3. **Contract-Based Communication**: All cross-service interaction via versioned contracts in `INTEGRATION/`
4. **Single Source of Truth**: AI maintains only derived state; ERP remains sole system of record

## 🚀 Getting Started

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/erp03.git
cd erp03
```

### 2. Setup Development Environment
```bash
cp .env.example .env
# Edit .env with your local configuration
make dev
```

### 3. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

## 📝 Development Guidelines

### Code Style
- **Python**: Follow PEP 8, use type hints, run `black` and `flake8`
- **TypeScript**: Follow ESLint config, use strict mode
- **Commit Messages**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

### Testing Requirements
- Write unit tests for all new functions/classes
- Add integration tests for cross-module changes
- Maintain >85% code coverage on backend
- Tests must pass before pushing:
  ```bash
  make test
  ```

### Security Checklist
- [ ] No hardcoded secrets
- [ ] Input validation on all user inputs
- [ ] Authentication checks on protected endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Dependencies pinned to specific versions

## 🔄 Pull Request Process

### 1. Before Submitting
- [ ] Code reviewed against [CODE_REVIEW_CHECKLIST.md](./CODE_REVIEW_CHECKLIST.md)
- [ ] All tests passing locally
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] Branch rebased on latest `main`

### 2. PR Template
Fill out the pull request template completely:
- Description of changes
- Related issues
- Testing performed
- Screenshots (if UI changes)

### 3. Review Process
1. Automated CI/CD checks must pass
2. At least 1 maintainer approval required
3. Address all review comments
4. Squash commits if necessary

### 4. Merging
- Maintainers will merge approved PRs
- Delete feature branch after merge
- Monitor production deployment if applicable

## 🐛 Reporting Bugs

### Bug Report Template
- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed reproduction steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, Docker version
- **Logs**: Relevant error logs
- **Screenshots**: If applicable

### Security Vulnerabilities
**DO NOT** open public issues for security vulnerabilities. Email nyeinpyaesone273@gmail.com directly.

## 💡 Feature Requests

### Feature Request Template
- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: How should it work?
- **Alternatives Considered**: Other approaches
- **Use Cases**: Who will use this and how?
- **Acceptance Criteria**: How do we know it's done?

## 📚 Documentation

### Updating Docs
- Keep README.md up-to-date
- Update API docs in `docs/API_SUMMARY.md`
- Add migration guides for breaking changes
- Include examples for new features

### Documentation Standards
- Clear, concise language
- Code examples with expected output
- Screenshots for UI features
- Troubleshooting section for common issues

## 🎯 Areas Needing Contribution

### High Priority
- [ ] Finance module backend implementation
- [ ] Real-time WebSocket dashboard
- [ ] Multi-tenant SaaS isolation
- [ ] Kubernetes auto-scaling policies
- [ ] AI integration contracts (M2)

### Medium Priority
- [ ] Enhanced reporting/analytics
- [ ] Mobile app feature parity
- [ ] Advanced search capabilities
- [ ] Audit log visualization
- [ ] Backup automation scripts

### Low Priority
- [ ] Theme customization
- [ ] Additional language support
- [ ] Social media integrations
- [ ] Advanced workflow designer

## 🏆 Recognition

Contributors will be recognized in:
- CHANGELOG.md
- README.md contributors section
- Annual contributor highlights

## ❓ Questions?

- Check existing documentation in `/docs`
- Review closed issues for similar questions
- Join discussion in GitHub Discussions
- Contact maintainers for urgent matters

## 📜 License

By contributing, you agree that your contributions will be licensed under the project's proprietary license.
