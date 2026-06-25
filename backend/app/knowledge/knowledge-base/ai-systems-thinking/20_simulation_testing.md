# 20 — How to Test AI Behavior in Simulation Mode

## Testing Pyramid for AI Systems

```
         ┌─────────────┐
         │   E2E Tests │  (Full workflow, real data)
         │   (10%)     │
         ├─────────────┤
         │  Integration │  (Agent + Skills + Tools)
         │   Tests (20%)│
         ├─────────────┤
         │   Unit Tests │  (Individual skills, deterministic)
         │   (50%)      │
         ├─────────────┤
         │  Simulation  │  (Fake agents, workflow logic)
         │   Tests (20%)│
         └─────────────┘
```

## Simulation Test Types

### 1. Path Coverage Tests
Verify every branch in the decision flow:
- Happy path (all conditions true)
- Each false branch (each condition false individually)
- Boundary conditions (exactly at threshold)
- Loop conditions (retry logic, max iterations)

### 2. Confidence Calibration Tests
Verify that AI confidence matches actual accuracy:
- Run 100 test cases
- Group by confidence buckets (0.9-1.0, 0.8-0.9, etc.)
- Verify accuracy in each bucket matches confidence
- If not, recalibrate thresholds

### 3. Load Tests
Verify system behavior under stress:
- 10 concurrent requests
- 100 concurrent requests
- 1000 concurrent requests
- Measure latency, error rate, resource usage

### 4. Chaos Tests
Verify resilience:
- Kill DB connection mid-request
- Timeout LLM response
- Corrupt input data
- Remove required skill from registry

## Test Case Template

```yaml
test_case:
  id: "TC001"
  name: "Invoice generation with tax calculation"
  skill: "INV_GEN"
  mode: "sandbox"

  input:
    contact_id: "550e8400-e29b-41d4-a716-446655440000"
    items:
      - product_id: "ERP-PRO"
        quantity: 10
        unit_price: 299

  expected_output:
    schema_valid: true
    total: 3139.50  # 10 * 299 * 1.05
    tax_amount: 149.50
    status: "draft"
    confidence: ">= 0.90"
    requires_approval: false

  validation_rules:
    - "output.total == expected.total"
    - "output.confidence >= expected.confidence"
    - "output.schema_valid == true"

  side_effects:
    - "no_email_sent"
    - "invoice_saved_to_sandbox_db"
    - "audit_log_entry_created"
```

## Automated Test Runner

```python
class SimulationTestRunner:
    def __init__(self, environment="sandbox"):
        self.env = environment
        self.results = []

    def run_test(self, test_case: dict) -> dict:
        try:
            # Setup sandbox
            sandbox = SandboxEnvironment()

            # Execute skill
            start_time = time.time()
            result = sandbox.execute(
                skill=test_case["skill"],
                input=test_case["input"]
            )
            elapsed_ms = (time.time() - start_time) * 1000

            # Validate output
            validation = self.validate(result, test_case["expected_output"])

            # Check side effects
            side_effects = self.check_side_effects(sandbox, test_case["side_effects"])

            return {
                "test_id": test_case["id"],
                "passed": validation.passed and side_effects.passed,
                "output": result,
                "validation": validation,
                "side_effects": side_effects,
                "elapsed_ms": elapsed_ms
            }
        except Exception as e:
            return {
                "test_id": test_case["id"],
                "passed": False,
                "error": str(e),
                "stack_trace": traceback.format_exc()
            }

    def run_suite(self, test_cases: list) -> dict:
        results = [self.run_test(tc) for tc in test_cases]
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results),
            "results": results
        }
```

## Simulation Report

```
=============================================================
SIMULATION TEST REPORT
Environment: sandbox
Date: 2026-06-15 14:30:00
=============================================================

SUMMARY
  Total Tests:    50
  Passed:         48 (96%)
  Failed:         2 (4%)
  Avg Latency:    245ms

SKILL BREAKDOWN
  INV_GEN:        15/15 passed (100%)
  TAX_CALC:       12/12 passed (100%)
  DEL_EST:        10/10 passed (100%)
  COMP_CHK:        8/10 passed (80%)  ← 2 failures
  TERM_VAL:        3/3 passed (100%)

FAILURES
  TC041: COMP_CHK - Border station status mismatch
    Expected: "Active" for Muse
    Actual:   "Restricted" (data changed since test written)
    Action:   Update test data or flag data drift

  TC042: COMP_CHK - Tax rate outdated
    Expected: CT = 5%
    Actual:   CT = 5% (but new regulation says 3%)
    Action:   Update tax_rates table, add data freshness check

RECOMMENDATIONS
  1. Add data freshness validation to COMP_CHK skill
  2. Update test data to match current regulations
  3. Re-run after fixes before deployment
=============================================================
```

