# 10 — Breaking Down Real-World Tasks into AI Steps

## The Task Decomposition Method

Any real-world business task can be decomposed into:
1. **Trigger** — What starts the task?
2. **Information Gathering** — What data is needed?
3. **Analysis** — What reasoning is applied?
4. **Decision** — What choice is made?
5. **Action** — What is executed?
6. **Verification** — How do we know it worked?
7. **Communication** — Who is informed?

## Example: "Process a New Customer Order"

### Step 1: Trigger
- Event: Webhook from e-commerce platform
- Data: {customer_id, items, shipping_address, payment_method}

### Step 2: Information Gathering
- Query DB: Is customer known? (contacts table)
- Query DB: Are items in stock? (products table)
- Query API: Is payment valid? (Stripe)
- Query DB: What is shipping address township? (townships table)

### Step 3: Analysis (AI + Rules)
- **Rule**: If stock < quantity → reject
- **Rule**: If payment fails → reject
- **AI**: Classify customer (new vs returning, enterprise vs SME)
- **AI**: Estimate delivery date based on township zone
- **AI**: Calculate total with tax (function call)

### Step 4: Decision
- **Rule**: If total > 1,000,000 MMK → flag for review
- **AI**: Confidence in delivery estimate > 0.85?
- **System**: Create invoice or queue for approval

### Step 5: Action
- **System**: Create invoice record
- **System**: Reserve inventory
- **System**: Charge payment
- **AI**: Generate confirmation email draft
- **System**: Send email (if approved)

### Step 6: Verification
- **System**: Check invoice saved correctly
- **System**: Check payment succeeded
- **System**: Check inventory reserved
- **AI**: Verify email content (terminology check)

### Step 7: Communication
- **System**: Notify customer (email/SMS)
- **System**: Notify sales team (Slack)
- **System**: Update dashboard (real-time)
- **Audit**: Log all actions

## Decomposition Template

```yaml
task: "Process New Customer Order"
trigger:
  type: webhook
  source: e-commerce
  event: order.placed

data_requirements:
  - source: contacts
    query: "SELECT * FROM contacts WHERE id = {customer_id}"
    required: true
  - source: products
    query: "SELECT stock FROM products WHERE id IN {item_ids}"
    required: true
  - source: townships
    query: "SELECT * FROM townships WHERE name_en ILIKE {shipping_city}"
    required: true
  - source: tax_rates
    query: "SELECT * FROM tax_rates WHERE is_active = true"
    required: true

analysis_steps:
  - name: validate_stock
    type: rule
    logic: "ALL(items.stock >= items.quantity)"
  - name: classify_customer
    type: ai
    agent: FIN_OFF
    input: customer_history
  - name: estimate_delivery
    type: ai
    agent: LOG_COO
    input: {township, weight}
  - name: calculate_total
    type: function
    name: calculate_tax
    input: {amount, tax_types}

decision_rules:
  - condition: "total > 1000000"
    action: require_approval
  - condition: "stock_insufficient"
    action: reject_with_reason
  - condition: "payment_failed"
    action: reject_and_notify

actions:
  - type: system
    name: create_invoice
  - type: system
    name: reserve_inventory
  - type: system
    name: charge_payment
  - type: ai
    name: draft_email
    agent: FIN_OFF
  - type: system
    name: send_email
    requires_approval: false

verification:
  - check: "invoice exists in DB"
  - check: "payment status = succeeded"
  - check: "inventory reserved"
  - ai_check: "terminology_validation"

communication:
  - recipient: customer
    channel: email
    template: order_confirmation
  - recipient: sales_team
    channel: slack
    message: "New order: {order_id}"
  - recipient: audit_log
    channel: database
    data: full_action_chain
```

## Key Insight

> The art of AI system design is not making the AI smarter. It is **making the system around the AI so structured that the AI only needs to handle the parts where human judgment genuinely adds value**.

