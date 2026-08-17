# Integration — Bridge

`INTEGRATION/` is the only application bridge between the ERP system of record and the AI/agent system.

## Responsibilities

- versioned API contracts
- request/response schemas
- service-to-service authentication
- ERP client adapters
- event contracts and event-bus adapters
- validation and compatibility checks
- contract tests

## Direction

```text
AI-BACKEND ──> INTEGRATION ──> ERP-BACKEND
                         └──> approved ERP events
```

AI must never import ERP ORM models, repositories, database sessions, migrations, or internal business services.

## Contract rule

If an AI capability requires ERP data or an ERP command, define an explicit integration contract first. No direct database access is an acceptable shortcut.