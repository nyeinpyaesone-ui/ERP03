# 21 — Common Mistakes in AI System Design

## The Top 10 Mistakes

### 1. The God Agent
**Mistake**: One AI that handles everything.
**Why it fails**: Untestable, unmaintainable, unpredictable. One bug breaks everything.
**Fix**: Role-based specialists with orchestration.

### 2. No Input Validation
**Mistake**: Trusting user input or AI output without validation.
**Why it fails**: SQL injection, schema violations, hallucinated data.
**Fix**: JSON Schema validation on every input. Validate AI output before using.

### 3. Missing Audit Trail
**Mistake**: AI modifies data with no record of what happened.
**Why it fails**: Cannot debug, cannot comply, cannot trust.
**Fix**: Immutable append-only logs with hash chains.

### 4. No Confidence Thresholds
**Mistake**: AI executes everything it generates.
**Why it fails**: Low-confidence outputs cause real damage.
**Fix**: Configurable thresholds per skill. Low confidence → human review.

### 5. Hardcoded Configuration
**Mistake**: Behavior baked into code, not configurable.
**Why it fails**: Cannot adapt to different tenants, regulations, or models.
**Fix**: External configuration with validation and audit.

### 6. Ignoring Latency
**Mistake**: Synchronous AI calls in user-facing UI.
**Why it fails**: Users wait 30 seconds for a response.
**Fix**: Async processing, streaming, caching, pre-computation.

### 7. No Sandbox Testing
**Mistake**: Deploying AI skills without testing.
**Why it fails**: Production becomes the test environment.
**Fix**: Mandatory sandbox testing with 20+ test cases per skill.

### 8. Monolithic Memory
**Mistake**: One big memory pool for all agents.
**Why it fails**: Privacy leaks, context pollution, unbounded growth.
**Fix**: Hierarchical memory (session → user → tenant → global) with TTL.

### 9. No Human Escape Hatch
**Mistake**: No way for humans to override AI decisions.
**Why it fails**: AI makes irreversible mistakes with no recourse.
**Fix**: Approval queues, override buttons, rollback capability.

### 10. Prompt Engineering as Architecture
**Mistake**: Believing better prompts fix system design.
**Why it fails**: Prompts are fragile. System design is durable.
**Fix**: Invest in workflow engineering, validation, and orchestration.

## Warning Signs

Your AI system is in trouble if:
- You cannot explain why the AI made a specific decision
- You have no test cases for AI outputs
- You cannot rollback an AI action
- AI errors are discovered by users, not monitoring
- You spend more time tuning prompts than designing workflows
- Different users get wildly different results for the same input
- AI has access to production data without approval gates

## The Fix Checklist

- [ ] Every AI skill has input/output schemas
- [ ] Every AI action is logged with actor, old/new values, timestamp
- [ ] Every AI output is validated before use
- [ ] Every skill has confidence thresholds
- [ ] Every skill is tested in sandbox before deployment
- [ ] Every workflow has a human escalation path
- [ ] Every configuration is external, not hardcoded
- [ ] Every system has health monitoring and alerting
- [ ] Every deployment is canaried before full rollout
- [ ] Every error has a documented recovery procedure

