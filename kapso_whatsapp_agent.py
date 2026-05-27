#!/usr/bin/env python3
"""
Kapso.ai WhatsApp Agent Pipeline
---------------------------------
Thin wrapper around the Kapso meta-proxy that lets your agent
send and receive WhatsApp messages using your provisioned digital number.

Requirements: none beyond stdlib (or install `requests` for convenience)

Usage:
    python kapso_whatsapp_agent.py
"""

import json
import os
import urllib.request
import urllib.error

# ── Config ────────────────────────────────────────────────────────────────────
KAPSO_API_KEY        = os.environ.get("KAPSO_API_KEY",
                         "bdfee3d96ec07cbd1c74a40896c3b76f8db3178ecaef345193d63d076669df4d")
KAPSO_BASE_URL       = os.environ.get("KAPSO_BASE_URL", "https://api.kapso.ai")
KAPSO_PHONE_NUMBER_ID = os.environ.get("KAPSO_PHONE_NUMBER_ID", "")   # fill after provisioning
# ─────────────────────────────────────────────────────────────────────────────


class KapsoWhatsApp:
    """Minimal Kapso WhatsApp Cloud API client (meta-proxy flavour)."""

    def __init__(self, api_key: str, phone_number_id: str, base_url: str = KAPSO_BASE_URL):
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.base = base_url.rstrip("/")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _req(self, path: str, method: str = "GET", body: dict = None) -> dict:
        url = f"{self.base}{path}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read().decode()
                return {"ok": True, "status": r.status, "data": json.loads(raw) if raw else {}}
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            return {"ok": False, "status": e.code, "data": json.loads(raw) if raw else {}}
        except Exception as e:
            return {"ok": False, "status": 0, "error": str(e), "data": {}}

    # ── phone number helpers ──────────────────────────────────────────────────

    def list_phone_numbers(self) -> dict:
        """List all WhatsApp phone numbers on the account."""
        return self._req("/platform/v1/phone_numbers")

    def get_phone_number_details(self) -> dict:
        """Get details for the configured phone number."""
        return self._req(
            f"/meta/whatsapp/v24.0/{self.phone_number_id}"
            "?fields=id,verified_name,display_phone_number,quality_rating,"
            "code_verification_status,platform_type,throughput"
        )

    def provision_number(self, country_iso: str = "US") -> dict:
        """Provision (buy) a new digital number."""
        return self._req(
            "/platform/v1/phone_numbers",
            method="POST",
            body={"country_iso": country_iso, "number_type": "local"},
        )

    # ── messaging ─────────────────────────────────────────────────────────────

    def send_text(self, to: str, text: str) -> dict:
        """
        Send a plain-text WhatsApp message.

        Args:
            to:   recipient phone number in E.164 format, e.g. "15551234567"
            text: message body
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        return self._req(
            f"/meta/whatsapp/v24.0/{self.phone_number_id}/messages",
            method="POST",
            body=payload,
        )

    def send_template(self, to: str, template_name: str,
                      language_code: str = "en_US", components: list = None) -> dict:
        """Send a WhatsApp template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                **({"components": components} if components else {}),
            },
        }
        return self._req(
            f"/meta/whatsapp/v24.0/{self.phone_number_id}/messages",
            method="POST",
            body=payload,
        )

    def mark_as_read(self, message_id: str) -> dict:
        """Mark an incoming message as read."""
        return self._req(
            f"/meta/whatsapp/v24.0/{self.phone_number_id}/messages",
            method="POST",
            body={"messaging_product": "whatsapp", "status": "read", "message_id": message_id},
        )


# ── Demo / smoke-test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = KapsoWhatsApp(
        api_key=KAPSO_API_KEY,
        phone_number_id=KAPSO_PHONE_NUMBER_ID,
        base_url=KAPSO_BASE_URL,
    )

    print("=== Kapso WhatsApp Agent Pipeline ===\n")

    # List numbers
    print("[1] Listing phone numbers on account …")
    numbers = client.list_phone_numbers()
    print(json.dumps(numbers, indent=2))

    if not KAPSO_PHONE_NUMBER_ID:
        print("\n⚠️  KAPSO_PHONE_NUMBER_ID is not set.")
        print("   Run  python kapso_integration.py  first to provision a number,")
        print("   then export KAPSO_PHONE_NUMBER_ID=<id> and re-run this script.")
    else:
        # Get details for the configured number
        print(f"\n[2] Phone number details for {KAPSO_PHONE_NUMBER_ID} …")
        details = client.get_phone_number_details()
        print(json.dumps(details, indent=2))

        display = (
            details.get("data", {}).get("display_phone_number")
            or details.get("data", {}).get("phone_number")
            or KAPSO_PHONE_NUMBER_ID
        )
        print(f"\n✅  Your WhatsApp digital number: {display}")
        print("\nReady to plug into your agent pipeline!")
        print(f"  Base URL : {KAPSO_BASE_URL}/meta/whatsapp/v24.0/{KAPSO_PHONE_NUMBER_ID}/messages")
        print(f"  API Key  : {KAPSO_API_KEY}")
