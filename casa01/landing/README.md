# Casa Pátio website (Vercel)

Every push to GitHub rebuilds the site. `scripts/vercel-build.sh` assembles it from this repo:

| Address | What it is | Source |
|---|---|---|
| `/` | Landing page with the early-list form | `casa01/landing/page.html` → `site/` |
| `/house` | Interactive house: live 3D model with sun slider, 360° tour, renders, finishes | `casa01/lookbook/web/house.html` + assets |
| `/homes/` | The homes: Single (Casa 01), Duo and Trio, with photos, site layouts, floor plans and the material board | `phase2/web/build.py` → `phase2/web/site/` |
| `/Casa01_Lookbook.pdf` | The latest 21-page lookbook | `casa01/Casa01_Lookbook.pdf` |
| `/Phase2_Lookbook.pdf` | The duo + trio lookbook (Casa 02 + Casita) | `phase2/Phase2_Lookbook.pdf` |
| `/leads` | **Private** list of sign-ups, with counts by ad and headline | `casa01/landing/leads.html` |
| `/api/lead`, `/api/leads` | Save a sign-up / read them (serverless functions) | `api/` |

After editing the landing page, rebuild it and push:

```bash
python3 casa01/landing/build.py
```

After changing the Phase 2 model or renders, rebuild the homes page the same way:

```bash
python3 phase2/web/build.py
```

## One-time Vercel setup (about 5 minutes)

1. **Show every push on the main address.** In the Vercel project, open **Settings → Git → Production Branch** and enter `claude/compassionate-keller-mtj4mo`. If you skip this, pushes only make preview links.
2. **Somewhere to keep sign-ups.** Open **Storage → Create Database → Upstash for Redis** (free plan) and connect it to this project. Vercel adds the connection settings automatically.
3. **Your private key for `/leads`.** Open **Settings → Environment Variables** and add `ADMIN_KEY` with a long password only you know.
4. **Optional email per sign-up.** Make a free resend.com account, then add `RESEND_API_KEY` and `NOTIFY_EMAIL` (your address).
5. **Redeploy** (Deployments → latest → Redeploy) so the new settings take effect.
6. **Test it.** Fill in the form on your site, then open `/leads`, enter your key, and you should see the test sign-up.

Until step 2 is done, the form shows "That didn't go through". Don't start ads before then.

**Link previews:** once you know the final address (for example `https://brazilian-modern-homes.vercel.app` or your own domain), put it in `config.json` as `site_url`, run the build above and push. Instagram and X then show the house image when the link is shared.

**Own domain:** buy one and add it under **Settings → Domains**.

## Ad tracking (optional, before you spend)

- **Meta (Instagram/Facebook):** create a Pixel in Events Manager, then put its ID in `config.json` → `meta_pixel_id`. The page sends `PageView` on load and `Lead` on each sign-up.
- **X:** create a pixel and a "Lead" conversion event, then put the IDs in `x_pixel_id` and `x_lead_event_id`.

Rebuild and push after changing `config.json`.

## Tag every ad link

Each sign-up records which ad it came from. `/leads` counts them by source and headline:

```
https://YOUR-SITE/?utm_source=instagram&utm_campaign=test1&utm_content=dusk&v=a
https://YOUR-SITE/?utm_source=x&utm_campaign=test1&utm_content=courtyard&v=b
```

- `v=a`: headline "A Brazilian courtyard house, built on your Austin lot."
- `v=b`: headline "Your own private courtyard, in the middle of Austin."

## A simple two-week test

| | |
|---|---|
| Budget | $300–$600 total, about $20–40 a day |
| Where | Instagram + Facebook (Meta Ads); a small X test if you like |
| Area | Austin and nearby Hill Country, 15+ mile radius |
| Creatives | street render, dusk render, courtyard, a 10–15 s 360 screen recording |
| Angles | `v=a` "on your lot" vs `v=b` "private courtyard" |

**Housing ads rule:** Meta treats home-building ads as a **Special Ad Category: Housing**. Declare it when you create the campaign. It limits targeting (no age, gender or ZIP targeting, and a 15-mile minimum radius), but it's required.

**What to watch:**
- **Cost per sign-up:** under about $30–40 is a good signal for a $500K+ product.
- **Quality:** the share of sign-ups that own land or a home ("What fits you best?").
- **Winners:** which headline and creative bring the most qualified sign-ups.

**A strong result:** 10–20 sign-ups from people who own land, from about $500 of ads.

*Netlify instead of Vercel:* drag `casa01/landing/site` onto app.netlify.com/drop, turn on Forms, and set `form_endpoint` to `""` in `config.json`.
