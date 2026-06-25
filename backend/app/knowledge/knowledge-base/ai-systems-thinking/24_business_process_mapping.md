# 24 — Introduction to Business Process Mapping (Generic)

## What is Business Process Mapping?

Business Process Mapping is the visual representation of how work flows through an organization. In ERP SOLUTION, it shows:
- **Who** does what (human, AI agent, system)
- **What** happens at each step (actions, decisions, checks)
- **When** things happen (triggers, sequences, dependencies)
- **Where** data comes from and goes (systems, databases, APIs)
- **Why** decisions are made (rules, policies, goals)

## Standard Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| **Oval** | Start/End | "Receive Order" / "Order Complete" |
| **Rectangle** | Process/Action | "Calculate Tax" / "Generate Invoice" |
| **Diamond** | Decision | "Amount > 1M?" / "Stock Available?" |
| **Parallelogram** | Input/Output | "Get Customer Data" / "Send Email" |
| **Cylinder** | Database | "Query Invoices" / "Save to DB" |
| **Cloud** | AI/External | "AI Draft Email" / "Call Stripe API" |

## Example: Order-to-Invoice Process

```
[Start: Customer Order Received]
    ↓
[Process: Validate Order Data]
    ↓
[Decision: Valid?]
    ├─ No → [Process: Return Error] → [End]
    └─ Yes → [Process: Load Customer Data]
        ↓
    [Process: Check Stock]
        ↓
    [Decision: In Stock?]
        ├─ No → [Process: Backorder] → [End]
        └─ Yes → [Process: Calculate Total + Tax]
            ↓
        [AI: Finance Officer Drafts Invoice]
            ↓
        [Decision: Confidence > 0.90?]
            ├─ No → [Process: Human Review Queue]
            └─ Yes → [Process: Auto-Create Invoice]
                ↓
            [Process: Save to DB + Audit Log]
                ↓
            [Process: Send to Customer]
                ↓
            [End: Invoice Sent]
```

## Process Mapping Steps

### 1. Identify the Trigger
What event starts this process?
- Customer submits order
- Timer fires (daily report)
- Webhook received (payment confirmed)
- User clicks button (generate report)

### 2. List the Actors
Who is involved?
- Customer (external)
- Sales Rep (human)
- Finance Officer (AI)
- Compliance Guardian (AI)
- Database (system)
- Email Service (external API)

### 3. Map the Flow
What happens in sequence?
- Number each step
- Show decision points
- Show parallel paths
- Show loops (retries, approvals)

### 4. Define Data Flows
What data moves where?
- Input data sources
- Transformed data
- Output destinations
- Side effects

### 5. Identify Controls
What checks and balances exist?
- Validation rules
- Approval gates
- Audit points
- Error handling

## Process Metrics

Once mapped, measure:
- **Cycle time** — Total time from start to end
- **Touch time** — Time actually spent working (not waiting)
- **Wait time** — Time spent waiting (approvals, queues)
- **Error rate** — How often process fails
- **Cost** — Human hours + AI tokens + system resources
- **Throughput** — How many orders per hour

## ERP SOLUTION Process Library

Common processes to map:
1. **Lead-to-Customer** (marketing → sales → onboarding)
2. **Order-to-Cash** (order → invoice → payment → receipt)
3. **Procure-to-Pay** (request → PO → receive → invoice → pay)
4. **Hire-to-Retire** (recruit → onboard → manage → offboard)
5. **Issue-to-Resolution** (ticket → triage → resolve → close)

## Tools for Mapping

| Tool | Best For | Integration |
|------|----------|-------------|
| **Mermaid** | Docs, README | Markdown |
| **Lucidchart** | Visual design | Export to PNG/PDF |
| **Draw.io** | Free, collaborative | Export to SVG |
| **BPMN 2.0** | Enterprise standard | XML interchange |
| **Temporal UI** | Running workflows | Real-time status |

## Why Map Processes?

1. **Clarity** — Everyone sees how work flows
2. **Optimization** — Spot bottlenecks, redundancies, gaps
3. **Automation** — Identify which steps AI can handle
4. **Compliance** — Prove processes follow regulations
5. **Training** — New employees learn from the map
6. **Debugging** — When things break, know exactly where

