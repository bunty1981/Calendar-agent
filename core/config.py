"""Shared configuration: environment variables and constants used by both the
CLI and web app.
"""
import os

from dotenv import load_dotenv  # *** If using this method ensure .env is listed in .gitignore so it STAYS local

load_dotenv()  # Load environment variables from .env file

# If modifying this scope, delete cli/token.json so a fresh consent is captured.
SCOPES = ["https://www.googleapis.com/auth/calendar"]  # Read-write scope
# SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]  # Read only scope

DEFAULT_TIMEZONE = "America/Los_Angeles"

# Running on local machines: assumes HOME_MAC_OPENAI_API_KEY / HOME_MAC_ANTHROPIC_API_KEY
# are set in .env.
OPENAI_API_KEY = os.getenv("HOME_MAC_OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("HOME_MAC_ANTHROPIC_API_KEY")
