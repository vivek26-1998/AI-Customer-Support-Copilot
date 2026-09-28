# Project Instructions

## Objective

Build a resume-quality agentic B2B customer-support system demonstrating AI
engineering, meaningful tool calling, structured outputs, PostgreSQL,
deterministic validation and policy enforcement, grounded generation,
evaluation, testing, and observability.

## Intended Architecture

1. An extraction agent understands and structures the customer email.
2. A validation service verifies customer, order, and other business facts.
3. A decision agent selects relevant tools and proposes an action.
4. Deterministic policy code approves, modifies, or rejects that proposal.
5. A drafting agent generates a reply using only approved, verified facts.
6. Unsafe, uncertain, or unauthorized cases go to human review.

## Architectural Rules

- Keep tool calling as a meaningful project feature.
- Use agents for language understanding, tool selection, and drafting.
- Use deterministic Python for validation, authorization, and business policy.
- Never treat email claims or model output as verified business facts.
- Never expose order details until customer ownership is verified.
- Agent proposals must pass policy checks before action tools execute.
- Drafting must use only verified facts and approved actions.
- Use Pydantic models at component boundaries.
- Keep SQLAlchemy models separate from Pydantic schemas.
- Access PostgreSQL through repositories, not directly from agents or prompts.
- Add tests for deterministic behavior before expanding a feature.
- Prefer incremental changes that keep the application working.

## Implementation Strategy

Prioritize working implementation before cleanup, presentation, deployment, or
a large repository restructure. For each stage, explain its purpose, implement
the smallest complete change, test it, and review it before moving forward.

## Current Development Order

1. Add `ValidationResult` to the Pydantic schemas.
2. Implement `validation.py` using the existing mock data.
3. Add validation tests.
4. Integrate validation into the current workflow without prematurely removing
   existing tools.
5. Add PostgreSQL, SQLAlchemy, Alembic, and repositories.
6. Replace mock lookups with database-backed repositories.
7. Move agent-callable tools into focused modules with typed results.
8. Refactor the decision agent to select tools and propose actions.
9. Add deterministic policy enforcement and tests.
10. Add a grounded drafting agent with a safe fallback.
11. Add workflow failure handling, tracing, and safe action tools.
12. Build evaluations, expand domains, and add human review.
13. Complete security, cleanup, documentation, deployment, and presentation.

## Current Priority

Read `docs/ROADMAP.md` before changing code and identify the first unfinished
step. Do not begin a later phase unless the current phase is complete or the
user explicitly changes priority.

Phases 1-4 are complete. The immediate task is Phase 5: focused customer/order
tool modules with typed results and independent tests. See docs/ROADMAP.md.

## Testing and Safety

- Validation and policy tests must not require an LLM or API key.
- Test missing, invalid, conflicting, and unauthorized data.
- Test every agent-callable tool independently.
- Include cross-customer order access as a security test.
- Never commit `.env`, API keys, or secrets.
- Do not log secrets or unnecessary customer information.
- Read tools may be selected by an agent.
- Write tools require validation and deterministic policy approval.
- Destructive or externally visible actions require explicit authorization.
