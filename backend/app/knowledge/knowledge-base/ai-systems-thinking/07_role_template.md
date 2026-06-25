# 07 — Building Your First AI Role Template

## The Template Structure

Every AI role in the system must be defined by a template that answers:

1. **Who am I?** — Role identity and personality
2. **What can I do?** — Skills and capabilities
3. **What do I need?** — Input requirements
4. **What do I produce?** — Output format
5. **When do I act?** — Triggers and routing
6. **When do I stop?** — Boundaries and escalation

## Template Format (YAML)

```yaml
role_template:
  metadata:
    name: "Finance Officer"
    code: "FIN_OFF"
    version: "1.0"
    author: "system"
    created_at: "2026-06-15"

  identity:
    role_type: "specialist"  # orchestrator | specialist | reviewer | executor | observer
    description: "Handles invoices, tax calculations, and financial reports"
    personality: "Precise, cautious, detail-oriented. Always verifies numbers."
    language: "en"

  capabilities:
    skills:
      - code: "INV_GEN"
        name: "Invoice Generation"
        confidence_threshold: 0.90
      - code: "TAX_CALC"
        name: "Tax Calculation"
        confidence_threshold: 0.95
      - code: "RPT_GEN"
        name: "Report Generation"
        confidence_threshold: 0.90

    forbidden_actions:
      - "Delete production records"
      - "Modify tax rates"
      - "Access payroll data"
      - "Send emails without approval"

  inputs:
    schema:
      type: "object"
      required: ["request_type", "context"]
      properties:
        request_type:
          type: "string"
          enum: ["invoice", "tax", "report", "query"]
        context:
          type: "object"
          properties:
            user_id: "string"
            tenant_id: "string"
            session_id: "string"

    validation_rules:
      - "request_type must be in enum"
      - "context.user_id must be valid UUID"
      - "context.tenant_id must match authenticated tenant"

  outputs:
    schema:
      type: "object"
      required: ["result", "confidence", "audit_log"]
      properties:
        result:
          type: "object"
        confidence:
          type: "number"
          minimum: 0
          maximum: 1
        requires_approval:
          type: "boolean"
        audit_log:
          type: "object"
          properties:
            action: "string"
            actor: "string"
            timestamp: "string"

  triggers:
    auto_execute:
      - condition: "confidence > 0.90 AND amount < 1000000"
        action: "execute"

    human_approval:
      - condition: "confidence < 0.90"
        action: "queue_for_review"
      - condition: "amount >= 1000000"
        action: "require_approval"
      - condition: "tax_type == 'CIT'"
        action: "require_approval"

  escalation:
    rules:
      - if: "confidence < 0.70"
        then: "route_to_senior_human"
      - if: "execution_time > 30000ms"
        then: "timeout_and_alert"
      - if: "error_count > 3"
        then: "disable_skill_and_alert"

  memory:
    type: "semantic"
    scope: "session"  # session | user | tenant | global
    ttl_days: 30
    max_entries: 1000

  testing:
    test_cases:
      - id: "TC001"
        input: {"request_type": "invoice", "context": {...}}
        expected_output: {"result": {...}, "confidence": 0.95}
        mode: "sandbox"
```

## Validation Checklist

Before deploying a role template:
- [ ] All skills exist in the skill registry
- [ ] Input schema is valid JSON Schema
- [ ] Output schema is valid JSON Schema
- [ ] Triggers are unambiguous (no overlapping conditions)
- [ ] Escalation paths lead to valid humans or systems
- [ ] Test cases cover happy path + edge cases + failure modes
- [ ] Memory scope is appropriate (don't store PII in global memory)

