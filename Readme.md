# Calendar Agent

A natural-language assistant for creating Google Calendar events, available
as a CLI chat loop and as a web app with an HTML form. Both share the same
event-building and Calendar API logic; see `core/` below.

Based on the quickstart at
https://developers.google.com/workspace/calendar/api/quickstart/python,
extended with a LangChain agent (see `core/agent.py`).

## Project structure

```
core/     shared logic: config, logging, event-body building, Calendar API client, LangChain agent
cli/      terminal chat loop, desktop OAuth flow (InstalledAppFlow)
webapp/   FastAPI + HTML form, web OAuth flow (browser redirect)
scripts/  standalone dev utilities (not part of either app)
archives/ earlier iterations, kept for reference
tests/    tests for core/ logic
```

## Setup

```bash
conda env create -f calendar-agent-env.yml
conda activate calendar-agent-env
# or: pip install -e .
```

Create a `.env` file (gitignored) with your API keys:

```
HOME_MAC_OPENAI_API_KEY=...
HOME_MAC_ANTHROPIC_API_KEY=...
```

### Google Cloud credentials

- **CLI**: download a **Desktop app** OAuth client and save it as
  `cli/gcp-desktop-client-credentials.json`.
- **Web app**: download a **Web application** OAuth client (redirect URI
  `http://localhost:8000/oauth2callback`) and save it as
  `webapp/gcp-web-client-credentials.json`. See `webapp/README.md` for the
  full Google Cloud Console walkthrough.

Both are gitignored; neither is committed to this repo.

### Enabling test users

New Google Cloud projects default to "Testing" mode, which limits access to
a manually defined list of authorized testers:

1. Google Cloud Console → APIs & Services → OAuth consent screen.
2. User Type: External.
3. Under Test users, add the Gmail/Workspace addresses of your testers.

## Running

**CLI:**

```bash
python -m cli
```

**Web app:**

```bash
python -m uvicorn webapp.app:app --reload
```

## References

- Reference for adding an LLM to create calendar events from free-form text:
  - https://github.com/jonathantan12/agent-tan/tree/a0f08d3a15223a243dc1851a537cab091954d5c6/google-calendar-ai-agent
  - https://medium.com/@jonathantan12/how-to-build-a-python-ai-agent-for-google-calendar-using-singapores-sea-lion-llm-8224e5e016a7
  - https://medium.com/@swatiagrawal_26/%EF%B8%8F-building-a-simple-ai-tool-to-extract-calendar-events-using-openai-sdk-9c65be613d59
