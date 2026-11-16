# Casa Pátio early-list landing page

A one-page site for running Instagram, Facebook and X ads and collecting sign-ups.

- `page.html`: the page (edit copy here).
- `config.json`: your domain, ad pixel IDs and an optional form endpoint.
- `build.py`: builds the deployable site into `site/`.
- `site/`: **the folder you put online.**

Rebuild after any edit:

```bash
python3 casa01/landing/build.py
```

## 1. Put it online (about 10 minutes, free)

The easiest host is **Netlify**, because it collects form sign-ups with no extra setup.

1. Create a free account at netlify.com.
2. Open app.netlify.com/drop and drag the `casa01/landing/site` folder onto the page.
3. In the new site's settings, open **Forms** and turn on **form detection**, then deploy again (drag the folder once more).
4. Under **Forms → Form notifications**, add your email so every sign-up is emailed to you.
5. Sign-ups appear under **Forms → early-list**, with a CSV export.

The free tier covers 100 sign-ups a month, plenty for an interest test.

**Own domain (recommended for ads):** buy one (for example casapatio.com or similar) and connect it under **Domain management**. Then put it in `config.json` as `"site_url": "https://yourdomain.com"` and rebuild, so link previews on Instagram and X show the house image.

**Other hosts:** to host anywhere else, create a free form at formspree.io and put its URL in `"form_endpoint"`.

## 2. Add ad tracking (optional, before you spend)

- **Meta (Instagram/Facebook):** in Events Manager create a Pixel, then put its ID in `"meta_pixel_id"`. The page sends `PageView` on load and `Lead` on each sign-up.
- **X:** create a pixel and a "Lead" conversion event, then put the pixel ID in `"x_pixel_id"` and the event ID in `"x_lead_event_id"`.

Rebuild and redeploy after changing `config.json`.

## 3. Tag every ad link

Every sign-up records which ad it came from. Use links like:

```
https://yourdomain.com/?utm_source=instagram&utm_campaign=test1&utm_content=dusk-video&v=a
https://yourdomain.com/?utm_source=x&utm_campaign=test1&utm_content=courtyard&v=b
```

- `utm_source`: instagram, facebook, x, pinterest
- `utm_content`: which creative (street, dusk, courtyard, 360 video)
- `v=a`: headline "A Brazilian courtyard house, built on your Austin lot."
- `v=b`: headline "Your own private courtyard, in the middle of Austin."

## 4. A simple two-week test

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
- **Quality:** the share of sign-ups that own land or a home ("What fits you best?") and pick a budget of $500K+.
- **Winners:** which headline (`variant`) and which creative (`utm_content`) bring the most qualified sign-ups.

**A strong result:** 10–20 sign-ups from people who own land, from about $500 of ads. Book calls with them and offer the Lot Fit Study.
