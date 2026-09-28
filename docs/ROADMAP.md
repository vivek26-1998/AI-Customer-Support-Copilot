# AI Customer Support Copilot Roadmap

## Current Status (2026-09-28)

- Phases 1 and 2: implemented; deterministic validation tests pass.
- Phase 3: completed with fail-closed validation routing, request-scoped read
  tools, and workflow/API security regression tests.
- Phase 4: complete. Existing Alembic migration verified; typed repositories,
  insert-only demo seeding, database-backed lookups, and SQLite/PostgreSQL tests
  preserve validation behavior. No runtime mock-data fallback remains.
- Phases 5-13: pending; the combined decision/drafting agent remains the MVP.

## Goal

Build a production-style agentic B2B customer-support system that understands
emails, chooses business tools, verifies retrieved facts, enforces deterministic
policies, produces grounded draft replies, and escalates unsafe cases for human
review.

## Target Pipeline

```text
Customer email
  -> Extraction agent
  -> Validation service
  -> Decision and tool-calling agent
  -> Deterministic policy engine
  -> Grounded drafting agent
  -> Human review or approved response
  -> Audit and evaluation
```

## Responsibility Boundaries

| Component | Responsibility |
| --- | --- |
| Extraction agent | Understand and structure the email |
| Validation service | Verify business facts and ownership |
| Decision agent | Select tools and propose an action |
| Policy engine | Approve, change, or reject the proposed action |
| Drafting agent | Write from approved, verified facts |
| Workflow | Coordinate stages and handle failures |
| Database | Store business records and audit history |

## Phase 1: Validation Contract

Add `ValidationResult` to the Pydantic schemas. It must represent customer and
order existence, ownership, verified facts, and validation errors.

Why: it creates a typed boundary between email claims and verified facts.

Done when: valid, missing, unknown, conflicting, and unauthorized states can be
represented.

## Phase 2: Mock-Data Validation

Create `app/services/validation.py` and `tests/test_validation.py`. Cover valid
ownership, unknown customers, missing order IDs, unknown orders, cross-customer
orders, and inconsistent records.

Why: prove deterministic behavior before adding database complexity.

Done when: tests pass without an LLM call or API key.

## Phase 3: Workflow Integration

Insert validation between extraction and the current decision agent. Treat the
validation result as the source of truth and keep current tools until their
usefulness is evaluated in the working pipeline.

Why: add grounding incrementally without breaking the MVP.

Done when: the API handles validation failures without disclosing another
customer's order information.

## Phase 4: PostgreSQL Foundation

Add PostgreSQL, SQLAlchemy 2.x, Alembic, Customer and Order models, repository
abstractions, migrations, seed data, and database tests. Keep SQLAlchemy models
separate from Pydantic schemas.

Why: demonstrate relational modelling, constraints, migrations, sessions,
transactions, repositories, and testable persistence.

Done when: database-backed repositories replace mock lookups while preserving
validation behavior.

## Phase 5: Agent Tool Layer

Move tools out of `agent_service.py`. Begin with customer and order tools, then
add inventory, invoice, RMA eligibility, and knowledge-base tools as those use
cases are implemented. Use typed, minimal, safe tool results.

Why: category-specific capabilities create meaningful agent tool selection.

Done when: every tool has tests, error handling, and controlled output fields.

## Phase 6: Decision Agent

Refactor the decision agent to receive extraction and validation context,
select relevant tools, and produce a structured `AgentProposal`. It proposes
actions but does not authorize them or verify ownership.

Why: flexible reasoning belongs to the agent; final authority does not.

Done when: representative emails reliably produce appropriate tool selections
and structured proposals.

## Phase 7: Deterministic Policy Engine

Add `PolicyDecision`, `policy.py`, and tests for missing customers or orders,
ownership mismatches, missing IDs, delays, priority escalation, tool failures,
and unsupported actions.

Why: deterministic code must control security-sensitive business decisions.

Done when: every approved and rejected action has a unit test.

## Phase 8: Grounded Drafting Agent

Implement `drafting.py`. Give the agent only the original request, safe verified
facts, and an approved policy decision. It may not query data, apply policy,
override validation, or send email. Add a template fallback.

Why: demonstrate grounded generation and separation of responsibilities.

Done when: drafts contain no unsupported facts or promises.

## Phase 9: Workflow Orchestration

Make `workflow.py` coordinate every stage. Add request IDs, stage-level error
handling, timeouts, limited retries, and safe human-review fallbacks.

Why: a clear orchestrator makes the system understandable and debuggable.

Done when: agent, tool, or database failures produce controlled outcomes.

## Phase 10: Tracing and Safe Actions

Record sanitized tool calls, validation outcomes, proposals, policies, latency,
usage, cost, and status. Then add controlled write tools such as ticket creation
and draft saving behind validation and policy approval.

Why: traces support debugging, while approval gates make action tools safe.

Done when: requests are auditable and no write tool bypasses policy approval.

## Phase 11: Evaluation Framework

Create labelled standard, edge-case, and adversarial email datasets. Measure
classification, extraction, tool selection, validation, policy routing,
groundedness, leakage, escalation, latency, and cost.

Why: reproducible evaluation distinguishes engineering from a one-off demo.

Done when: a repeatable command produces a saved report with real measurements.

## Phase 12: Domain and Product Expansion

Add inventory, invoices, RMA, support history, agent runs, human reviews, and a
small review interface only as their corresponding features are implemented.

Why: feature-driven growth avoids premature complexity.

## Phase 13: Reliability, Cleanup, and Presentation

Add prompt-injection testing, authorization, PII-aware logging, idempotency,
CI, containers, documentation, architecture diagrams, evaluation results,
screenshots, and deployment after the core implementation is stable.

Why: presentation should document proven behavior rather than planned behavior.

## Working Method

For every phase: discuss the purpose, inspect affected code, implement the
smallest complete change, test it, review it, and then select the next step from
the working system.

## Immediate Next Step

Begin Phase 5: move the existing request-scoped customer and order tools out of
`agent_service.py` into focused modules with typed results and independent tests.
Preserve the validation context and ownership restrictions. Add further domain
tools only when their corresponding use cases are implemented.
