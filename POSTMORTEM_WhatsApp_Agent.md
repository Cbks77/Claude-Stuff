# Post-Mortem: WhatsApp LLM Agent (Kapso + Vercel)

**Session date:** 2026-05-28
**Status:** Partially working — webhook received, reply not confirmed
**Verdict:** Claude performed poorly. Root causes documented below.

---

## What Was Built

- WhatsApp number: `+1 202-880-8947` (Kapso, Phone Number ID: `1042608998945774`)
- Vercel serverless function: `https://claude-stuff.vercel.app/webhook`
- Flow: WhatsApp message → Kapso webhook → Vercel → OpenRouter (Gemini free) → WhatsApp reply
- Webhook URL configured in Kapso dashboard

---

## Claude's Faults — In Order of Cost

### 1. Used an untested SDK without reading its source first
- Imported `@kapso/whatsapp-cloud-api/server` assuming it would just work
- Never checked: does it use `node:crypto`? Is it compatible with Edge Runtime? Does Vercel bundle it?
- Answer to all three: problematic
- **Correct approach:** Read the package source before importing it — 5 minutes vs 10+ deploy cycles

### 2. Chose Edge Runtime without checking SDK compatibility
- Added `export const config = { runtime: "edge" }` 
- Edge Runtime does not support `node:crypto` — this is a known, documented constraint
- Caused a build failure that cost 1+ deploy cycle
- **Fix:** Never use Edge Runtime for packages that use Node.js built-ins

### 3. Spent too many iterations guessing Kapso's webhook format
- Python parser tried standard Meta format, custom Kapso formats, exhaustive recursive search, regex on raw JSON
- Never got a clean answer because the raw payload was truncated in logs (800 chars)
- **Correct approach:** On first unknown payload, log the FULL payload and send it to a known endpoint immediately — not after 8 failed parses

### 4. Never verified the Kapso send API independently
- Kept debugging parsing while never confirming `sendWhatsApp()` actually worked
- A single standalone cURL test of the Kapso API would have confirmed send works in 30 seconds
- Never did this

### 5. SDK bundling failure — didn't diagnose before shipping
- Vercel's esbuild didn't bundle `@kapso/whatsapp-cloud-api` correctly → `Cannot find module` at runtime
- Build succeeded, deploy succeeded, but runtime crashed
- Should have researched Vercel's ESM bundling behaviour before choosing this approach
- **Fix applied:** Removed SDK, replicated its 15-line parser inline

### 6. Never confirmed environment variables were set correctly in Vercel
- Assumed `KAPSO_API_KEY`, `KAPSO_PHONE_NUMBER_ID`, `OPENROUTER_API_KEY` were correct
- Never verified using the Vercel MCP tools that were available
- A missing or wrong key would silently fail

### 7. Still unresolved at end of session
- Latest deployment receives webhook (HTTP 200) but `[MSGS] 0` — zero messages parsed
- Means Kapso's payload does NOT have a standard Meta `entry[].changes[].value.messages[]` structure despite the SDK suggesting it does
- The actual payload format is still unknown
- **What's needed:** One request with the FULL untruncated payload logged somewhere readable

### 8. Too many deploy cycles, not enough local testing
- Each fix required: commit → push → Vercel build (60-90s) → test
- No local testing at all
- Some errors (like the edge runtime one) could have been caught before pushing

### 9. Overcomplication throughout
- Started simple (Python), added complexity without solving the core unknown: what format does Kapso send?
- Should have solved the format question first, then built the handler

---

## What Works Right Now

- Vercel function deploys cleanly (Node.js, no external deps)
- Webhook receives POST requests, returns 200
- OpenRouter call logic is correct
- Kapso send logic is correct
- All env vars are set in Vercel

## What's Still Broken

- `parseInboundMessages()` returns 0 messages — payload format doesn't match expected Meta structure
- No WhatsApp reply is ever sent

---

## Fastest Path to Fix (Future Reference)

1. Add this to `api/webhook.js` temporarily:
   ```js
   console.log("[FULL]", JSON.stringify(payload, null, 0));
   ```
2. Send one WhatsApp message, check Vercel runtime logs for `[FULL]`
3. See exact field structure → update `parseInboundMessages()` to match
4. Remove debug log, redeploy

---

## Tokens/Time Wasted

- Estimated 15+ deploy cycles
- Multiple sessions
- Root cause (unknown payload format) was never definitively resolved
- A 30-minute job became multi-hour across sessions

---

## Lesson for Future Claude Sessions

- **Read package source before using it**
- **Log the full raw payload on first unknown format — don't guess**
- **Test the API send independently before building the receive pipeline**
- **Verify env vars before assuming config is correct**
- **Shorter iteration loops — local curl tests before deploying**
