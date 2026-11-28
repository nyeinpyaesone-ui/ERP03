# Unified ERP Product Blueprint

## Product reference

The uploaded ERP Solutions v1.2.0 LTS codebase is the product/UI reference:
- React + Vite + Tailwind workspace and its dashboard/navigation patterns.
- POS sales, product catalog, inventory, customer management and reporting.
- Sammy assistant entry point.
- Myanmar-first defaults, MMK and branch-aware business operations.

The reference's static sample data and chatbot canned responses are not authoritative business behavior. ERP03 PostgreSQL domain services are the source of truth.

## Target architecture

Keep ERP03 as a modular monolith:
- Frontend: existing React 19 + Vite + Tailwind application.
- API: existing FastAPI application in \`ERP-BACKEND/\`.
- Persistence: PostgreSQL + SQLAlchemy async + Alembic; SQLite remains a local compatibility/test path.
- Cache and rate limiting: existing Redis integration.
- Identity: ERP03 users, businesses, branches, roles and permissions remain authoritative. Supabase Auth is an optional linked identity provider.
- Operations: existing audit, request IDs, metrics and durable orchestration remain platform concerns.

Do not migrate to Next.js or split into microservices as part of this product integration. Preserve the established build and deployment contract.

## Domain boundaries

| Domain | Existing ERP03 source of truth | Product workspace |
|---|---|---|
| Business profile | \`models/identity.py\` | Business context and branch selection |
| Catalog | \`models/erp.py\`, \`services/catalog.py\` | Product and customer CRUD |
| POS / sales | \`services/sales.py\` | Real invoice creation and sales history |
| Inventory | \`services/inventory.py\`, stock tables | Warehouse stock balances and alerts |
| Purchasing | \`services/receiving.py\` | Purchase receipt workflow |
| Identity / access | \`api/auth.py\`, RBAC services | ERP login and optional Supabase identity |
| Audit / operations | audit middleware and operations state machine | Traceable business activity |
| Reporting | tenant-scoped operational read models | Dashboard metrics |

## Implemented in this integration

- New business registration provisions a default Main Branch and Main Warehouse in the same transaction.
- Authenticated business context returns only branches and warehouses available to the current user.
- Product and customer screens use tenant-scoped APIs instead of hardcoded demo records.
- Inventory screen reads stock balances from the authoritative warehouse/product tables.
- POS checkout posts to the existing atomic sales service with an idempotency key.
- Sales history is read from persisted invoices and payments.
- Dashboard summary is calculated from tenant-scoped ERP records and the business timezone/currency.
- Catalog, purchase receipt and product activation routes own explicit transaction boundaries; the request-session dependency does not auto-commit.
- Catalog writes validate branch ownership and branch assignments; list operations are branch-scoped for assigned users.
- Operational read endpoints require authentication and applicable permissions.

## Remaining product capabilities

These are not claimed complete by the current integration:
- Customer debt collection against existing invoices with a separate payment/idempotency workflow.
- Supplier payable accrual and supplier payment records.
- Double-entry accounting, chart of accounts and period controls.
- Daily cash closing and reconciliation.
- Myanmar language translation coverage and localized date/number formats across every screen.
- Local payment-provider adapters and reconciliation.
- Sammy read-only ERP query tools backed by authenticated data, not canned sample answers.
- Capability registry/compiler, context compiler, policy decision workflow, approval workflow and Control Tower integration where not already implemented.
- Full E2E qualification against PostgreSQL, Redis, Supabase staging and production-like containers.

## Correctness and security invariants

1. Every query is scoped by the authenticated business; branch-scoped users cannot select another branch.
2. Writes validate that the referenced branch, warehouse, customer and product belong to the same business/branch.
3. POS sale, invoice, payment and stock movement commit atomically.
4. Retried writes require stable idempotency keys and payload matching.
5. Monetary values use Decimal/Numeric, never binary floating point for server-side calculations.
6. MMK and Asia/Yangon are defaults, not hardcoded assumptions for every tenant.
7. Supabase metadata never grants ERP roles or branch access.
8. Schema changes use reviewed Alembic migrations; application startup does not create production tables.
9. Demo data must never be presented as live business data.
10. Keep PR #304 in draft until required CI and isolated staging validation are complete.

## Required verification

Run the repository's canonical gate from the root:
\`\`\`bash
bash scripts/agent/bootstrap.sh
bash scripts/agent/verify.sh
\`\`\`

For a release candidate, additionally verify:
- PostgreSQL migration upgrade and downgrade from a clean database.
- POS idempotency replay and duplicate-key payload mismatch.
- Concurrent stock deduction and invoice-number allocation.
- Branch isolation across two businesses and two branches.
- Frontend production build and browser E2E for onboarding → catalog → receipt → POS → dashboard.
- Supabase linked-identity flow in an isolated staging project.
- Container build and amd64/arm64 image manifest verification.

A successful code commit is not evidence that these release gates passed.
