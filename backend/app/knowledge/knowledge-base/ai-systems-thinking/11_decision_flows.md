# 11 — Designing Simple Decision Flows

## Decision Flow Principles

1. **Binary where possible** — Yes/No gates are easier to test and audit
2. **Explicit conditions** — Every branch must have a clear, testable rule
3. **Default paths** — Always define what happens when no condition matches
4. **Confidence-based** — Let AI uncertainty drive routing, not just rules
5. **Human escape hatch** — Every flow must have a path to human intervention

## Basic Decision Patterns

### Pattern 1: Confidence Gate
```
AI generates output
    ↓
Confidence >= threshold?
    ├─ Yes → Auto-execute
    └─ No  → Human review queue
```

### Pattern 2: Risk-Based Routing
```
Input received
    ↓
Risk level?
    ├─ Low (routine, small amount) → Auto-process
    ├─ Medium (unusual, medium amount) → AI review + human notification
    └─ High (compliance, large amount) → Human approval required
```

### Pattern 3: Multi-Agent Consensus
```
Task received
    ↓
Route to 3 specialist agents
    ↓
Collect outputs
    ↓
Do they agree?
    ├─ Yes (all confidence > 0.90) → Execute
    ├─ Partial (2 agree, 1 dissent) → Execute with warning
    └─ No (disagreement) → Human arbitration
```

### Pattern 4: Escalation Chain
```
AI attempts task
    ↓
Success?
    ├─ Yes → Done
    └─ No  → Retry with different approach
        ↓
        Success?
        ├─ Yes → Done
        └─ No  → Escalate to senior agent
            ↓
            Success?
            ├─ Yes → Done
            └─ No  → Human intervention
```

## Decision Flow Language

Use a simple, declarative format:

```yaml
decision_flow:
  name: "Invoice Approval"

  steps:
    - id: "check_amount"
      condition: "invoice.total < 1000000"
      true_next: "check_confidence"
      false_next: "require_approval"

    - id: "check_confidence"
      condition: "ai.confidence > 0.90"
      true_next: "check_customer"
      false_next: "ai_review"

    - id: "check_customer"
      condition: "customer.risk_score == 'low'"
      true_next: "auto_approve"
      false_next: "require_approval"

    - id: "auto_approve"
      action: "execute_invoice"
      next: "done"

    - id: "ai_review"
      action: "ai_second_opinion"
      next: "check_confidence"  # Loop back with new confidence
      max_loops: 2

    - id: "require_approval"
      action: "queue_for_human"
      next: "done"

    - id: "done"
      action: "log_and_notify"
```

## Testing Decision Flows

Every decision flow must have test cases for:
- **Happy path** — All conditions true, auto-execution
- **Boundary** — Exactly at threshold (amount = 1,000,000)
- **False path** — Each condition false, verify routing
- **Loop** — Retry logic doesn't infinite loop
- **Timeout** — What if AI doesn't respond?
- **Error** — What if DB is down during check?

## Anti-Patterns

- ❌ **Nested IFs** — More than 3 levels deep becomes untestable
- ❌ **Implicit defaults** — "Otherwise do X" without explicit rule
- ❌ **No confidence** — Routing purely on rules, ignoring AI uncertainty
- ❌ **No escape** — No way for human to override or intervene
- ❌ **Hidden state** — Decision depends on data not in the input

