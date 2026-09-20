# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A natural-language assistant for creating Google Calendar events, available as a CLI chat loop (LangChain agent) and as a FastAPI web app (fixed HTML form). Both share the same event-building and Calendar API logic in `core/`.

## Setup

```bash
conda env create -f calendar-agent-env.yml && conda activate calendar-agent-env
# or: pip install -e .
```

Requires a `.env` file (gitignored) with `HOME_MAC_OPENAI_API_KEY` and `HOME_MAC_ANTHROPIC_API_KEY`, and OAuth client credentials from Google Cloud Console:
- CLI: Desktop app client saved as `cli/gcp-desktop-client-credentials.json`
- Web app: Web application client (redirect URI `http://localhost:8000/oauth2callback`) saved as `webapp/gcp-web-client-credentials.json` — must use `http://localhost`, not `127.0.0.1` (Google blocks that loopback for this flow)

Both credential files and `.env` are gitignored and never committed.

## Commands

```bash
python -m cli                                  # run the CLI chat loop
python -m uvicorn webapp.app:app --reload      # run the web app (from repo root)
pytest                                          # run all tests
pytest tests/test_event_builder.py::test_all_day_event_uses_date_only  # run a single test
```

## Architecture

```
core/     shared logic: config, logging, event-body building, Calendar API client, LangChain agent
cli/      terminal chat loop, desktop OAuth flow (InstalledAppFlow)
webapp/   FastAPI + HTML form, web OAuth flow (browser redirect)
scripts/  standalone dev utilities (not part of either app)
archives/ earlier iterations, kept for reference — not maintained, don't fix bugs there
tests/    tests for core/ logic
```

The CLI and web app are two independent entry points that share `core/` but never import from each other:

- **`core/event_builder.py`** — pure function `build_event_body(...)` that turns simple fields (summary, start/end, timezone, `event_type`: `"Timed"` or `"All-day"`) into a Calendar API event resource dict. This was extracted after the same logic was duplicated (and had drifted) between the old CLI and web app; keep it as the single source of truth rather than reintroducing a copy.
- **`core/calendar_client.py`** — thin, auth-agnostic wrapper around `events().insert()`. Callers obtain credentials however suits their own OAuth flow and pass them in; this module doesn't know which flow produced them.
- **`core/agent.py`** — `build_calendar_agent(get_service)` builds a LangChain agent (Claude Haiku) with a single tool, `create_google_calendar_event`, which calls `build_event_body` + `insert_event`. It's parameterized over `get_service` (a zero-arg callable returning an authenticated service or `None`) specifically so it stays decoupled from any one OAuth flow — the CLI passes `cli.auth.get_calendar_service`. The web app doesn't use the agent; it has its own fixed-field form flow instead.
- **Two separate OAuth flows, deliberately not unified**: `cli/auth.py` uses `InstalledAppFlow` (local server + on-disk `cli/token.json` cache) for desktop use; `webapp/auth.py` uses `Flow` (browser-redirect authorization-code flow) with an in-memory `CREDENTIALS_STORAGE` dict keyed by a single hardcoded `SESSION_ID` — a demo-only stand-in for real per-user session/database storage. Both ultimately hand credentials to `core.calendar_client.get_service`.
- **`core/logging_config.py`** — `setup_logging(name, log_file)` is called once per app at startup. It deliberately pins the *root* logger to WARNING regardless of the requested level, because third-party libraries (`requests_oauthlib`, `urllib3`) log full OAuth request/response bodies — including access/refresh tokens and client secrets — at DEBUG. Only the named app logger gets the requested level. Don't relax this without preserving that guarantee.

## Notes

- `SCOPES` in `core/config.py` is the full read-write `.../auth/calendar` scope. If it changes, `cli/token.json` must be deleted so a fresh consent captures the new scope.
- New Google Cloud OAuth consent screens default to "Testing" mode; test users must be added manually under OAuth consent screen → Test users in Google Cloud Console, or auth will fail for anyone not listed.
- The web app's `SessionMiddleware` secret key and `CREDENTIALS_STORAGE` are explicitly marked in-code as dev-only placeholders, not production-ready session/credential handling.
