#!/usr/bin/env python3
"""
WhatsApp ↔ LLM Bridge
Receives WhatsApp messages via Kapso webhook → sends to OpenRouter → replies on WhatsApp.
"""

import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── Config ────────────────────────────────────────────────────────────────────
KAPSO_API_KEY         = os.environ.get("KAPSO_API_KEY", "")
KAPSO_PHONE_NUMBER_ID = os.environ.get("KAPSO_PHONE_NUMBER_ID", "1042608998945774")
OPENROUTER_API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
MODEL                 = os.environ.get("MODEL", "google/gemini-2.0-flash-exp:free")
PORT                  = int(os.environ.get("PORT", 8080))

# ── Validate required keys ────────────────────────────────────────────────────
_missing = [name for name, val in [("KAPSO_API_KEY", KAPSO_API_KEY), ("OPENROUTER_API_KEY", OPENROUTER_API_KEY)] if not val]
if _missing:
    print(f"[WARNING] Missing required environment variable(s): {', '.join(_missing)}")
    print("[WARNING] The app will start but API calls will fail until these are set.")

SYSTEM_PROMPT = """You are a smart, concise AI assistant for Curtis Brooks.
You help him work on the move via WhatsApp — coding, planning, research, writing, anything.
Keep replies short and clear unless detail is asked for. Use plain text, no markdown."""

# ── Per-user conversation memory (in-memory, resets on restart) ───────────────
conversations: dict[str, list] = {}

def get_history(phone: str) -> list:
    if phone not in conversations:
        conversations[phone] = []
    return conversations[phone]

def add_to_history(phone: str, role: str, content: str):
    get_history(phone).append({"role": role, "content": content})
    # Keep last 20 messages to avoid token bloat
    if len(conversations[phone]) > 20:
        conversations[phone] = conversations[phone][-20:]

# ── OpenRouter call ───────────────────────────────────────────────────────────
def ask_llm(phone: str, user_message: str) -> str:
    add_to_history(phone, "user", user_message)

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(phone),
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cbks77.com",
            "X-Title": "Curtis WhatsApp Agent",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode())
            reply = result["choices"][0]["message"]["content"].strip()
            add_to_history(phone, "assistant", reply)
            return reply
    except Exception as e:
        return f"[Error reaching AI: {e}]"

# ── Send WhatsApp reply via Kapso ─────────────────────────────────────────────
def send_whatsapp(to: str, text: str):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    req = urllib.request.Request(
        f"https://api.kapso.ai/meta/whatsapp/v24.0/{KAPSO_PHONE_NUMBER_ID}/messages",
        data=json.dumps(payload).encode(),
        headers={
            "X-API-Key": KAPSO_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[Kapso error {e.code}] {e.read().decode()}")
    except Exception as e:
        print(f"[Send error] {e}")

# ── Parse incoming Kapso/Meta webhook payload ─────────────────────────────────
def parse_message(body: dict) -> tuple[str, str] | None:
    """Returns (sender_phone, message_text) or None if not a text message."""
    try:
        # Standard Meta WhatsApp Cloud API webhook format
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None
        msg = messages[0]
        if msg.get("type") != "text":
            return None
        sender = msg["from"]
        text = msg["text"]["body"]
        return sender, text
    except Exception:
        return None

# ── HTTP Server ───────────────────────────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def do_GET(self):
        # Kapso/Meta webhook verification
        parsed = urlparse(self.path)
        params = dict(p.split("=") for p in parsed.query.split("&") if "=" in p)
        challenge = params.get("hub.challenge", "")
        self._respond(200, challenge or "OK")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        self._respond(200, "OK")   # always ack quickly

        try:
            body = json.loads(raw.decode())
        except Exception:
            return

        result = parse_message(body)
        if not result:
            return

        sender, text = result
        print(f"[IN]  {sender}: {text}")

        # Handle /reset command to clear conversation memory
        if text.strip().lower() in ("/reset", "reset", "/clear", "clear"):
            conversations.pop(sender, None)
            send_whatsapp(sender, "Conversation cleared. Fresh start! 👋")
            return

        reply = ask_llm(sender, text)
        print(f"[OUT] {sender}: {reply[:80]}...")
        send_whatsapp(sender, reply)

    def _respond(self, code: int, body: str):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())


if __name__ == "__main__":
    print(f"🚀 WhatsApp LLM Bridge running on port {PORT}")
    print(f"   Number  : +1 202-880-8947  (ID: {KAPSO_PHONE_NUMBER_ID})")
    print(f"   Model   : {MODEL}")
    print(f"   Webhook : POST /")
    HTTPServer(("0.0.0.0", PORT), WebhookHandler).serve_forever()
