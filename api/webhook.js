import { normalizeWebhook } from "@kapso/whatsapp-cloud-api/server";

const KAPSO_API_KEY         = process.env.KAPSO_API_KEY         || "";
const KAPSO_PHONE_NUMBER_ID = process.env.KAPSO_PHONE_NUMBER_ID || "1042608998945774";
const OPENROUTER_API_KEY    = process.env.OPENROUTER_API_KEY    || "";
const MODEL                 = process.env.MODEL                 || "google/gemini-2.0-flash-exp:free";

const SYSTEM_PROMPT =
  "You are a smart, concise AI assistant for Curtis Brooks. " +
  "You help him work on the move via WhatsApp — coding, planning, research, writing, anything. " +
  "Keep replies short and clear unless detail is asked for. Use plain text, no markdown.";

async function askLLM(message) {
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://cbks77.com",
      "X-Title": "Curtis WhatsApp Agent",
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user",   content: message },
      ],
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    console.error("[OpenRouter error]", res.status, JSON.stringify(data));
    return `AI error ${res.status}: ${JSON.stringify(data).slice(0, 200)}`;
  }
  return data.choices[0].message.content.trim();
}

async function sendWhatsApp(to, text) {
  const clean = to.replace(/\D/g, "");
  const res = await fetch(
    `https://api.kapso.ai/meta/whatsapp/v24.0/${KAPSO_PHONE_NUMBER_ID}/messages`,
    {
      method: "POST",
      headers: {
        "X-API-Key": KAPSO_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messaging_product: "whatsapp",
        recipient_type: "individual",
        to: clean,
        type: "text",
        text: { body: text.slice(0, 4000) },
      }),
    }
  );
  const data = await res.json();
  if (!res.ok) console.error("[Kapso send error]", res.status, JSON.stringify(data));
  else console.log("[Kapso sent ok] to=" + clean);
  return data;
}

export default async function handler(req) {
  // Webhook verification (GET)
  if (req.method === "GET") {
    const url  = new URL(req.url);
    const challenge = url.searchParams.get("hub.challenge") || "OK";
    return new Response(challenge, { status: 200 });
  }

  // Incoming webhook (POST)
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const raw = await req.text();
  console.log("[RAW]", raw.slice(0, 800));

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (e) {
    console.error("[JSON parse error]", e.message);
    return new Response("OK", { status: 200 });
  }

  // Use Kapso's official normalizer — handles all their webhook formats
  let events;
  try {
    events = normalizeWebhook(payload);
  } catch (e) {
    console.error("[normalizeWebhook error]", e.message);
    events = { messages: [] };
  }

  console.log("[EVENTS] messages=" + (events.messages?.length || 0));

  for (const msg of events.messages || []) {
    console.log("[MSG]", JSON.stringify(msg).slice(0, 300));

    // Only handle inbound text messages
    if (msg.type !== "text") continue;
    if (msg.kapso?.direction === "outbound") continue;

    const sender = msg.from;
    const text   = msg.text?.body || "";

    if (!sender || !text) continue;

    console.log("[IN]", sender, ":", text);

    if (["reset", "/reset", "clear", "/clear"].includes(text.trim().toLowerCase())) {
      await sendWhatsApp(sender, "Fresh start! What can I help you with?");
      continue;
    }

    const reply = await askLLM(text);
    console.log("[OUT]", reply.slice(0, 120));
    await sendWhatsApp(sender, reply);
  }

  return new Response("OK", { status: 200 });
}

export const config = { runtime: "edge" };
