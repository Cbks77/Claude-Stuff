# Kapso.ai WhatsApp Agent Integration

Connect to [Kapso.ai](https://kapso.ai) and provision a digital number for your WhatsApp agent pipeline.

## Quick Start

### 1. Provision your digital number

```bash
python kapso_integration.py
```

This script will:
- Verify your API key
- List any existing phone numbers on your account
- Attempt to provision a new digital number
- Generate a setup link if direct provisioning requires browser confirmation

### 2. Configure your environment

```bash
cp .env.kapso .env
# Then fill in KAPSO_PHONE_NUMBER_ID with the ID returned in step 1
```

### 3. Run the WhatsApp agent pipeline

```bash
export KAPSO_PHONE_NUMBER_ID=<your-number-id>
python kapso_whatsapp_agent.py
```

---

## Credentials

| Variable | Value |
|---|---|
| `KAPSO_API_KEY` | `bdfee3d96ec07cbd1c74a40896c3b76f8db3178ecaef345193d63d076669df4d` |
| `KAPSO_BASE_URL` | `https://api.kapso.ai` |
| `KAPSO_PHONE_NUMBER_ID` | _(run `kapso_integration.py` to get this)_ |

---

## Key API Endpoints (Kapso Meta Proxy)

| Operation | Method | Path |
|---|---|---|
| Send message | `POST` | `/meta/whatsapp/v24.0/{phone_number_id}/messages` |
| List numbers | `GET` | `/platform/v1/phone_numbers` |
| Get number details | `GET` | `/meta/whatsapp/v24.0/{phone_number_id}` |
| Provision number | `POST` | `/platform/v1/phone_numbers` |

**Auth header:** `X-API-Key: <your-api-key>`

---

## Send a Message (cURL)

```bash
curl -X POST "https://api.kapso.ai/meta/whatsapp/v24.0/$KAPSO_PHONE_NUMBER_ID/messages" \
  -H "X-API-Key: $KAPSO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "15551234567",
    "type": "text",
    "text": { "body": "Hello from my AI agent! 🤖" }
  }'
```

---

## Webhook for Incoming Messages

Configure your webhook URL in the [Kapso dashboard](https://app.kapso.ai) to receive incoming messages. Events include:
- `message.received`
- `message.sent`
- `conversation.inactive`

---

## References

- [Kapso Docs](https://docs.kapso.ai)
- [Connect WhatsApp](https://docs.kapso.ai/docs/how-to/whatsapp/connect-whatsapp)
- [API & Webhooks](https://docs.kapso.ai/docs/integrations/api-webhooks)
- [List Phone Numbers](https://docs.kapso.ai/api/meta/whatsapp/phone-numbers/list-phone-numbers)
- [Connect Phone Number](https://docs.kapso.ai/api/platform/v1/phone-numbers/connect-phone-number)
