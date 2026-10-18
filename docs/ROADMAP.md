# AI Customer Support Copilot Roadmap

## Current Status (2026-10-18)

- Phases 1 and 2: implemented; deterministic validation tests pass.
- Phase 3: completed with fail-closed validation routing, request-scoped read
  tools, and workflow/API security regression tests.
- Phase 4: complete. Existing Alembic migration verified; typed repositories,
  insert-only demo seeding, database-backed lookups, and SQLite/PostgreSQL tests
  preserve validation behavior. No runtime mock-data fallback remains.
- Phase 5: complete. Repository-backed tools enforce customer scope, return typed
  results and record per-run evidence. The workflow fails closed on missing
  evidence or failed tool calls. SQLite and PostgreSQL regression tests pass.
- Phases 6-13: pending; the combined decision/drafting agent remains the MVP.

## Goal

Build a production-style agentic B2B customer-support system that understands
emails, chooses business tools, verifies retrieved facts, enforces deterministic
policies, produces grounded draft replies, and escalates unsafe cases for human
review.

## Target Pipeline

```text
Customer email
  -> Extraction agent
  -> Application-controlled customer scope
  -> Decision agent selects read tools
  -> Tools query repositories and deterministically verify access and facts
  -> Deterministic policy engine
  -> Grounded drafting agent
  -> Human review or approved response
  -> Audit and evaluation
```

## Responsibility Boundaries

| Component | Responsibility |
| --- | --- |
| Extraction agent | Understand and structure the email |
| Request context | Carry application-controlled customer scope; never model-selected identity |
| Read tools and validation code | Retrieve through repositories and verify business facts and ownership |
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

## Phase 5: Repository-Backed Agent Tools

Build focused customer and order tools outside `agent_service.py` that retrieve
business facts through repositories instead of returning facts already supplied
in the agent prompt.

Responsibilities:
- Application code establishes the customer scope for the request and passes
  it through runtime context.
- The decision agent selects tools and supplies lookup arguments, such as
  an order ID.
- `get_customer` retrieves the current customer's profile using the customer
  identity from context.
- `get_order` retrieves an order through a customer-scoped repository query.
  The model cannot choose or override the customer identity.
- Deterministic Python enforces access before any business facts are returned.
- Tools return minimal, typed Pydantic results for successful lookups,
  unavailable records, invalid arguments, and operational failures.
- Unknown and unauthorized orders produce the same outward-facing result,
  avoiding disclosure of another customer's order existence.

Workflow changes:
- Keep email extraction.
- Replace eager order retrieval before the decision agent with request-scope
  preparation. Extracted IDs remain unverified lookup inputs.
- Do not preload order details into the decision agent's prompt.
- Let tools retrieve and verify facts when called.
- Preserve safe human-review handling when verification cannot be completed.

Boundaries:
- Access PostgreSQL only through repositories.
- A supplied customer ID is not authentication. Bind customer scope to an
  authenticated caller before public deployment.
- Keep these tools read-only. Business-action authorization belongs to the
  deterministic policy engine.
- Structured action proposals remain Phase 6 work.
- Add inventory, invoice, RMA, and knowledge-base tools only when their
  corresponding use cases are implemented.

Tests:
- Test every tool independently without an LLM or API key.
- Cover successful retrieval, missing records, invalid inputs, database
  failures, and cross-customer access.
- Verify that model arguments cannot override customer scope.
- Verify that returned facts reflect database records.
- Test workflow integration using simulated agent tool calls.

Why: tool selection should retrieve needed business facts, while deterministic
code retains control of validation and authorization.

Done when: the agent can obtain customer/order facts through meaningful
repository-backed tool calls, access checks cannot be bypassed, and the workflow
remains working.

## Phase 6: Decision Agent

Refactor the decision agent to receive extraction and request context, select
relevant tools, and produce a structured `AgentProposal` grounded in verified
tool results. It proposes actions but does not authorize them or verify ownership.

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

Begin Phase 6: replace the combined decision/draft output with a structured
`AgentProposal` grounded in tool-recorded evidence. Preserve application-controlled
customer scope, deterministic ownership checks and the missing-evidence guard.
Business-action authorization remains Phase 7 work.
