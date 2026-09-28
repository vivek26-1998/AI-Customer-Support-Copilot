# Change Log

## 2026-09-28 - Complete Phase 3 workflow integration

### Existing workspace baseline

There were no prior Git commits. This inventory records the code present at
session start; earlier dates and individual historical edits cannot be recovered.

- FastAPI health and email-analysis endpoints with Pydantic input/output models.
- Structured extraction agent and combined decision/drafting agent with customer
  and order read tools; a drafting module placeholder.
- Mock customers/orders and lookup functions.
- ValidationResult and deterministic validation for customer existence, missing
  orders, ownership and incomplete order records; six passing validation tests.
- Workflow passing extraction and validation into the decision agent.
- PostgreSQL dependencies, SQLAlchemy Customer/Order models, session setup,
  Alembic configuration and initial migration (not yet used by application reads).
- Architecture instructions, 13-phase roadmap and environment configuration template.

### Changes in this session

- Identified Phase 3 as the first unfinished completion criterion: validation
  failures still reached the decision model, and tools accepted model-selected
  customer identities without binding them to the request.
- Added deterministic human-review responses on failed validation, withholding
  order/product details and avoiding decision-agent calls.
- Preserved customer/order tool calling while restricting both tools to the
  request's verified validation snapshot. Guessed customer IDs and order IDs
  cannot expand the available facts.
- Set response order ID, product name and priority from validated facts instead
  of model output.
- Added API, workflow and actual tool-invocation regression tests, including
  cross-customer access, unknown/inconsistent data and missing order IDs.
- Disabled dotenv, API credentials and SDK tracing during deterministic tests.
- Updated roadmap and project instructions to point to unfinished Phase 4.
- Added README with setup, test commands and prototype limitations.
- Removed trailing whitespace identified by the staged Git diff check.
- Replaced database credentials in .env.example with placeholders and expanded
  ignore rules for environment files and virtual environments.

### Verification

- Baseline: `python -m pytest -q` - 6 passed.
- Final: `python -m pytest -q` - 22 passed (Python 3.14).
- Reviewed publishable files for credential patterns; no matches. Local .env
  and generated caches are excluded from Git.
- No live LLM calls or PostgreSQL migration runs are part of this phase.

### Publication

Target: https://github.com/vivek26-1998/AI-Customer-Support-Copilot
Source publication only; no application hosting is configured.
