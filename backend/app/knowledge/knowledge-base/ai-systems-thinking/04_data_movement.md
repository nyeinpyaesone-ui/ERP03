# 04 — How Data Moves Inside an AI System

## The Data Flow Model

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │───→│  Ingestion   │───→│  Knowledge  │───→│   Agent     │
│  (DB/API)   │    │  (ETL/API)   │    │    Store    │    │  (Process)  │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                                                              │
                                                              ↓
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Action    │←───│   Approval    │←───│   Output    │←───│  Reasoning  │
│  (Execute)  │    │   (Human/AI)  │    │  (Format)   │    │  (LLM/Rule) │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                                                              │
                                                              ↓
                                                        ┌─────────────┐
                                                        │   Audit     │
                                                        │    Log      │
                                                        └─────────────┘
```

## Data States

| State | Description | Example |
|-------|-------------|---------|
| **Raw** | Unstructured, unvalidated | User chat message, uploaded PDF |
| **Structured** | Validated against schema | JSON with contact_id, amount, date |
| **Enriched** | Augmented with context | Invoice + tax rates + customer history |
| **Processed** | Transformed by AI | Generated invoice text, calculated totals |
| **Reviewed** | Checked by human or reviewer | Approved invoice with signature |
| **Actioned** | Committed to system | Saved to DB, sent to customer |
| **Archived** | Immutable record | Audit log entry with hash |

## Data Lineage

Every piece of data must be traceable:
- **Origin** — Where did this data come from?
- **Transformations** — What changed it along the way?
- **Agents** — Which AI or human touched it?
- **Timestamp** — When did each step happen?
- **Confidence** — How certain was the AI at each step?

## Implementation in ERP SOLUTION

1. **Source Layer** — PostgreSQL tables (contacts, invoices, townships, tax_rates)
2. **Ingestion Layer** — FastAPI endpoints validate and normalize inputs
3. **Knowledge Store** — pgvector embeddings + structured tables for agent context
4. **Agent Layer** — Specialist agents query knowledge store, apply skills
5. **Output Layer** — Structured JSON responses formatted per output_schema
6. **Approval Layer** — Configurable gates based on confidence + rules
7. **Action Layer** — Executors commit to DB, send notifications, generate PDFs
8. **Audit Layer** — Immutable append-only logs with hash chains

## Critical Rule

> **Never let AI modify production data without an audit trail.**
> Every CREATE, UPDATE, DELETE must be logged with: actor, old_values, new_values, reason, timestamp, hash.

