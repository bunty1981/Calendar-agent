"""FastAPI app that receives Twilio SMS webhooks.

Run with (from the repo root):
    python -m uvicorn sms.app:app --reload --port 8001
"""
import os.path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from core.logging_config import setup_logging

_SMS_DIR = os.path.dirname(os.path.abspath(__file__))
logger = setup_logging(__name__, log_file=os.path.join(_SMS_DIR, "app.log"))

app = FastAPI()


@app.post("/sms/incoming")
async def incoming_sms(request: Request):
    """Twilio's "A message comes in" webhook. Replies to the sender with TwiML."""
    form = await request.form()
    sender = form.get("From")
    body = form.get("Body", "")
    logger.info(f"Incoming SMS from {sender}: {body!r}")

    reply = MessagingResponse()
    reply.message(f"Echo: {body}")
    return Response(content=str(reply), media_type="application/xml")
