"""CLI entrypoint: a REPL that turns natural-language input into Google
Calendar events.

Run with:
    python -m cli
"""
import os.path
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage

from cli.auth import get_calendar_service
from core.agent import build_calendar_agent, run_agent
from core.logging_config import setup_logging

setup_logging(__name__, log_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log"))


def main():
    print("Initializing Google Calendar service...")
    print("If this is your first time, a browser window will open for authentication.")
    if not get_calendar_service():
        print("FATAL ERROR: Could not authenticate with Google Calendar.")
        print("Please check your credentials.json file and network connection.")
        raise SystemExit(1)
    print("Authentication successful! Calendar service is ready.")

    agent = build_calendar_agent(get_calendar_service)

    print("Create Google Calendar events.")
    print()
    print("Some prompt examples that you can use below:")
    print("  - Create an event titled 'Gym' for 2026-05-25 at 6 PM")
    print("  - Create an event with description 'Discuss project updates' on 2026-05-25 from 3 PM to 4 PM")
    print("  - Create an event at location 'Office' on 2026-05-25 from 10 AM to 11 AM")
    print()
    print("Commands: 'quit' or 'exit' to end")
    print("=" * 60)

    history: list[BaseMessage] = []

    while True:
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "q", ""]:
            print("Goodbye!")
            break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] User input: {user_input}")  # Log user input with timestamp

        user_input = timestamp + " - " + user_input  # Prepend timestamp to user input for agent context
        print("Agent: ", end="", flush=True)
        response = run_agent(agent, user_input, history)
        print(response.content)
        print()

        # Update conversation history
        history += [HumanMessage(content=user_input), response]


if __name__ == "__main__":
    main()
