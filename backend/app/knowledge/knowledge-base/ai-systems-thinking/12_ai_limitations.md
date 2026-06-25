# 12 — Understanding AI Limitations in Systems

## What AI Cannot Do Reliably

| Task | Why It Fails | System Solution |
|------|-------------|---------------|
| **Exact math** | LLMs hallucinate numbers | Use SQL functions, calculators |
| **Real-time data** | Training data has cutoff | Query live DB, use APIs |
| **Multi-step logic** | Loses track after 3-4 steps | Break into workflow steps |
| **Schema adherence** | Generates invalid JSON | Validate with JSON Schema |
| **Long context** | Forgets early information | Chunk, summarize, retrieve |
| **Deterministic rules** | Interprets ambiguously | Use rule engines, not LLMs |
| **Legal compliance** | Doesn't know jurisdiction | Query regulation DB, human review |
| **Real-world actions** | Has no physical presence | Trigger APIs, webhooks, executors |

## The Hallucination Problem

AI "hallucinates" when it:
- Makes up facts not in its training data
- Confuses similar concepts
- Generates plausible but wrong structured data
- Invents citations, references, or IDs

### Mitigation Strategies

1. **Grounding** — Always retrieve facts from DB before generating
2. **Validation** — Check AI output against known data
3. **Constrained generation** — Force AI to use provided context only
4. **Confidence scoring** — Train AI to say "I don't know"
5. **Human review** — High-stakes outputs always checked

## The Context Window Problem

LLMs have limited context (4K-128K tokens). In an ERP system:
- One customer record: ~500 tokens
- One invoice with 10 items: ~1,000 tokens
- Full customer history: 10,000+ tokens

### Solutions

1. **Chunking** — Break large documents into smaller pieces
2. **Summarization** — Compress history into key points
3. **Retrieval** — Only load relevant context on demand
4. **Hierarchical memory** — Session → User → Tenant → Global

## The Latency Problem

| Operation | Typical Latency | Acceptable? |
|-----------|----------------|-------------|
| DB query | 10-50ms | Yes |
| Cache read | 1-5ms | Yes |
| LLM inference (small) | 500ms-2s | Yes, for async |
| LLM inference (large) | 5-30s | No, for sync UI |
| Multi-agent chain | 10-60s | No, must be background |

### Strategies

1. **Async processing** — Queue long tasks, notify when done
2. **Streaming** — Show partial results as they arrive
3. **Caching** — Store frequent AI outputs
4. **Pre-computation** — Generate reports overnight
5. **Faster models** — Use GPT-3.5 for simple tasks, GPT-4 for complex

## The Cost Problem

| Model | Cost per 1K tokens | Monthly cost (heavy use) |
|-------|-------------------|-------------------------|
| GPT-3.5 | $0.002 | $500-2,000 |
| GPT-4 | $0.03-0.06 | $5,000-20,000 |
| Claude 3 | $0.03 | $5,000-15,000 |
| Local LLM | Hardware cost | $2,000-10,000 (one-time) |

### Strategies

1. **Token optimization** — Shorter prompts, compressed context
2. **Caching** — Don't re-process identical queries
3. **Model selection** — Cheaper model for simple tasks
4. **Batching** — Process multiple items in one prompt
5. **Hybrid** — Rules for deterministic, AI for interpretive

## The Safety Problem

AI can:
- Leak sensitive data in outputs
- Be tricked by prompt injection
- Generate harmful or biased content
- Make decisions that violate policy

### Safety Layers

1. **Input filtering** — Block dangerous prompts
2. **Output filtering** — Scan for PII, toxicity, policy violations
3. **Sandboxing** — AI cannot access production without approval
4. **Logging** — Every AI action is audited
5. **Kill switch** — Disable AI if anomaly detected

