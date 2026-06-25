# 03 — Understanding Workflow vs Automation

## Workflow

A **workflow** is a sequence of steps that may involve humans, AI, and systems. It is:
- **Directed** — Steps follow a defined path (sequential, parallel, conditional)
- **Stateful** — Each step has a status (pending, in-progress, completed, failed)
- **Observable** — Progress can be tracked and audited
- **Interruptible** — Humans can pause, modify, or cancel at any point

## Automation

**Automation** is the subset of a workflow where steps execute without human intervention. It is:
- **Deterministic** — Same input always produces same output
- **Rule-based** — Conditions are explicit, not interpreted
- **Fast** — No human latency
- **Limited scope** — Only handles pre-defined scenarios

## The Spectrum

```
Manual → Assisted → Semi-Automated → Fully Automated → Autonomous
  |         |            |                |               |
Human   Human+AI     Human approves    AI executes    AI decides
 does    suggests     AI proposals      low-risk       everything
all
```

## Where ERP SOLUTION Sits

| Feature | Level | Human Role |
|---------|-------|------------|
| Invoice creation | Assisted | Human reviews AI draft |
| Tax calculation | Semi-Automated | Human verifies totals |
| Delivery estimation | Fully Automated | Human only if exception |
| Anomaly detection | Assisted | Human investigates alerts |
| Compliance check | Semi-Automated | Human approves violations |
| Report generation | Fully Automated | Human reads output |

## Designing the Handoff

1. **Define the trigger** — What event starts the workflow?
2. **Define the path** — What are the steps and decision points?
3. **Define the automation boundary** — Which steps can run without humans?
4. **Define the approval gates** — Where must humans intervene?
5. **Define the exception handling** — What happens when automation fails?
6. **Define the audit points** — What gets logged at each step?

## Example: Invoice Workflow

```
[Trigger] Customer order confirmed
    ↓
[AI] Finance Officer drafts invoice (skill: INV_GEN)
    ↓
[Gate] Confidence > 0.90 AND amount < 1,000,000 MMK?
    ├─ Yes → [Auto] Save invoice, send to customer
    └─ No  → [Human] Review and approve in dashboard
    ↓
[Audit] Log all actions with hash chain
    ↓
[Observer] Anomaly Hunter checks for unusual patterns
```

