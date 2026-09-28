# AI Customer Support Copilot

Agentic B2B email-support prototype using FastAPI, Pydantic and the OpenAI
Agents SDK. Extraction feeds deterministic validation, followed by a decision
agent with request-scoped read tools. Invalid records produce a fixed human
review response without invoking the decision agent.

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
Read sessions close after each lookup; agents receive only validation-approved
facts. Missing configuration, database failures and malformed records route to
human review, with no mock fallback or connection details in the response.

The seed command is an explicit local administration step. It inserts missing
demo customers/orders in one transaction and preserves existing rows. It does
not run at startup and is not an agent-callable write tool. `app/mock_data.py`
now supplies demo seed values only.

## Status and limitations

Phases 1-4 are complete; Phase 5 (focused, typed agent tools) is next. See
[the roadmap](docs/ROADMAP.md) and [the change log](CHANGELOG.md).

The API currently trusts the supplied customer ID. Authentication and binding
that ID to an authenticated caller are required before public deployment.
Tool access is restricted to validation-approved facts, but generated prose
still needs the planned policy and grounded-drafting stages. This is a local
prototype, not a production service. Publishing source to GitHub does not host
or deploy the API.
