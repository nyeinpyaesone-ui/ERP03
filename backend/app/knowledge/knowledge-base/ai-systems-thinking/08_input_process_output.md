# 08 — Input → Process → Output Concept Model

## The Universal Pattern

Every AI system, no matter how complex, can be reduced to:

```
INPUT → PROCESS → OUTPUT
```

But the sophistication comes from what happens **between** and **around** these three nodes.

## Input Layer

| Component | Purpose | Example |
|-----------|---------|---------|
| **Ingestion** | Receive raw data | API endpoint, file upload, webhook |
| **Validation** | Check format and constraints | JSON Schema validation, type checking |
| **Sanitization** | Remove dangerous content | SQL injection prevention, XSS filtering |
| **Enrichment** | Add context from other sources | Lookup customer history, add tax rates |
| **Structuring** | Convert to processable format | PDF → text, voice → transcript |

## Process Layer

| Component | Purpose | Example |
|-----------|---------|---------|
| **Routing** | Decide which agent/skill handles it | Keyword matching, intent classification |
| **Context Loading** | Retrieve relevant knowledge | Query vector DB, fetch user preferences |
| **Reasoning** | Apply logic (rules + AI) | Calculate tax, generate text, classify risk |
| **Tool Use** | Call external systems | Query DB, send email, generate PDF |
| **Validation** | Check output quality | Schema validation, confidence scoring |

## Output Layer

| Component | Purpose | Example |
|-----------|---------|---------|
| **Formatting** | Structure for consumer | JSON for API, HTML for email, PDF for download |
| **Approval Gate** | Human check if needed | Dashboard queue, notification, Slack message |
| **Action** | Commit to system | Save to DB, send to customer, trigger webhook |
| **Feedback** | Tell user what happened | Success message, error details, progress update |
| **Audit** | Immutable record | Log entry with hash chain |

## The Feedback Loop

```
        ┌─────────────────────────────────────┐
        │                                     │
        ▼                                     │
┌──────────────┐    ┌──────────┐    ┌─────────┐│
│    Input     │───→│ Process  │───→│ Output  ││
└──────────────┘    └──────────┘    └─────────┘│
        │                    │                    │
        │                    ▼                    │
        │            ┌──────────┐               │
        └───────────→│  Audit   │───────────────┘
                     │   Log    │
                     └──────────┘
```

The audit log feeds back into the system for:
- **Learning** — What did the AI get wrong? How often?
- **Calibration** — Adjust confidence thresholds based on real performance
- **Compliance** — Prove what happened for regulators
- **Debugging** — Trace exactly why a decision was made

## Example: Complete Pipeline

```
[Input] User: "Create invoice for Acme Corp, 10 units of ERP Pro"
    ↓
[Validation] Check: contact exists, product exists, quantity > 0
    ↓
[Enrichment] Add: Acme Corp details, product price ($299), tax rate (5% CT)
    ↓
[Routing] Match to Finance Officer (triggers: "invoice", "create")
    ↓
[Context] Load: Acme Corp history, previous invoices, credit status
    ↓
[Reasoning] Calculate: 10 × $299 = $2,990 + 5% CT = $3,139.50
    ↓
[Validation] Confidence: 0.97 (high, rules-based calculation)
    ↓
[Gate] Amount < $1M AND confidence > 0.90 → Auto-execute
    ↓
[Action] Save invoice INV-2024-157 to DB, mark as "draft"
    ↓
[Output] Return: {invoice_id: "INV-2024-157", total: 3139.50, status: "draft"}
    ↓
[Audit] Log: actor=AI(FIN_OFF), action=CREATE, table=invoices, old=null, new={...}
    ↓
[Feedback] Notify: User sees success toast, invoice appears in dashboard
```

