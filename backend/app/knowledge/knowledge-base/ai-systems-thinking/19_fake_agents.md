# 19 — Building Fake AI Agents for Learning

## Why Build Fake Agents?

Fake (simulated) AI agents help you:
- **Learn** the orchestration layer without LLM costs
- **Test** workflow logic without waiting for inference
- **Debug** routing and decision flows deterministically
- **Demo** the system without API keys or internet
- **Validate** that the system architecture works before adding real AI

## Fake Agent Implementation

```python
class FakeAgent:
    """A deterministic agent that simulates AI behavior for testing."""

    def __init__(self, role_config: dict):
        self.role = role_config["role_type"]
        self.skills = role_config["skills"]
        self.behavior = role_config.get("behavior", "cooperative")

    def execute(self, request: dict) -> dict:
        # Deterministic response based on input patterns
        if request["type"] == "invoice":
            return {
                "result": {
                    "invoice_id": f"INV-FAKE-{random_id()}",
                    "total": request["amount"] * 1.05,
                    "status": "draft"
                },
                "confidence": 0.95,
                "requires_approval": request["amount"] > 1000000,
                "execution_time_ms": 150
            }
        elif request["type"] == "tax_calc":
            return {
                "result": {
                    "breakdown": [{"type": "CT", "rate": 0.05, "amount": request["amount"] * 0.05}],
                    "total_tax": request["amount"] * 0.05,
                    "total_with_tax": request["amount"] * 1.05
                },
                "confidence": 0.99,
                "requires_approval": False,
                "execution_time_ms": 50
            }
        elif request["type"] == "delivery":
            return {
                "result": {"estimated_days": 3, "cost_mmk": 4000, "route": "Standard"},
                "confidence": 0.88,
                "requires_approval": False,
                "execution_time_ms": 200
            }

    def simulate_error(self, error_type: str):
        if error_type == "timeout":
            raise TimeoutError("Fake timeout after 30s")
        elif error_type == "validation":
            raise ValueError("Fake validation error")
        elif error_type == "low_confidence":
            return {"result": None, "confidence": 0.45, "requires_approval": True}
```

## Fake Agent Behaviors

| Behavior | Use Case |
|----------|----------|
| **Cooperative** | Happy path testing |
| **Pessimistic** | Error handling testing |
| **Slow** | Performance testing |
| **Random** | Stress testing |
| **Adversarial** | Security testing |

## Key Insight

> Fake agents are not "cheating." They are **scaffolding** that lets you build and test the system architecture before adding the expensive, unpredictable LLM layer.

---

