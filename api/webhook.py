from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

KAPSO_API_KEY         = os.environ.get("KAPSO_API_KEY", "")
KAPSO_PHONE_NUMBER_ID = os.environ.get("KAPSO_PHONE_NUMBER_ID", "1042608998945774")
OPENROUTER_API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
MODEL                 = os.environ.get("MODEL", "google/gemini-2.0-flash-exp:free")

SYSTEM_PROMPT = (
    "You are a smart, concise AI assistant for Curtis Brooks. "
    "You help him work on the move via WhatsApp — coding, planning, research, writing, anything. "
    "Keep replies short and clear unless detail is asked for. Use plain text, no markdown."
)


def ask_llm(message: str) -> str:
    if not OPENROUTER_API_KEY:
        print("[ERROR] OPENROUTER_API_KEY env var not set")
        return "Setup error: OPENROUTER_API_KEY not configured on server."
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cbks77.com",
            "X-Title": "Curtis WhatsApp Agent",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            result = json.loads(r.read().decode())
            return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[OpenRouter error {e.code}] {body}")
        return f"AI error ({e.code}): {body[:200]}"
    except Exception as e:
        print(f"[OpenRouter error] {e}")
        return f"AI error: {e}"


def send_whatsapp(to: str, text: str):
    if not KAPSO_API_KEY:
        print("[ERROR] KAPSO_API_KEY env var not set")
        return
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
            resp = json.loads(r.read().decode())
            print(f"[Kapso sent] {resp}")
            return resp
    except urllib.error.HTTPError as e:
        print(f"[Kapso error {e.code}] {e.read().decode()}")
    except Exception as e:
        print(f"[Kapso send error] {e}")


def parse_message(body: dict):
    """Standard Meta WhatsApp Cloud API format."""
    try:
        messages = (
            body.get("entry", [{}])[0]
                .get("changes", [{}])[0]
                .get("value", {})
                .get("messages", [])
        )
        if not messages or messages[0].get("type") != "text":
            return None
        return messages[0]["from"], messages[0]["text"]["body"]
    except Exception:
        return None


def parse_kapso_message(body: dict):
    """Kapso webhook event format — handles all known type variants."""
    try:
        event_type = body.get("type", "")

        # Kapso formats: "whatsapp.message", "whatsapp.message.received", "message.received"
        if "message" in event_type:
            # Try body.data first
            data = body.get("data") or body.get("message") or body
            if isinstance(data, dict):
                sender = (data.get("from") or data.get("sender") or
                          data.get("phone_number") or data.get("wa_id"))
                msg = data.get("text") or data.get("message") or data.get("body") or {}
                text = msg.get("body") if isinstance(msg, dict) else msg
                if not text:
                    text = data.get("body") or data.get("content")
                if sender and text:
                    return str(sender), str(text)

        # Flat format: { "from": "...", "body": "..." }
        sender = body.get("from") or body.get("sender")
        text = body.get("body") or body.get("text") or body.get("content")
        if isinstance(text, dict):
            text = text.get("body")
        if sender and text:
            return str(sender), str(text)

        return None
    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return None


class handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"{fmt % args}")

    # Kapso webhook verification (GET)
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        challenge = params.get("hub.challenge", ["OK"])[0]
        self._ok(challenge)

    # Incoming WhatsApp message (POST)
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        print(f"[RAW] {raw.decode()[:2000]}")

        try:
            body = json.loads(raw.decode())
        except Exception as e:
            print(f"[JSON ERROR] {e}")
            self._ok("OK")
            return

        # Try both payload formats
        result = parse_message(body) or parse_kapso_message(body)

        if not result:
            print(f"[SKIP] Unknown payload keys: {list(body.keys())}")
            self._ok("OK")
            return

        sender, text = result
        print(f"[IN] {sender}: {text}")

        if text.strip().lower() in ("/reset", "reset", "/clear", "clear"):
            send_whatsapp(sender, "Fresh start! What can I help you with?")
            self._ok("OK")
            return

        # Call LLM and send reply BEFORE returning 200
        # (Vercel stops execution after response is sent)
        reply = ask_llm(text)
        print(f"[OUT] {reply[:120]}")
        send_whatsapp(sender, reply)

        self._ok("OK")  # respond last so Vercel doesn't kill the function early

    def _ok(self, body: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())
