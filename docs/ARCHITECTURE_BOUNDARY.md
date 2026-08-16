# ERP03 Architecture Boundary

Target structure from the supplied architecture diagrams:

PROJECT/
- ERP-BACKEND/ — ERP system of record
- AI-BACKEND/ — AI and agent system
- INTEGRATION/ — only ERP-to-AI bridge
- INFRASTRUCTURE/ — runtime and platform services
- docs/ — architecture documentation
- backend/ — legacy implementation during migration

Dependency rule: ERP-BACKEND <- INTEGRATION <- AI-BACKEND.

ERP owns authoritative commands, validation, authorization, transactions, persistence, and audit. AI must not access ERP database or repositories directly.

Migration is incremental. Existing backend, backend-v1.8, and backend-v2.1 are preserved until replacement behavior is tested and cut over.