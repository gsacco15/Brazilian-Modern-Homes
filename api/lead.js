// POST /api/lead: saves one early-list sign-up from the landing page.
//
// Storage: Upstash Redis (Vercel dashboard > Storage > Upstash for Redis > Connect to this project).
// Connecting it adds KV_REST_API_URL / KV_REST_API_TOKEN (or UPSTASH_REDIS_REST_URL / _TOKEN).
// Optional email alert per sign-up: set RESEND_API_KEY, NOTIFY_EMAIL (and NOTIFY_FROM if your
// domain is verified with Resend).

const FIELDS = ["name", "email", "phone", "location", "situation", "home", "budget", "timing", "notes",
  "consent", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "variant", "referrer", "landing_url"];

function store() {
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
  return url && token ? { url, token } : null;
}

async function redis(cmd) {
  const s = store();
  const r = await fetch(s.url, {
    method: "POST",
    headers: { Authorization: `Bearer ${s.token}`, "Content-Type": "application/json" },
    body: JSON.stringify(cmd),
  });
  if (!r.ok) throw new Error(`storage ${r.status}`);
  return r.json();
}

function clean(v, max) {
  return String(v == null ? "" : v).replace(/[\u0000-\u001f]/g, " ").trim().slice(0, max);
}

async function notify(lead) {
  const key = process.env.RESEND_API_KEY, to = process.env.NOTIFY_EMAIL;
  if (!key || !to) return;
  const lines = FIELDS.filter((k) => lead[k]).map((k) => `${k}: ${lead[k]}`).join("\n");
  try {
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: process.env.NOTIFY_FROM || "Casa Pátio <onboarding@resend.dev>",
        to: [to],
        subject: `New early-list sign-up: ${lead.name} (${lead.situation})`,
        text: lines,
      }),
    });
  } catch (e) { /* the sign-up is already saved; the alert is best effort */ }
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "method_not_allowed" });
  }
  let body = req.body || {};
  if (typeof body === "string") {
    try { body = Object.fromEntries(new URLSearchParams(body)); } catch (e) { body = {}; }
  }
  if (body["bot-field"]) return res.status(200).json({ ok: true });   // honeypot: quietly drop bots

  const lead = { ts: new Date().toISOString() };
  for (const k of FIELDS) lead[k] = clean(body[k], k === "notes" ? 2000 : 300);
  if (lead.name.length < 2 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(lead.email) || !lead.situation) {
    return res.status(400).json({ error: "missing_fields" });
  }
  if (!store()) {
    console.error("Lead NOT saved: connect Upstash Redis to this Vercel project.", JSON.stringify(lead));
    return res.status(503).json({ error: "storage_not_configured" });
  }
  try {
    await redis(["LPUSH", "leads", JSON.stringify(lead)]);
  } catch (e) {
    console.error("Lead NOT saved:", e.message, JSON.stringify(lead));
    return res.status(502).json({ error: "storage_error" });
  }
  await notify(lead);
  return res.status(200).json({ ok: true });
};
