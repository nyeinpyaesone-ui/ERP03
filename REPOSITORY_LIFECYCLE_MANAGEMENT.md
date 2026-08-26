# Repository Lifecycle Management (RLM) System

## Executive Summary
The ERP03 Repository Lifecycle Management system provides enterprise-grade automation for repository creation, governance enforcement, project status tracking, and version control management. This system separates repository operations from business logic, ensuring clean architecture and maintainability.

## Architecture Overview

### Core Components
1. **Repository Template Engine**: Standardized templates for different project types
2. **Governance Enforcer**: Automated branch protection, required checks, and security policies
3. **Project Status Tracker**: Integration with GitHub Projects for visual management
4. **Webhook Receiver**: Secure event processing with HMAC verification
5. **CI/CD Orchestrator**: Reusable workflows for consistent pipeline execution

### Technology Stack
- **Runtime**: Node.js 20 LTS with TypeScript
- **Queue**: Redis for reliable event processing
- **API**: Express.js for webhook handling
- **Container**: Docker with multi-stage builds
- **Orchestration**: GitHub Actions with reusable workflows

## Directory Structure
```
/workspace
├── .github/
│   ├── ISSUE_TEMPLATE/          # Standardized issue templates
│   ├── workflows/
│   │   ├── repo-lifecycle.yml   # Main lifecycle orchestration
│   │   ├── reusable-*.yml       # Shared workflow components
│   │   └── project-sync.yml     # Project board automation
│   └── PULL_REQUEST_TEMPLATE.md
├── rlm-service/                 # Repository Lifecycle Manager
│   ├── src/
│   │   ├── controllers/         # Request handlers
│   │   ├── middleware/          # Security & validation
│   │   ├── services/            # Business logic
│   │   ├── templates/           # Repository templates
│   │   └── index.ts             # Entry point
│   ├── tests/
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
├── templates/
│   ├── backend-service/         # Backend template
│   ├── frontend-app/            # Frontend template
│   ├── mobile-app/              # Mobile template
│   └── shared-lib/              # Library template
└── docs/
    └── rlm-guide.md             # Usage documentation
```

## Security Model

### Authentication & Authorization
- GitHub App authentication for automated actions
- Repository-scoped tokens with minimal permissions
- HMAC-SHA256 signature verification for webhooks
- Scope validation to prevent cross-repository contamination

### Secret Management
- All secrets stored in GitHub Repository Secrets
- Environment-specific configurations via Codespaces
- Zero secrets in code or configuration files
- Automatic secret rotation support

## Implementation Components

### 1. Webhook Receiver Service
Located: `rlm-service/src/index.ts`

**Features:**
- HMAC signature verification using `WEBHOOK_GITHUB_KEY`
- Repository scope validation
- Async event queuing with Redis
- Forwarding to internal endpoints via `WEBHOOK_GITHUB_URL`
- Health check endpoints for monitoring

**Security Controls:**
- Reject events from unauthorized repositories
- Timing-safe signature comparison
- Rate limiting per repository
- Audit logging for all events

### 2. Repository Template Engine
Located: `rlm-service/src/services/template-engine.ts`

**Template Types:**
- `backend-service`: FastAPI/Node.js backend with CI/CD
- `frontend-app`: React/Next.js with optimized builds
- `mobile-app`: React Native/Expo with EAS Build
- `shared-lib`: TypeScript library with automated publishing

**Template Contents:**
- Pre-configured `.github/workflows/`
- Standardized `Dockerfile` with security best practices
- `.gitignore` patterns for the technology stack
- `README.md` with project structure
- `SECURITY.md` with vulnerability reporting process
- `LICENSE` file (MIT/Apache 2.0)

### 3. Governance Enforcer
Located: `rlm-service/src/services/governance.ts`

**Automated Policies:**
- Branch protection rules for `main` and `develop`
- Required status checks before merge
- Minimum number of approvals (2 for production)
- Disallow force pushes and deletions
- Require signed commits (optional)
- Automatic stale PR management

**Compliance Checks:**
- Security scan requirements (Trivy/Snyk)
- Code coverage thresholds (>85%)
- License compatibility verification
- Dependency vulnerability scanning

### 4. Project Status Tracker
Located: `rlm-service/src/services/project-tracker.ts`

**Integration Points:**
- GitHub Projects V2 (Project #29)
- Automatic card creation for Issues and PRs
- Status updates based on workflow events
- Custom fields for sprint planning

**Status Workflow:**
```
Backlog → In Progress → Code Review → Testing → Done
```

**Automation Triggers:**
- Issue opened → Add to Backlog
- PR created → Move to Code Review
- CI passed → Move to Testing
- PR merged → Move to Done

### 5. CI/CD Orchestrator
Located: `.github/workflows/repo-lifecycle.yml`

**Reusable Workflows:**
- `reusable-tests.yml`: Unit, integration, e2e testing
- `reusable-security.yml`: SAST, DAST, dependency scanning
- `reusable-build.yml`: Multi-platform Docker builds
- `reusable-deploy.yml`: Kubernetes deployments

**Pipeline Stages:**
1. **Quality Gate**: Linting, formatting, type checking
2. **Security Scan**: Vulnerability detection, secret scanning
3. **Test Suite**: Unit, integration, performance tests
4. **Build Artifact**: Container image with SBOM
5. **Deploy**: Staging (auto), Production (manual approval)

## Configuration Requirements

### GitHub Repository Secrets
Required for RLM operation:
```bash
WEBHOOK_GITHUB_KEY=<64-character-hex-secret>
WEBHOOK_GITHUB_URL=https://erp.anynoob.com/webhook/github
GITHUB_APP_ID=<app-id-for-automation>
GITHUB_APP_PRIVATE_KEY=<rsa-private-key>
REDIS_URL=redis://localhost:6379
```

### Environment Variables (`.env.example`)
```bash
# RLM Service Configuration
PORT=3000
NODE_ENV=production
LOG_LEVEL=info

# GitHub Integration
REPO_OWNER=nyeinpyaesone-ui
REPO_NAME=ERP03
PROJECT_NUMBER=29

# Redis Queue
REDIS_URL=redis://localhost:6379
REDIS_QUEUE_NAME=rlm_events

# Security
HMAC_ALGORITHM=sha256
SIGNATURE_HEADER=X-Hub-Signature-256
```

## Operational Procedures

### Creating a New Repository
1. Trigger via GitHub Issue with label `type:new-repo`
2. RLM service validates request and selects template
3. Repository created from template with:
   - Initialized git history
   - Branch protection rules
   - CI/CD workflows
   - Security policies
4. Project card created in Project #29
5. Notification sent to repository owner

### Updating Governance Policies
1. Modify policy definitions in `rlm-service/src/services/governance.ts`
2. Deploy updated RLM service
3. Run audit script to apply changes to existing repositories
4. Generate compliance report

### Monitoring & Alerting
- **Metrics**: Webhook latency, queue depth, success rate
- **Alerts**: Signature failures, queue backups, template errors
- **Logs**: Structured JSON logging with correlation IDs
- **Dashboard**: Grafana dashboard for RLM health

## Disaster Recovery

### Backup Strategy
- Daily export of repository templates
- Weekly backup of Redis queue state
- Monthly audit of governance policies

### Recovery Procedures
1. Restore RLM service from container registry
2. Reconnect to Redis instance
3. Verify webhook configurations
4. Replay missed events from GitHub API

## Compliance & Auditing

### Audit Trail
All RLM operations logged with:
- Timestamp
- Actor (user or automation)
- Action performed
- Target repository
- Result status
- Correlation ID

### Compliance Reports
- Monthly repository governance compliance
- Quarterly security policy adherence
- Annual template usage analysis

## Future Enhancements
- Support for GitLab and Bitbucket
- AI-powered template recommendations
- Automated dependency updates
- Custom workflow builder UI
- Multi-organization support

## Support & Maintenance
- Primary Contact: DevOps Team
- Escalation Path: Platform Engineering
- Documentation: `/docs/rlm-guide.md`
- Incident Response: Follow SECURITY.md procedures

---

*This document is part of the ERP03 Enterprise System. Version 1.0.0*
