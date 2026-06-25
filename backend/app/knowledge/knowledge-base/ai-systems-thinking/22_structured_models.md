# 22 — Turning Real Tasks into Structured Models

## The Modeling Process

Every real-world task can be modeled as:

```
ENTITY + ACTION + CONSTRAINTS + OUTPUT
```

### Step 1: Identify the Entity
What object is being acted upon?
- Invoice, Contact, Shipment, Report, Payment

### Step 2: Define the Action
What is being done to the entity?
- Create, Update, Delete, Calculate, Generate, Validate, Send

### Step 3: List Constraints
What rules must be satisfied?
- Schema, business rules, compliance, authorization

### Step 4: Specify Output
What is produced?
- Structured data, document, notification, action trigger

## Example: "Send Invoice to Customer"

### Entity: Invoice
```yaml
entity:
  name: "Invoice"
  table: "invoices"
  schema:
    id: UUID
    contact_id: UUID → contacts.id
    items: ARRAY[InvoiceItem]
    total: NUMERIC(12,2)
    tax_amount: NUMERIC(12,2)
    status: ENUM[draft, sent, paid, overdue, cancelled]
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
```

### Action: Send
```yaml
action:
  name: "Send Invoice"
  verb: "SEND"
  actor: "Finance Officer (AI)"

  preconditions:
    - "invoice.status == 'draft'"
    - "invoice.total > 0"
    - "contact.email IS NOT NULL"
    - "invoice.created_at < NOW() - INTERVAL '1 minute'"

  steps:
    - "Generate PDF from invoice data"
    - "Validate PDF structure"
    - "Send email to contact.email with PDF attachment"
    - "Update invoice.status to 'sent'"
    - "Log action to audit trail"
    - "Notify user of success"

  postconditions:
    - "invoice.status == 'sent'"
    - "email_log entry exists"
    - "audit_log entry exists"
```

### Constraints
```yaml
constraints:
  authorization:
    - "user.has_permission('invoice.send')"

  business_rules:
    - "invoice.total >= 0"
    - "invoice.tax_amount == calculate_tax(invoice.total)"
    - "invoice.items.length > 0"

  compliance:
    - "invoice.includes_tax_breakdown"
    - "invoice.includes_payment_terms"

  rate_limits:
    - "max 100 emails per hour per tenant"
```

### Output
```yaml
output:
  success:
    - "email_id: UUID"
    - "invoice.status: 'sent'"
    - "timestamp: TIMESTAMP"

  failure:
    - "error_code: ENUM"
    - "error_message: STRING"
    - "retryable: BOOLEAN"

  side_effects:
    - "email_sent: BOOLEAN"
    - "pdf_generated: BOOLEAN"
    - "audit_log_created: BOOLEAN"
```

## Model Templates

### Template: Create Entity
```yaml
task_model:
  type: "CREATE"
  entity: {name}

  input:
    required_fields: [...]
    optional_fields: [...]
    validation_rules: [...]

  processing:
    enrichment: [...]
    calculations: [...]
    defaults: [...]

  output:
    entity_id: UUID
    created_entity: {schema}

  side_effects:
    notifications: [...]
    audit: true
```

### Template: Calculate Value
```yaml
task_model:
  type: "CALCULATE"
  entity: {name}

  input:
    parameters: [...]
    formulas: [...]

  processing:
    deterministic: true
    ai_assisted: false

  output:
    result: {type}
    breakdown: [...]
    confidence: 1.0

  side_effects:
    audit: true
```

### Template: Generate Document
```yaml
task_model:
  type: "GENERATE"
  entity: "Document"

  input:
    template_id: UUID
    data_source: {entity}

  processing:
    template_engine: "Jinja2"
    ai_enhancement: "optional"

  output:
    document_url: STRING
    format: ENUM[pdf, docx, html]

  side_effects:
    storage: true
    audit: true
```

## Why Model?

1. **Clarity** — Everyone understands exactly what the task does
2. **Testability** — Each part can be tested independently
3. **Documentation** — The model IS the documentation
4. **Code generation** — Models can generate API specs, tests, UI forms
5. **Audit** — Regulators can read the model, not the code

