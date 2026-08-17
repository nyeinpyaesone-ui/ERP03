# AI Backend

AI / agent system boundary for ERP03.

## Rules

- No direct access to ERP SQLAlchemy models or the ERP database.
- No ERP transaction ownership.
- Consume ERP data and commands through `INTEGRATION/` contracts and the ERP API boundary.
- LLM providers, orchestration, agents, memory, policies, tools, and AI events belong here.

## Migration state

The former in-process AI/LLM implementation was removed from the ERP runtime in this architecture migration. Its Git history remains available through the pre-migration archive branch. The new AI runtime must be introduced behind the integration boundary before AI endpoints are re-enabled in production.
