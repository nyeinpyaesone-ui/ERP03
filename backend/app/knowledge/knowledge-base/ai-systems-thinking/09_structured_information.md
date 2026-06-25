# 09 — How AI Understands Structured Information

## The Problem

AI (LLMs) are trained on unstructured text. They excel at:
- Understanding natural language
- Generating coherent text
- Reasoning about concepts

They struggle with:
- Exact numerical precision
- Strict schema adherence
- Deterministic rule application
- Tabular data manipulation

## The Solution: Hybrid Architecture

```
┌─────────────────────────────────────────────────────────┐
│  UNSTRUCTURED (AI/LLM)        │  STRUCTURED (Rules/DB)   │
├─────────────────────────────────────────────────────────┤
│  • Intent recognition           │  • Schema validation     │
│  • Context understanding        │  • Exact calculations    │
│  • Natural language generation  │  • Database queries      │
│  • Summarization                │  • Business rules        │
│  • Anomaly detection            │  • Compliance checks     │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  ORCHESTRATOR    │
                    │  (Routes tasks   │
                    │   to right layer)│
                    └──────────────────┘
```

## Structured Information Types in ERP SOLUTION

### 1. Relational Data (PostgreSQL)
- Contacts, companies, invoices, products
- Strict schema, ACID transactions, foreign keys
- **AI uses**: Read for context, never write directly (goes through API)

### 2. Vector Embeddings (pgvector)
- Semantic representations of documents, queries, knowledge
- Similarity search, clustering, retrieval
- **AI uses**: Find relevant context, match intents, recommend

### 3. Knowledge Graph (implied)
- Entities and relationships: Company → has → Contacts, Invoice → belongs_to → Company
- Path traversal, inference, reasoning
- **AI uses**: Understand business relationships, validate consistency

### 4. Configuration (JSONB)
- Feature flags, model settings, thresholds, rules
- Hierarchical: global → tenant → user
- **AI uses**: Adjust behavior per context, enable/disable features

### 5. Audit Logs (Append-only)
- Immutable, hashed, time-ordered
- **AI uses**: Learn from past decisions, detect patterns, prove compliance

## How to Feed Structure to AI

### Method 1: Schema Injection
```
System prompt: "You are a Finance Officer. You have access to the following schema:

Table: invoices
  id: UUID
  contact_id: UUID → contacts.id
  total: NUMERIC(12,2)
  tax_amount: NUMERIC(12,2)
  status: ENUM ['draft','sent','paid','overdue']

Current tax rates:
  CT: 5% on sales
  CIT: 22% on net profit

You must output valid JSON matching this schema: {...}"
```

### Method 2: Function Calling
```python
# AI decides to call a function
functions = [
    {
        "name": "calculate_tax",
        "description": "Calculate tax for a transaction",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "tax_types": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["amount", "tax_types"]
        }
    }
]

# AI outputs: call calculate_tax(amount=2990, tax_types=["CT"])
# System executes: exact SQL function, returns precise result
# AI receives: {"CT": 149.50, "total": 3139.50}
```

### Method 3: Retrieval-Augmented Generation (RAG)
```
User query: "What is the delivery fee to Taunggyi?"
    ↓
Vector search: query_embedding → townships table
    ↓
Retrieved context: "Taunggyi (SHN-001), Shan State, Remote zone, 4000 MMK, 3 days"
    ↓
AI generates: "The delivery fee to Taunggyi is 4,000 MMK with an estimated delivery time of 3 days."
```

## The Critical Rule

> **Never ask AI to do exact math or strict lookups. Give it the tools (functions) or the context (RAG) to do them deterministically.**

## Validation Strategy

| AI Output | Validation Method | Fallback |
|-----------|-------------------|----------|
| Invoice total | Recalculate with SQL function | Reject if mismatch > 0.01 |
| Tax amount | Query tax_rates table | Reject if rate doesn't match |
| Delivery estimate | Query townships + corridors | Flag for human review |
| Terminology | Query business_terms | Auto-correct if forbidden found |
| Compliance | Query border_stations + tax_rules | Always require human approval |

