# Code Review Checklist

**All PRs must satisfy these requirements before merging.**

## 🔒 Security (Mandatory)
- [ ] No hardcoded secrets, API keys, or passwords
- [ ] Environment variables used for configuration
- [ ] Input validation on all user inputs
- [ ] Authentication/authorization checks on protected endpoints
- [ ] SQL injection prevention (parameterized queries only)
- [ ] XSS prevention (proper escaping in frontend)
- [ ] CORS configured correctly
- [ ] Rate limiting applied to auth endpoints
- [ ] Dependencies pinned to specific versions
- [ ] No sensitive data in logs

## ⚡ Performance
- [ ] Database queries use indexes where appropriate
- [ ] N+1 query problems avoided (use eager loading)
- [ ] Large datasets paginated
- [ ] Async operations used for I/O-bound tasks
- [ ] Caching strategy documented if applicable
- [ ] No unnecessary computations in loops

## 🧪 Testing
- [ ] Unit tests added for new functionality
- [ ] Integration tests for cross-module changes
- [ ] Test coverage maintained or improved (>85% backend)
- [ ] Edge cases covered (empty inputs, errors, boundaries)
- [ ] Tests pass locally before pushing
- [ ] Mock external services appropriately

## 📝 Documentation
- [ ] README updated if architecture changed
- [ ] API endpoints documented (OpenAPI/Swagger)
- [ ] Environment variables documented
- [ ] Migration steps documented if schema changed
- [ ] Changelog entry added

## 🏗️ Architecture
- [ ] Follows ERP ← INTEGRATION ← AI dependency rule
- [ ] No direct database access from AI-BACKEND
- [ ] Service layer patterns followed
- [ ] Proper error handling with context
- [ ] Logging includes correlation IDs
- [ ] Type hints used consistently

## 🐳 Docker & Deployment
- [ ] Dockerfile uses multi-stage builds
- [ ] Non-root user in containers
- [ ] Health checks defined
- [ ] .dockerignore excludes unnecessary files
- [ ] docker-compose.yml validated
- [ ] Migrations tested in CI

## ✅ Final Checks
- [ ] Code follows project style guide (black, flake8)
- [ ] No console.log() or debug statements in production code
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up-to-date with main
- [ ] All CI/CD checks passing

**Reviewer:** _________________  
**Date:** ____________________  
**Approved:** ☐ Yes  ☐ No  ☐ Request Changes
