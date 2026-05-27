#!/usr/bin/env python3
"""
Kapso.ai API Integration
Connects to Kapso API and provisions a digital phone number for WhatsApp agent pipeline.

Usage:
    python kapso_integration.py
"""

import json
import sys
import os
import urllib.request
import urllib.error
import urllib.parse

KAPSO_API_KEY = os.environ.get(
    "KAPSO_API_KEY",
    "bdfee3d96ec07cbd1c74a40896c3b76f8db3178ecaef345193d63d076669df4d"
)
BASE_URL = "https://api.kapso.ai"


def make_request(path: str, method: str = "GET", body: dict = None) -> dict:
    """Make an authenticated request to the Kapso API."""
    url = f"{BASE_URL}{path}"
    headers = {
        "X-API-Key": KAPSO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return {"status": resp.status, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw}
        return {"status": e.code, "error": str(e), "data": payload}
    except urllib.error.URLError as e:
        return {"status": 0, "error": str(e), "data": {}}


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def pretty(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


# ─────────────────────────────────────────────
# 1. Verify API key / get account profile
# ─────────────────────────────────────────────
section("1. Verifying API Key")
me = make_request("/platform/v1/me")
print(f"Status: {me['status']}")
pretty(me["data"])
customer_id = me["data"].get("id") or me["data"].get("customer_id") or me["data"].get("customerId")

# ─────────────────────────────────────────────
# 2. List existing digital/phone numbers
# ─────────────────────────────────────────────
section("2. Listing Existing Phone Numbers")

# Try the platform v1 phone numbers endpoint
phone_resp = make_request("/platform/v1/phone_numbers")
print(f"[/platform/v1/phone_numbers] Status: {phone_resp['status']}")
pretty(phone_resp["data"])

# Also try the digital_lines variant
digital_resp = make_request("/platform/v1/digital_lines")
print(f"\n[/platform/v1/digital_lines] Status: {digital_resp['status']}")
pretty(digital_resp["data"])

# If we have a customer_id, try that scoped endpoint too
if customer_id:
    scoped = make_request(f"/platform/v1/customers/{customer_id}/whatsapp/phone_numbers")
    print(f"\n[/platform/v1/customers/{customer_id}/whatsapp/phone_numbers] Status: {scoped['status']}")
    pretty(scoped["data"])

# ─────────────────────────────────────────────
# 3. Get available numbers to buy / provision
# ─────────────────────────────────────────────
section("3. Checking Available Digital Numbers")
avail = make_request("/platform/v1/phone_numbers/available")
print(f"Status: {avail['status']}")
pretty(avail["data"])

# ─────────────────────────────────────────────
# 4. Provision a digital number via Setup Link
# ─────────────────────────────────────────────
section("4. Provisioning Digital Number via Setup Link")

setup_payload = {
    "provision_phone_number": True,
    "phone_number_country_isos": ["US"],   # change to your preferred country
}
setup_resp = make_request("/platform/v1/setup_links", method="POST", body=setup_payload)
print(f"Status: {setup_resp['status']}")
pretty(setup_resp["data"])

setup_link = (
    setup_resp["data"].get("url")
    or setup_resp["data"].get("setup_url")
    or setup_resp["data"].get("link")
)
if setup_link:
    print(f"\n✅  Setup Link (open in browser to complete provisioning):\n{setup_link}")

# ─────────────────────────────────────────────
# 5. Direct number purchase (if endpoint exists)
# ─────────────────────────────────────────────
section("5. Direct Number Provision / Purchase")

buy_payload = {
    "country_iso": "US",
    "number_type": "local",
}
buy_resp = make_request("/platform/v1/phone_numbers", method="POST", body=buy_payload)
print(f"Status: {buy_resp['status']}")
pretty(buy_resp["data"])

# Extract and highlight the provisioned number
provisioned_number = (
    buy_resp["data"].get("phone_number")
    or buy_resp["data"].get("number")
    or buy_resp["data"].get("display_phone_number")
)
provisioned_id = (
    buy_resp["data"].get("id")
    or buy_resp["data"].get("phone_number_id")
)

if provisioned_number or provisioned_id:
    section("✅  YOUR NEW DIGITAL NUMBER")
    if provisioned_number:
        print(f"  Phone Number : {provisioned_number}")
    if provisioned_id:
        print(f"  Number ID    : {provisioned_id}")
    print("\nAdd these to your WhatsApp agent pipeline config:")
    print(f"  KAPSO_PHONE_NUMBER_ID = {provisioned_id or '<see above>'}")
    print(f"  KAPSO_PHONE_NUMBER    = {provisioned_number or '<see above>'}")
else:
    print("\nℹ️  No number returned from direct provision endpoint.")
    print("   Check the Setup Link in Step 4, or see Kapso dashboard:")
    print("   https://app.kapso.ai")

# ─────────────────────────────────────────────
# 6. Summary
# ─────────────────────────────────────────────
section("6. Environment Config for WhatsApp Agent")
print(f"""
Add these to your .env or pipeline config:

  KAPSO_API_KEY={KAPSO_API_KEY}
  KAPSO_BASE_URL={BASE_URL}
  # KAPSO_PHONE_NUMBER_ID=<your-phone-number-id>

WhatsApp Cloud API proxy base URL (for sending messages):
  {BASE_URL}/meta/whatsapp/v24.0/<PHONE_NUMBER_ID>/messages

Authentication header:  X-API-Key: {KAPSO_API_KEY}
""")
