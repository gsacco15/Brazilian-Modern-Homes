// GET /api/leads: returns every sign-up for the /leads page (or ?format=csv for a spreadsheet).
// Protected by the ADMIN_KEY environment variable, sent as the x-admin-key header or ?key=.

const COLS = ["ts", "name", "email", "phone", "location", "situation", "home", "budget", "timing", "notes",
  "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "variant", "referrer", "landing_url"];

function store() {
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
  return url && token ? { url, token } : null;
}

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Robots-Tag", "noindex");
  const admin = process.env.ADMIN_KEY;
  if (!admin) return res.status(503).json({ error: "admin_key_not_set" });
  const given = req.headers["x-admin-key"] || (req.query && req.query.key) || "";
  if (given !== admin) return res.status(401).json({ error: "wrong_key" });
  const s = store();
  if (!s) return res.status(503).json({ error: "storage_not_configured" });

  const r = await fetch(s.url, {
    method: "POST",
    headers: { Authorization: `Bearer ${s.token}`, "Content-Type": "application/json" },
    body: JSON.stringify(["LRANGE", "leads", "0", "-1"]),
  });
  if (!r.ok) return res.status(502).json({ error: "storage_error" });
  const rows = ((await r.json()).result || []).map((t) => { try { return JSON.parse(t); } catch (e) { return null; } })
    .filter(Boolean);

  if (req.query && req.query.format === "csv") {
    const esc = (v) => `"${String(v == null ? "" : v).replace(/"/g, '""')}"`;
    const csv = [COLS.join(","), ...rows.map((row) => COLS.map((c) => esc(row[c])).join(","))].join("\n");
    res.setHeader("Content-Type", "text/csv; charset=utf-8");
    res.setHeader("Content-Disposition", 'attachment; filename="casa-patio-early-list.csv"');
    return res.status(200).send(csv);
  }
  return res.status(200).json({ count: rows.length, leads: rows });
};
