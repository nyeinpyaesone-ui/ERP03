# ERP Backend

System-of-record backend for ERP03.

## Boundary

- Owns ERP domain, transactions, persistence, authentication, authorization, reporting, and deterministic business workflows.
- Does not host LLM/agent orchestration or direct model calls.
- AI capabilities consume ERP data through the `INTEGRATION/` boundary.

## Runtime

The canonical repository-level Compose configuration builds this service from `./ERP-BACKEND`.
