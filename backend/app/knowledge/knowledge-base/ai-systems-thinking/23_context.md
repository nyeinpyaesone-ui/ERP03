# 23 — Understanding Context in AI Systems

## What is Context?

Context is **all the information an AI needs to make a good decision** that is not in the immediate prompt. It includes:
- **User context** — Who is asking, what do they know, what do they prefer?
- **Business context** — What company, what industry, what regulations apply?
- **Session context** — What was discussed earlier, what decisions were made?
- **System context** — What time is it, what features are enabled, what is the load?
- **World context** — What are current tax rates, exchange rates, border statuses?

## The Context Pyramid

```
                    ┌─────────────────┐
                    │   IMMEDIATE     │  ← The current prompt
                    │    PROMPT       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    SESSION      │  ← This conversation
                    │    MEMORY       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    USER         │  ← This user''s history
                    │    PROFILE      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    TENANT       │  ← This company''s data
                    │    CONTEXT      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    GLOBAL       │  ← System-wide knowledge
                    │    KNOWLEDGE    │
                    └─────────────────┘
```

## Context Loading Strategy

### 1. Retrieve Only What is Needed
Do not dump the entire database into the prompt. Instead:
- Vector search for semantic relevance
- Structured queries for exact data
- Summaries for long histories

### 2. Prioritize by Relevance
```python
def load_context(user_query, user_id, tenant_id):
    # 1. Immediate: The query itself
    context = {"query": user_query}

    # 2. Semantic: Relevant knowledge articles
    context["knowledge"] = vector_search(user_query, top_k=3)

    # 3. Structured: Exact data needed
    if "invoice" in user_query:
        context["recent_invoices"] = query_db(
            "SELECT * FROM invoices WHERE contact_id = %s ORDER BY created_at DESC LIMIT 5",
            user_id
        )

    # 4. User: Preferences and history
    context["user_prefs"] = get_user_preferences(user_id)

    # 5. Tenant: Business rules
    context["tenant_config"] = get_tenant_config(tenant_id)

    return context
```

### 3. Compress Long Context
- **Summarization**: Compress 10 pages of history into 3 bullet points
- **Extraction**: Pull only relevant fields from large records
- **Chunking**: Break long documents into retrievable pieces

### 4. Update Context in Real-Time
- **Event-driven**: When data changes, update context cache
- **Invalidation**: Clear cached context when underlying data changes
- **Streaming**: Push context updates to active sessions

## Context in ERP SOLUTION

| Context Type | Source | How Loaded | TTL |
|--------------|--------|------------|-----|
| **User profile** | `users` table | On login | Session |
| **Recent invoices** | `invoices` table | On demand | 5 min |
| **Tax rates** | `tax_rates` table | On startup | 1 hour |
| **Township data** | `townships` table | On demand | 1 hour |
| **Business terms** | `business_terms` table | On startup | 24 hours |
| **AI skills** | `ai_skills` table | On startup | Until updated |
| **Agent config** | `ai_agents` table | On startup | Until updated |
| **System config** | `system_configs` table | On startup | 5 min |

## The Context Window Problem

LLMs have limited context. In ERP SOLUTION:
- **GPT-4**: 8K-128K tokens
- **Claude 3**: 200K tokens
- **Local LLM**: 4K-8K tokens

One customer record with full history: ~2,000 tokens
One invoice with 10 items: ~1,500 tokens
One knowledge article: ~800 tokens

**Strategy**: Load only what is needed, compress what is loaded, retrieve what is referenced.

## Context-Aware Prompt Template

```
You are {agent.role} for {tenant.name}.

USER CONTEXT:
- Name: {user.name}
- Role: {user.role}
- Department: {user.department}

BUSINESS CONTEXT:
- Industry: {tenant.industry}
- Currency: {tenant.currency}
- Tax jurisdiction: {tenant.jurisdiction}

CURRENT TASK:
{user.query}

RELEVANT DATA:
{retrieved_context}

INSTRUCTIONS:
1. Use the provided data, do not make up facts
2. If data is insufficient, ask for clarification
3. Output must match the schema: {output_schema}
4. Confidence must be between 0 and 1
```

