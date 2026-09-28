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
# Set OPENAI_API_KEY in .env for live extraction and decision calls.
python -m uvicorn app.main:app --reload
```

Use `/docs` for the API and `/health` for a health check. `POST /emails/analyze`
accepts `customer_id`, `email_subject`, and `email_body`. It returns a draft;
it does not send email or execute business actions.

```powershell
python -m pytest -q
```

Tests disable dotenv loading and use mocked model calls; no API key or database
is required. Production lookups still use demonstration mock data. PostgreSQL
models and an Alembic migration are scaffolding for the next phase.

## Status and limitations

Phases 1-3 are complete; Phase 4 (PostgreSQL repositories) is next. See
[the roadmap](docs/ROADMAP.md) and [the change log](CHANGELOG.md).

The API currently trusts the supplied customer ID. Authentication and binding
that ID to an authenticated caller are required before public deployment.
Tool access is restricted to validation-approved facts, but generated prose
still needs the planned policy and grounded-drafting stages. This is a local
prototype, not a production service. Publishing source to GitHub does not host
or deploy the API.
