# 06 — Simulation vs Real Execution

## What is Simulation?

**Simulation** is running an AI workflow in a **safe, non-destructive environment** where:
- No production data is modified
- No real emails are sent
- No actual payments are processed
- Outputs are logged for review, not committed

## Why Simulate?

1. **Testing** — Validate new skills before deployment
2. **Training** — Teach AI agents without risk
3. **Debugging** — Trace exactly what the AI did and why
4. **Confidence Calibration** — Measure accuracy against known outcomes
5. **Human Review** — Let humans approve AI behavior patterns before automation

## Simulation Modes in ERP SOLUTION

| Mode | Data | Actions | Output |
|------|------|---------|--------|
| **Dry Run** | Read-only from production | None | Report of what WOULD happen |
| **Sandbox** | Synthetic/test data | Simulated (no real side effects) | Full output for validation |
| **Shadow** | Production data | Parallel to real system, results compared | Accuracy metrics |
| **Canary** | Small % of production | Real but monitored | Gradual rollout validation |

## Simulation Checklist

Before enabling real execution for any AI skill:

- [ ] Skill tested in Sandbox with 100+ test cases
- [ ] Accuracy > threshold (e.g., 95% for tax calc, 90% for invoice gen)
- [ ] Edge cases documented and handled
- [ ] Failure modes tested (bad input, missing data, timeout)
- [ ] Human review process defined for exceptions
- [ ] Rollback plan documented
- [ ] Audit trail verified in simulation
- [ ] Performance acceptable (latency < 2s for sync, < 30s for async)

## Example: Invoice Skill Simulation

```python
# Simulation mode
result = ai_skill.run(
    skill="INV_GEN",
    input={"contact_id": "123", "items": [...]},
    mode="sandbox"  # ← No real invoice created
)

# Review output
print(result.draft_invoice)      # See what AI generated
print(result.confidence)         # 0.94 — above threshold
print(result.warnings)           # ["Tax rate may have changed recently"]
print(result.would_execute)      # True — if not in sandbox

# After validation, switch to real
result = ai_skill.run(
    skill="INV_GEN",
    input={"contact_id": "123", "items": [...]},
    mode="production"  # ← Real invoice created
)
```

## The Golden Rule

> **Never let an untested AI skill touch production data.** Simulation is not optional — it is the quality gate.

