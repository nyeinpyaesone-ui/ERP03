# 02 — What is an AI Role in a System

## Defining AI Roles

An AI Role is a **contract** that specifies:
- What the AI can do (skills)
- What the AI cannot do (boundaries)
- What inputs it expects (schemas)
- What outputs it produces (schemas)
- When it should act (triggers)
- When it should ask for help (escalation rules)

## Role Types in ERP SOLUTION

| Role Type | Responsibility | Example |
|-----------|---------------|---------|
| **Orchestrator** | Routes tasks, synthesizes results, manages workflow | Executive Orchestrator |
| **Specialist** | Deep expertise in one domain, handles specific tasks | Finance Officer, Logistics Coordinator |
| **Reviewer** | Checks outputs for compliance, accuracy, policy adherence | Compliance Guardian |
| **Executor** | Performs actions (sends emails, generates PDFs, updates DB) | Workflow Executor |
| **Observer** | Monitors systems, detects anomalies, alerts humans | Anomaly Hunter |

## Role Design Template

```yaml
role_name: Finance Officer
role_code: FIN_OFF
role_type: specialist
objective: Handle invoices, tax calculations, and financial reports with precision
skills:
  - INV_GEN: Generate invoices
  - TAX_CALC: Calculate taxes
  - RPT_GEN: Generate reports
input_schema:
  type: object
  properties:
    request_type: enum [invoice, tax, report]
    context: object
output_schema:
  type: object
  properties:
    result: object
    confidence: number
    requires_approval: boolean
confidence_threshold: 0.90
escalation_rules:
  - if: confidence < 0.90
    then: route_to_human
  - if: amount > 1000000
    then: require_approval
memory:
  type: semantic
  ttl_days: 30
```

## Role Separation of Concerns

- **No role should do everything** — Specialists handle depth, orchestrators handle breadth
- **Reviewers must be independent** — A specialist cannot review its own work
- **Executors must be deterministic** — Actions that modify data should be rule-based, not AI-guessed
- **Observers must be passive** — They watch and alert, never act autonomously

## Anti-Patterns

- ❌ **God Agent** — One AI that handles everything (unmaintainable, untestable)
- ❌ **No Boundaries** — AI decides what it can do (unpredictable, unsafe)
- ❌ **Silent Failure** — AI produces wrong output with no detection mechanism
- ❌ **No Escalation** — AI never asks for human help when uncertain

