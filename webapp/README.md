# Web app

A FastAPI front-end for creating Google Calendar events via an HTML form,
using the web (browser-redirect) OAuth2 flow.

## Install the necessary dependencies

```bash
pip install fastapi uvicorn google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-multipart itsdangerous
```

(Or, from the repo root, `pip install -e .` — see the top-level `pyproject.toml`.)

## Run & test

From the repo root:

```bash
python -m uvicorn webapp.app:app --reload
```

## Google Cloud setup

To set up a Python web app for testing with the Google Calendar API, you will
configure a Google Cloud project, download your OAuth 2.0 credentials, and
use the Google API client libraries in a local Python virtual environment to
handle user authentication.

### Enable the Google Calendar API

1. Navigate to the Google Cloud Console.
2. Create a New Project.
3. Click Enable APIs and Services and search for Google Calendar API. Enable it.

### Configure OAuth consent and credentials

Because you are building a web application, you will need to authenticate
test users securely.

1. Go to the OAuth consent screen in the sidebar. Choose External for the
   User Type and fill out the required app name and support email.
2. Under Scopes, add `.../auth/calendar` (or `calendar.readonly` if you only
   need to view events).
3. Under Test users, add the email address of the Google account you will
   use for testing.
4. Go to Credentials, click Create Credentials, and select OAuth client ID.
5. Set the Application type to Web application.
6. Add `http://localhost:8000` (or your chosen local port) to the Authorized
   redirect URIs.
7. Click Create and download the credentials file. Save it as
   `webapp/gcp-web-client-credentials.json` (gitignored).

**Must use `http://localhost` as opposed to `http://127.0.0.1`** — Google
explicitly blocks the `127.0.0.1` loopback but allows `localhost`-based
testing.
