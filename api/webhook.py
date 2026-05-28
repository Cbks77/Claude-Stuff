from http.server import BaseHTTPRequestHandler
import json
import os
import re
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
        return "Setup error: OPENROUTER_API_KEY not configured."
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
        err = e.read().decode()
        print(f"[OpenRouter {e.code}] {err[:300]}")
        return f"AI error {e.code}: {err[:150]}"
    except Exception as e:
        print(f"[OpenRouter error] {e}")
        return f"AI error: {e}"


def send_whatsapp(to: str, text: str):
    if not KAPSO_API_KEY:
        print("[ERROR] KAPSO_API_KEY not set")
        return None
    # strip non-digits except leading +
    to_clean = re.sub(r"[^\d]", "", to)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_clean,
        "type": "text",
        "text": {"body": text[:4000]},
    }
    req = urllib.request.Request(
        f"https://api.kapso.ai/meta/whatsapp/v24.0/{KAPSO_PHONE_NUMBER_ID}/messages",
        data=json.dumps(payload).encode(),
        headers={"X-API-Key": KAPSO_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode())
            print(f"[Kapso sent ok] to={to_clean}")
            return resp
    except urllib.error.HTTPError as e:
        print(f"[Kapso {e.code}] {e.read().decode()[:300]}")
    except Exception as e:
        print(f"[Kapso send error] {e}")
    return None


def find_sender(raw: str, body: dict) -> str | None:
    """Try every known location for the sender phone number."""
    candidates = []

    # 1. Standard Meta format
    try:
        msgs = (body.get("entry", [{}])[0]
                    .get("changes", [{}])[0]
                    .get("value", {})
                    .get("messages", []))
        if msgs:
            candidates.append(msgs[0].get("from"))
    except Exception:
        pass

    # 2. Kapso wrapped Meta format
    for wrapper_key in ("payload", "data", "message", "event"):
        try:
            inner = body.get(wrapper_key, {})
            msgs = (inner.get("entry", [{}])[0]
                        .get("changes", [{}])[0]
                        .get("value", {})
                        .get("messages", []))
            if msgs:
                candidates.append(msgs[0].get("from"))
        except Exception:
            pass

    # 3. Direct fields on body or body.data / body.message
    for section in [body, body.get("data", {}), body.get("message", {}),
                    body.get("contact", {}), body.get("customer", {})]:
        if not isinstance(section, dict):
            continue
        for key in ("from", "sender", "phone_number", "wa_id", "phone", "msisdn", "number"):
            val = section.get(key)
            if val and isinstance(val, str):
                candidates.append(val)

    # 4. Regex fallback — grab any phone-like number from raw JSON
    #    that is NOT our own bot number
    phones = re.findall(r'"(\+?[1-9]\d{7,14})"', raw)
    bot_ids = {KAPSO_PHONE_NUMBER_ID, "12028808947", "2028808947"}
    for p in phones:
        cleaned = re.sub(r"[^\d]", "", p)
        if cleaned not in bot_ids and len(cleaned) >= 8:
            candidates.append(p)

    for c in candidates:
        if c:
            return str(c)
    return None


def find_text(body: dict) -> str | None:
    """Try every known location for the message text."""
    # Standard Meta
    try:
        msgs = (body.get("entry", [{}])[0]
                    .get("changes", [{}])[0]
                    .get("value", {})
                    .get("messages", []))
        if msgs and msgs[0].get("type") == "text":
            return msgs[0]["text"]["body"]
    except Exception:
        pass

    # Recursive search for text/body/content in nested dicts
    def _search(obj, depth=0):
        if depth > 6 or not isinstance(obj, dict):
            return None
        for key in ("body", "text", "content", "message", "msg"):
            val = obj.get(key)
            if isinstance(val, str) and len(val) > 0:
                return val
            if isinstance(val, dict):
                t = val.get("body") or val.get("text") or val.get("content")
                if isinstance(t, str):
                    return t
        for val in obj.values():
            if isinstance(val, dict):
                result = _search(val, depth + 1)
                if result:
                    return result
        return None

    return _search(body)


class handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(fmt % args)

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        challenge = params.get("hub.challenge", ["OK"])[0]
        self._ok(challenge)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_bytes = self.rfile.read(length)
        raw = raw_bytes.decode("utf-8", errors="replace")

        try:
            body = json.loads(raw)
        except Exception as e:
            print(f"[JSON ERROR] {e} | raw={raw[:300]}")
            self._ok("OK")
            return

        sender = find_sender(raw, body)
        text   = find_text(body)

        # Single line with everything visible
        print(f"[RESULT] sender={sender!r} text={text!r} type={body.get('type')} keys={list(body.keys())} raw={raw[:400]}")

        if not sender:
            print("[SKIP] could not find sender")
            self._ok("OK")
            return

        if not text:
            # Send the raw payload back so we can debug the format
            send_whatsapp(sender, f"[debug] payload keys: {list(body.keys())} | raw: {raw[:600]}")
            self._ok("OK")
            return

        if text.strip().lower() in ("/reset", "reset", "/clear", "clear"):
            send_whatsapp(sender, "Fresh start! What can I help you with?")
            self._ok("OK")
            return

        reply = ask_llm(text)
        print(f"[REPLY] {reply[:120]}")
        send_whatsapp(sender, reply)
        self._ok("OK")

    def _ok(self, body: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())
