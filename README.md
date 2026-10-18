# AI Customer Support Copilot

Agentic B2B email-support prototype using FastAPI, Pydantic and the OpenAI
Agents SDK. Extraction feeds a decision agent with repository-backed read tools.
Tools retrieve facts and enforce ownership within an application-controlled
customer scope. Missing evidence or failed lookups produce a fixed human-review
response, even if the agent claims it verified the request.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL to your PostgreSQL database and OPENAI_API_KEY for live calls.
# Create the database/user first; Alembic creates tables, not databases.
python -m alembic upgrade head
python -m app.db.seed
python -m uvicorn app.main:app --reload
```

Use `/docs` for the API and `/health` for a health check. `POST /emails/analyze`
accepts `customer_id`, `email_subject`, and `email_body`. It returns a draft;
it does not send email or execute business actions.

```powershell
python -m pytest -q
```

The default tests use isolated in-memory SQLite with foreign keys enabled and
mocked model calls. No API key or running database is required.

To also run the suite against PostgreSQL, set `TEST_DATABASE_URL` in `.env` (or
the environment) to a separate test database whose user can create schemas:

```powershell
python -m pytest -q --postgres
```

This explicitly requested test run reads only the database settings from `.env`;
it never loads an API key. It creates a random schema, exercises the existing
Alembic migration in both directions, runs the tests, then removes only that
schema. Each test's data changes are rolled back. The suite also checks that the
migration matches the ORM models.

Application lookups use SQLAlchemy repositories returning typed Pydantic records.
Read sessions close after each tool's lookups; agents receive verified tool
results. Missing configuration, database failures and malformed records route to
human review, with no mock fallback or connection details in the response.

The seed command is an explicit local administration step. It inserts missing
demo customers/orders in one transaction and preserves existing rows. It does
not run at startup and is not an agent-callable write tool. `app/mock_data.py`
now supplies demo seed values only.

## Status and limitations

Phases 1-5 are complete; Phase 6 (structured agent proposals) is next. See
[the roadmap](docs/ROADMAP.md) and [the change log](CHANGELOG.md).

The API currently trusts the supplied customer ID. Authentication and binding
that ID to an authenticated caller are required before public deployment.
Tool access is restricted by customer scope, but generated prose
still needs the planned policy and grounded-drafting stages. This is a local
prototype, not a production service. Publishing source to GitHub does not host
or deploy the API.

## Tool-driven request flow

1. `workflow.py` extracts email claims and creates `SupportContext(customer_id)`.
   No order facts are fetched or preloaded into the prompt.
2. The decision agent selects `get_customer()` or `get_order(order_id)`.
   Neither tool accepts a customer ID from the model.
3. Tools query repositories. Order queries filter by both order and customer;
   Python checks ownership again before returning data. Missing and foreign
   orders share the same `unavailable` result.
4. Pydantic result contracts are serialized to JSON for the SDK. Tools record
   verified customer/order evidence in private per-run context state.
5. The workflow checks that required evidence exists and no tool failed before
   accepting the decision. Response identity/product/priority fields come from
   recorded facts. Missing evidence produces a fixed review response.

`validation.py` retains the legacy eager validator for regression coverage and
provides the ownership helper used by the order tool. The live workflow no longer
calls the eager validator. This completeness check is not the full business
policy engine, and it does not validate every claim in generated prose; those
remain Phases 7 and 8. Any failed tool call conservatively requires human review
for this run, even after a later successful lookup.
