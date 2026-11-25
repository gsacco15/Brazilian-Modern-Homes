"""Build the /homes/ page: Single (Casa 01), Duo and Trio, each with its photos, site layouts and floor plans,
and one material board shared by all three.

    python3 phase2/web/build.py   ->  phase2/web/site/   (scripts/vercel-build.sh serves it at /homes/)

Everything comes from the model and the renders, so rebuilding after a design change keeps the page in step:
site plans and floor plans are drawn by phase2/concepts/concepts.py, layout facts come from model/sites.py,
the material board from model/finishes.py. Casa 01 photos reuse the landing page's images at /img/.
"""
import html
import json
import os
import re
import shutil
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
sys.path.insert(0, P2)
sys.path.insert(0, os.path.join(P2, "concepts"))

import concepts as C  # noqa: E402
from model import homes as H, sites as S  # noqa: E402
from model.finishes import EXTERIOR, INTERIOR  # noqa: E402

SITE = os.path.join(HERE, "site")
IMG = os.path.join(SITE, "img")
URL = "/homes/img/"          # this page's images
C01 = "/img/"                # the landing page's Casa 01 images (street-1600.jpg, street-800.jpg, ...)
CASA01 = os.path.join(ROOT, "casa01")
RENDER_DIRS = [os.path.join(P2, "render", d) for d in ("final", "hifi_v2", "hifi")]
SWATCHES = os.path.join(CASA01, "renders", "swatches")

esc = html.escape
SITE_URL = json.load(open(os.path.join(CASA01, "landing", "config.json"))).get("site_url", "").rstrip("/")


# ---------------------------------------------------------------- content
C01_GAL = [
    ("street", "From the street: limestone, a cedar gate and the cobogó screen."),
    ("street_dusk", "At dusk the cobogó glows like a lantern."),
    ("gate", "Through the gate, the pátio opens to the right."),
    ("entry", "Covered entry: black calçada underfoot, the cobogó beside you."),
    ("courtyard", "The pátio under a live oak. Every room opens onto it."),
    ("interior", "The great room, under a cedar ceiling."),
    ("kitchen", "Kitchen with honed black granite and green tile."),
    ("bath", "Primary bath: green tile, a curbless shower, a skylight overhead."),
    ("bath2", "Hall bath: terracotta tile around the tub."),
    ("veranda", "The veranda faces the backyard oak."),
]

P2_CAPTIONS = {
    "duo_street": "The pair from the street: limestone corners, cedar carport gates, one cobogó lantern between the doors.",
    "duo_dusk": "At dusk the stair light turns the cobogó into a lantern.",
    "duo_entry": "Each front door sits under the cobogó, on a black calçada threshold.",
    "duo_garden": "Evening at the back: each home opens to its own pátio under a cedar sunshade.",
    "kitchen": "Kitchen: rift oak, green tile, a granite island with an oak table built on.",
    "primary_bath": "Primary bath: from the green-tiled shower to the oak vanity, the round brass mirror and sconces.",
    "upper_hall": "Upstairs: a skylight over the stair, a cedar ceiling, and a desk on the landing behind the cobogó.",
    "trio_street": "On an alley lot the Casita faces the street behind its walled garden; the pair sits back.",
    "side_drive": "One drive serves all three homes. A cobogó screen closes the front garden from the street.",
    "side_drive_night": "At night, lights set into the walk and the walls lead to each front door, and the screen glows.",
    "trio_aerial": "From above: the pair at the street, the Casita behind with its own garden.",
}

PLANS = {
    "GC": (H.CASA02_GF_CARPORT, "Ground floor, carport", "570 sf + carport",
           "Kitchen, dining and living in one long room that opens to the pátio. Powder room by the front "
           "door, carport behind a cedar gate."),
    "GS": (H.CASA02_GF_SUITE, "Ground floor, suite", "780 sf",
           "The carport becomes a bedroom suite with its own bath, for lots that park on a pad. "
           "3 bed + den, 3.5 bath, 1,560 sf in all."),
    "GD": (H.CASA02_GF_SIDE, "Ground floor, side drive", "570 sf + carport",
           "For lots with a shared drive. The front door opens off the drive under a cedar canopy, the car "
           "turns in from the side, and the street sees a limestone wall."),
    "UP": (H.CASA02_UPPER, "Upper floor", "780 sf",
           "Primary suite with a walk-in and a skylit shower, two more bedrooms, a second bath and the laundry."),
    "CS": (H.CASITA, "Casita", "640 sf",
           "One story: living and kitchen, a flex room, a bedroom and bath, and a covered porch on its own garden."),
}

LAYOUT_LABEL = {
    "L1-D1": ("Side by side", "50 × 125 ft lot"),
    "L4-D2": ("Front and back", "65 × 125 ft lot"),
    "L1-T1": ("Casita behind", "50 × 125 ft lot"),
    "L2-T2": ("Casita at the street", "50 × 125 ft, with alley"),
    "L3-T1": ("Corner lot", "60 × 125 ft corner"),
    "L4-T1": ("Shared side drive", "65 × 125 ft lot"),
}

OPTIONS = [
    dict(id="single", name="Single", sub="1 home", title="Casa 01, the courtyard house",
         lede="One story wrapped around a pátio and its live oak. Every room opens onto it.",
         facts=[("1", "home"), ("1,670", "sq ft"), ("3 / 2", "bed / bath"), ("65 ft", "typical lot width")],
         gallery=[("c01", k, cap) for k, cap in C01_GAL],
         layouts=["C01"], plans=["C01"]),
    dict(id="duo", name="Duo", sub="2 homes", title="Casa 02, a pair on one lot",
         lede="Two two-story homes that share one wall. Each has its own front door, carport and pátio.",
         facts=[("2", "homes"), ("1,350–1,560", "sq ft each"), ("3 / 2.5", "bed / bath each"),
                ("50–65 ft", "lot width")],
         gallery=[("p2", k, P2_CAPTIONS[k]) for k in
                  ("duo_street", "duo_dusk", "duo_entry", "duo_garden", "kitchen", "primary_bath", "upper_hall")],
         layouts=["L1-D1", "L4-D2"], plans=["GC", "UP", "GS"]),
    dict(id="trio", name="Trio", sub="3 homes", title="The pair plus a Casita",
         lede="The Casa 02 pair plus a one-story Casita on the same lot. Three front doors, three gardens.",
         facts=[("3", "homes"), ("3,340", "sq ft in all"), ("3 + 3 + 1", "bedrooms"), ("50–65 ft", "lot width")],
         gallery=[("p2", k, P2_CAPTIONS[k]) for k in
                  ("side_drive", "side_drive_night", "trio_street", "trio_aerial", "duo_garden", "kitchen",
                   "primary_bath")],
         layouts=["L4-T1", "L1-T1", "L2-T2", "L3-T1"], plans=["GD", "UP", "CS", "GC"]),
]

C01_LAYOUT = dict(
    label=("On its own lot", "65 × 125 ft lot"), name="On its own lot",
    facts=[("Homes", "Casa 01, 3 bed / 2 bath"), ("Floor area", "1,670 sf"), ("Parking", "Carport")],
    notes="The house wraps the pátio, and the backyard oak stays.",
)

C01_PLAN = ("Floor plan", "1,670 sf",
            "Great room, kitchen and primary suite across the back; two bedrooms along the gallery; carport "
            "and covered entry at the street.")


# ---------------------------------------------------------------- images
def jpg(src, dst, width, quality=80):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, quality=quality, optimize=True, progressive=True)


def render_src(key):
    for d in RENDER_DIRS:
        p = os.path.join(d, f"{key}.png")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(key)


def brass_swatch(path, n=600):
    """Brushed brass: streaks along x, a soft diagonal sheen."""
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (n, n * 2))
    k = 90
    c = np.cumsum(noise, axis=1)
    streak = (c[:, k:] - c[:, :-k])[:, :n] / np.sqrt(k)
    streak = streak / np.abs(streak).max()
    yy, xx = np.mgrid[0:n, 0:n] / n
    sheen = 0.5 + 0.5 * np.cos((xx * 0.8 + yy * 1.2) * np.pi * 1.1)
    base = np.array([176, 140, 74], float)
    hi = np.array([226, 196, 128], float)
    col = base[None, None] + (hi - base)[None, None] * (0.25 + 0.55 * sheen)[..., None]
    col = col * (1 + 0.07 * streak)[..., None]
    Image.fromarray(np.clip(col, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6)).save(path, quality=86)


def swatch_images():
    for m in EXTERIOR + INTERIOR:
        dst = os.path.join(IMG, f"sw_{m['key']}.jpg")
        if m["key"] == "brass":
            brass_swatch(dst)
        elif m["key"] in ("tile", "zellige_terracotta"):
            im = Image.open(os.path.join(SWATCHES, "tile.png")).convert("RGB")
            w, h = im.size
            x0 = 0 if m["key"] == "tile" else w // 2 + 4
            half = im.crop((x0, 0, x0 + w // 2 - 4, h))
            hw = half.width
            half.crop((0, (h - hw) // 2, hw, (h + hw) // 2)).resize((600, 600), Image.LANCZOS).save(dst, quality=86)
        else:
            jpg(os.path.join(SWATCHES, f"{m['key']}.png"), dst, 600, 86)


def images():
    os.makedirs(IMG, exist_ok=True)
    keys = sorted({k for o in OPTIONS for src, k, _ in o["gallery"] if src == "p2"})
    for k in keys:
        try:
            src = render_src(k)
        except FileNotFoundError:
            print("  missing render, left out:", k)
            for o in OPTIONS:
                o["gallery"] = [g for g in o["gallery"] if not (g[0] == "p2" and g[1] == k)]
            continue
        for w in (1600, 800, 400):
            jpg(src, os.path.join(IMG, f"{k}-{w}.jpg"), w, 80 if w > 400 else 74)
    for k, _ in C01_GAL:                                  # small thumbs only: the landing has 800 and 1600
        jpg(os.path.join(CASA01, "renders", f"{k}.png"), os.path.join(IMG, f"c01_{k}-400.jpg"), 400, 74)
    for f in S.SITES:
        s = f()
        air = os.path.join(P2, "render", "final", f"air_{s['id']}.png")      # high-detail aerial, else the massing view
        src = air if os.path.exists(air) else os.path.join(P2, "render", "out", f"{s['id']}_aerial.png")
        jpg(src, os.path.join(IMG, f"mass_{s['id']}.jpg"), 1100, 80)
    jpg(os.path.join(CASA01, "renders", "aerial.png"), os.path.join(IMG, "mass_C01.jpg"), 900, 78)
    swatch_images()
    # drawings
    for k, (plan, *_rest) in PLANS.items():
        open(os.path.join(IMG, f"plan_{k}.svg"), "w").write(C.plan_svg(plan, note_front="FRONT"))
    for f in S.SITES:
        s = f()
        open(os.path.join(IMG, f"site_{s['id']}.svg"), "w").write(C.site_svg(s))
    shutil.copy(os.path.join(CASA01, "drawings", "02_floor_plan.svg"), os.path.join(IMG, "plan_C01.svg"))
    shutil.copy(os.path.join(CASA01, "drawings", "01_site_plan.svg"), os.path.join(IMG, "site_C01.svg"))


# ---------------------------------------------------------------- html parts
def gal_src(src, k, w):
    if src == "c01":
        return f"{URL}c01_{k}-400.jpg" if w == 400 else f"{C01}{k}-{w}.jpg"
    return f"{URL}{k}-{w}.jpg"


def gallery_html(o):
    items = o["gallery"]
    src, k, cap = items[0]
    data = [{"s": gal_src(s, kk, 800), "l": gal_src(s, kk, 1600), "c": c} for s, kk, c in items]
    thumbs = "".join(
        f'<button class="th" type="button" data-i="{i}" aria-label="Photo {i + 1}: {esc(c)}"'
        f'{" aria-current=\"true\"" if i == 0 else ""}><img src="{gal_src(s, kk, 400)}" alt="" loading="lazy"></button>'
        for i, (s, kk, c) in enumerate(items))
    return f'''<div class="viewer" data-gal='{esc(json.dumps(data, ensure_ascii=False))}'>
  <figure class="stage">
    <button class="frame" type="button" aria-label="Open larger">
      <img class="main" src="{gal_src(src, k, 1600)}" srcset="{gal_src(src, k, 800)} 800w, {gal_src(src, k, 1600)} 1600w"
        sizes="(min-width:1152px) 1120px, 100vw" alt="{esc(cap)}" loading="lazy">
    </button>
    <figcaption><span class="cap">{esc(cap)}</span>
      <span class="nav"><button class="arrow prev" type="button" aria-label="Previous photo">←</button>
      <span class="count">1 / {len(items)}</span>
      <button class="arrow next" type="button" aria-label="Next photo">→</button></span></figcaption>
  </figure>
  <div class="thumbs">{thumbs}</div>
</div>'''


def chips(group, items, current=0):
    """items: (key, label, sublabel)"""
    if len(items) < 2:
        return ""
    return (f'<div class="chips" role="group" aria-label="{esc(group)}">' + "".join(
        f'<button class="chip" type="button" data-k="{esc(k)}" aria-pressed="{"true" if i == current else "false"}">'
        f'<b>{esc(a)}</b><span>{esc(b)}</span></button>' for i, (k, a, b) in enumerate(items)) + "</div>")


def fmt(n):
    return f"{n:,.0f}"


LAYOUT_DESC = {
    "L1-D1": "Side by side, each with its own carport at the street.",
    "L4-D2": "One behind the other on a shared drive. Each ground floor gains a bedroom suite.",
    "L1-T1": "The pair at the street, the Casita in the back garden.",
    "L2-T2": "The Casita faces the street. The pair sits back and parks off the alley.",
    "L3-T1": "The Casita faces the side street, with its own parking.",
    "L4-T1": "One shared drive with a lit walk to all three front doors. Cobogó screens give each garden privacy.",
}


def layout_html(lid, first=False):
    air = os.path.exists(os.path.join(P2, "render", "final", f"air_{lid}.png"))
    if lid == "C01":
        L = C01_LAYOUT
        title, lot_s, facts, desc = L["name"], L["label"][1], L["facts"], L["notes"]
        mass_cap = "From above"
    else:
        s = next(f() for f in S.SITES if f()["id"] == lid)
        c = S.check_site(s)
        kinds = {}
        for h in s["homes"]:
            kinds.setdefault(h["kind"], []).append(h["beds"])
        homes_s = "; ".join(f"{len(v)} × {k} ({v[0]})" if len(v) > 1 else f"{k} ({v[0]})" for k, v in kinds.items())
        title, lot_s = LAYOUT_LABEL[lid]
        facts = [("Homes", homes_s), ("Floor area", f"{fmt(c['fa'])} sf in all"), ("Parking", f"{c['parking']} on site")]
        desc = LAYOUT_DESC[lid]
        mass_cap = "From above" if air else "Massing view"
    kv = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in facts)
    return f'''<div class="pane lay" data-k="{lid}"{'' if first else ' hidden'}>
  <a class="sheet site" href="{URL}site_{lid}.svg" target="_blank" rel="noopener" title="Open the drawing full size"><img src="{URL}site_{lid}.svg" alt="Site plan: {esc(title)}" loading="lazy"></a>
  <div class="info">
    <div class="eyebrow">{esc(lot_s)}</div>
    <h3>{esc(title)}</h3>
    <p>{esc(desc)}</p>
    <dl class="kv">{kv}</dl>
    <figure class="mass"><img src="{URL}mass_{lid}.jpg" alt="{esc(mass_cap)}: {esc(title)}" loading="lazy"><figcaption>{esc(mass_cap)}</figcaption></figure>
  </div>
</div>'''


def plan_html(pk, first):
    if pk == "C01":
        name, area, desc = C01_PLAN
    else:
        plan, name, area, desc = PLANS[pk]
    return f'''<div class="pane pl" data-k="{pk}"{'' if first else ' hidden'}>
  <a class="sheet plan" href="{URL}plan_{pk}.svg" target="_blank" rel="noopener" title="Open the drawing full size"><img src="{URL}plan_{pk}.svg" alt="Floor plan: {esc(name)}" loading="lazy"></a>
  <div class="info">
    <div class="eyebrow">{esc(area)}</div>
    <h3>{esc(name)}</h3>
    <p>{esc(desc)}</p>
  </div>
</div>'''


def option_html(o, first):
    oid = o["id"]
    facts = "".join(f"<div><b>{esc(a)}</b><span>{esc(b)}</span></div>" for a, b in o["facts"])
    if o["layouts"] == ["C01"]:
        lay_items = []
    else:
        lay_items = [(lid, *LAYOUT_LABEL[lid]) for lid in o["layouts"]]
    plan_items = [(pk, PLANS[pk][1] if pk != "C01" else C01_PLAN[0], PLANS[pk][2] if pk != "C01" else C01_PLAN[1])
                  for pk in o["plans"]]
    lays = "".join(layout_html(lid, i == 0) for i, lid in enumerate(o["layouts"]))
    plans = "".join(plan_html(pk, i == 0) for i, pk in enumerate(o["plans"]))
    lay_head = "On the lot" if oid == "single" else "Site layouts"
    return f'''<section class="opt" id="p-{oid}" role="tabpanel" aria-labelledby="t-{oid}"{'' if first else ' hidden'}>
  <div class="band photos" data-sec="photos" id="{oid}-photos">
    <div class="wrap">
      <div class="opt-head">
        <div><div class="eyebrow">{esc(o['name'])} · {esc(o['sub'])}</div><h2>{esc(o['title'])}</h2></div>
        <p class="lede">{esc(o['lede'])}</p>
      </div>
      <div class="facts">{facts}</div>
      {gallery_html(o)}
    </div>
  </div>
  <div class="band soft" data-sec="layouts" id="{oid}-layouts">
    <div class="wrap">
      <div class="sec-head"><div class="eyebrow">Site</div><h2>{lay_head}</h2></div>
      {chips("Layouts", lay_items)}
      <div class="panes">{lays}</div>
    </div>
  </div>
  <div class="band" data-sec="plans" id="{oid}-plans">
    <div class="wrap">
      <div class="sec-head"><div class="eyebrow">Plans</div><h2>Floor plans</h2></div>
      {chips("Floors", plan_items)}
      <div class="panes">{plans}</div>
    </div>
  </div>
</section>'''


def board_html():
    groups = [("Outside", EXTERIOR), ("Inside", INTERIOR)]
    tiles = ""
    for g, items in groups:
        for m in items:
            d = {k: m[k] for k in ("name", "ref", "spec", "where")}
            d["g"] = g
            tiles += (f'<button class="tile" type="button" data-g="{g}" data-m=\'{esc(json.dumps(d, ensure_ascii=False))}\' '
                      f'data-img="{URL}sw_{m["key"]}.jpg" aria-pressed="{"true" if m["key"] == "limestone" else "false"}">'
                      f'<span class="sw"><img src="{URL}sw_{m["key"]}.jpg" alt="" loading="lazy"></span>'
                      f'<span class="tn">{esc(m["name"])}</span></button>')
    first = next(m for m in EXTERIOR if m["key"] == "limestone")
    return f'''<section class="band board" id="materials" aria-labelledby="h-mat">
  <div class="wrap">
    <div class="sec-head"><div class="eyebrow">One palette</div><h2 id="h-mat">The material board</h2>
      <p class="lede">Fourteen materials, used in every home. Tap one to see where it goes.</p></div>
    <div class="mb">
      <div class="detail" aria-live="polite">
        <div class="big"><img id="mbImg" src="{URL}sw_limestone.jpg" alt=""></div>
        <div class="txt">
          <div class="eyebrow" id="mbG">Outside</div>
          <h3 id="mbName">{esc(first['name'])}</h3>
          <p class="ref">Brazilian reference: <i id="mbRef">{esc(first['ref'])}</i></p>
          <p id="mbSpec">{esc(first['spec'])}</p>
          <p class="where"><b>Where</b> <span id="mbWhere">{esc(first['where'])}</span></p>
        </div>
      </div>
      <div class="grid-wrap">
        <div class="chips mini" role="group" aria-label="Filter materials">
          <button class="chip" type="button" data-f="all" aria-pressed="true"><b>All</b></button>
          <button class="chip" type="button" data-f="Outside" aria-pressed="false"><b>Outside</b></button>
          <button class="chip" type="button" data-f="Inside" aria-pressed="false"><b>Inside</b></button>
        </div>
        <div class="tiles">{tiles}</div>
      </div>
    </div>
  </div>
</section>'''


CSS = r"""
:root{
  --paper:#f5f2ea; --card:#fffdf7; --ink:#1d2520; --muted:#5b625b; --line:#dcd6c8; --soft:#ece7db;
  --forest:#1d2520; --on-forest:#ece6d8; --on-forest-muted:#b7b9ab;
  --gold:#94712f; --gold-hi:#d2b47c; --sage:#5f7458;
  --serif:"Cormorant Garamond",Georgia,"Times New Roman",serif;
  --sans:"Lato","Helvetica Neue",Arial,sans-serif;
  color-scheme:light;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:76px}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.6;margin:0;-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:11;background:var(--forest)}
img{max-width:100%}
[hidden]{display:none!important}
.wrap{max-width:1120px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.band{padding-block:clamp(44px,6vw,80px)}
.band.soft{background:var(--soft)}
.band.dark{background:var(--forest);color:var(--on-forest)}
h1,h2,h3{font-family:var(--serif);font-weight:500;text-wrap:balance;margin:0;font-variant-numeric:lining-nums}
h1{font-size:clamp(40px,6vw,68px);line-height:1}
h2{font-size:clamp(30px,4vw,46px);line-height:1.05}
h3{font-size:28px;line-height:1.1}
p{margin:0}
a{color:inherit}
:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
.eyebrow{font-size:12px;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)}
.dark .eyebrow{color:var(--gold-hi)}
.lede{font-size:clamp(16px,1.7vw,19px);max-width:60ch;color:var(--muted)}
.dark .lede{color:var(--on-forest-muted)}
button{font:inherit;color:inherit}

/* top */
.top{background:var(--forest);color:var(--on-forest)}
.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;min-height:60px}
.bar a{text-decoration:none;font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.bar .brand{font-family:var(--serif);font-size:21px;font-weight:500;letter-spacing:0;text-transform:none}
.bar .links{display:flex;gap:20px;align-items:center}
.bar .links a:hover{color:var(--gold-hi)}
.bar .pill{border:1px solid rgba(236,230,216,.75);padding:9px 13px}
@media (max-width:640px){.bar .lg{display:none}.bar .brand{font-size:17px}.bar .links{gap:14px}}
.hello{padding-block:clamp(36px,6vw,72px) clamp(28px,4vw,48px)}
.hello .lede{margin-top:14px;color:var(--on-forest-muted)}
.hello .eyebrow{color:var(--gold-hi)}

/* the Single / Duo / Trio picker */
.picker{position:sticky;top:env(safe-area-inset-top,0px);z-index:10;background:rgba(245,242,234,.94);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line)}
.picker .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:68px}
.seg{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line);background:var(--card);padding:3px;gap:3px;flex:0 1 480px}
.seg button{border:0;background:transparent;cursor:pointer;padding:8px 10px;display:grid;gap:1px;text-align:center;border-radius:1px;
  transition:background .25s,color .25s}
.seg b{font-family:var(--serif);font-size:22px;font-weight:500;line-height:1}
.seg span{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);transition:color .25s}
.seg button:hover{background:#f1ece0}
.seg button[aria-selected="true"]{background:var(--forest);color:var(--on-forest)}
.seg button[aria-selected="true"] span{color:var(--gold-hi)}
.jump{display:flex;gap:22px}
.jump a{font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;color:var(--muted)}
.jump a:hover{color:var(--ink)}
@media (max-width:860px){.jump{display:none}.seg{flex:1 1 auto}}

/* option header + facts */
.opt-head{display:grid;gap:14px;align-items:end}
@media (min-width:900px){.opt-head{grid-template-columns:1fr 1fr;gap:40px}}
.facts{display:grid;grid-template-columns:repeat(2,1fr);gap:14px 24px;margin:26px 0 22px;padding-block:16px;border-block:1px solid var(--line)}
@media (min-width:700px){.facts{grid-template-columns:repeat(4,1fr)}}
.facts div{display:grid;gap:2px}
.facts b{font-family:var(--serif);font-size:32px;font-weight:500;line-height:1;font-variant-numeric:lining-nums tabular-nums}
.facts span{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.opt{animation:fade .45s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* photo viewer */
.stage{margin:0}
.frame{display:block;width:100%;padding:0;border:0;background:#2a332d;cursor:zoom-in;overflow:hidden;touch-action:pan-y}
.frame img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;transition:opacity .35s ease}
.frame img.out{opacity:.15}
.stage figcaption{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-top:12px;min-height:48px}
.cap{color:var(--muted);font-size:15px}
.nav{display:flex;align-items:center;gap:6px;flex:none}
.count{font-size:12px;letter-spacing:.12em;color:var(--muted);min-width:46px;text-align:center;font-variant-numeric:tabular-nums}
.arrow{width:40px;height:40px;border:1px solid var(--line);background:var(--card);cursor:pointer;font-size:16px;border-radius:2px}
.arrow:hover{border-color:var(--ink)}
.thumbs{display:grid;grid-auto-flow:column;grid-auto-columns:104px;gap:8px;overflow-x:auto;padding:6px 0 4px;scrollbar-width:thin}
.th{padding:0;border:0;background:none;cursor:pointer;opacity:.62;transition:opacity .25s;position:relative}
.th img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover}
.th::after{content:"";position:absolute;left:0;right:0;bottom:-4px;height:2px;background:transparent;transition:background .25s}
.th:hover{opacity:.9}
.th[aria-current="true"]{opacity:1}
.th[aria-current="true"]::after{background:var(--gold)}

/* section heads + chips */
.sec-head{display:grid;gap:10px;margin-bottom:22px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chip{display:grid;gap:0;text-align:left;min-height:44px;padding:8px 14px;border:1px solid var(--line);background:var(--card);cursor:pointer;border-radius:2px;
  transition:background .2s,border-color .2s,color .2s}
.chip b{font-size:13px;font-weight:700;letter-spacing:.02em}
.chip span{font-size:11.5px;color:var(--muted)}
.chip:hover{border-color:#b9b09c}
.chip[aria-pressed="true"]{background:var(--forest);border-color:var(--forest);color:var(--on-forest)}
.chip[aria-pressed="true"] span{color:var(--on-forest-muted)}
.chips.mini .chip{min-height:36px;padding:6px 14px}

/* layouts and plans: drawing + info */
.pane{display:grid;gap:24px;align-items:start;animation:fade .4s ease}
@media (min-width:900px){.pane{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:40px}}
.sheet{background:#fff;border:1px solid var(--line);padding:clamp(10px,2vw,22px);display:flex;justify-content:center;cursor:zoom-in;transition:border-color .25s}
.sheet:hover{border-color:#b9b09c}
.sheet img{display:block;width:auto;max-width:100%;height:auto;max-height:min(78vh,820px)}
.sheet.plan img{max-height:min(74vh,760px)}
.info{display:grid;gap:14px;align-content:start}
.info p{color:var(--muted)}
.kv{display:grid;margin:4px 0 0;border-top:1px solid var(--line)}
.kv div{display:grid;grid-template-columns:110px 1fr;gap:12px;padding:8px 0;border-bottom:1px solid var(--line)}
.kv dt{font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding-top:3px}
.kv dd{margin:0;font-size:15px}
.notes{margin:4px 0 0;padding-left:18px;color:var(--muted);display:grid;gap:6px;font-size:15px}
.mass{margin:6px 0 0}
.mass img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid var(--line)}
.mass figcaption{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding-top:6px}

/* material board */
.board{background:var(--card);border-top:1px solid var(--line)}
.mb{display:grid;gap:28px}
@media (min-width:900px){.mb{grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:48px;align-items:start}
  .detail{position:sticky;top:96px}}
.detail{display:grid;gap:18px}
.big{overflow:hidden;aspect-ratio:4/3;background:var(--soft)}
.big img{display:block;width:100%;height:100%;object-fit:cover;transform:scale(1.02);transition:opacity .35s ease,transform 6s ease}
.big img.out{opacity:0}
.big:hover img{transform:scale(1.1)}
.txt{display:grid;gap:8px}
.txt h3{font-size:34px}
.txt .ref{font-size:15px;color:var(--muted)}
.txt .ref i{font-family:var(--serif);font-size:19px;color:var(--ink)}
.txt p{color:var(--muted)}
.txt .where b{font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;color:var(--ink);margin-right:6px}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:14px 12px}
@media (min-width:560px){.tiles{grid-template-columns:repeat(4,1fr)}}
.tile{padding:0;border:0;background:none;cursor:pointer;display:grid;gap:7px;text-align:left;align-content:start}
.tile .sw{display:block;overflow:hidden;aspect-ratio:1;outline:1px solid transparent;outline-offset:3px;transition:outline-color .25s}
.tile img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .6s ease}
.tile:hover img{transform:scale(1.08)}
.tile .tn{font-size:12.5px;line-height:1.3;color:var(--muted);transition:color .25s}
.tile:hover .tn{color:var(--ink)}
.tile[aria-pressed="true"] .sw{outline-color:var(--gold)}
.tile[aria-pressed="true"] .tn{color:var(--ink);font-weight:700}

/* closing */
.end .cta-row{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:50px;padding:0 22px;border-radius:2px;border:1px solid transparent;
  font:900 13px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;text-decoration:none;cursor:pointer;transition:background .2s}
.btn.primary{background:var(--gold-hi);color:var(--forest)}
.btn.primary:hover{background:#e2c690}
.btn.ghost{border-color:currentColor;background:transparent}
.btn.ghost:hover{background:rgba(236,230,216,.12)}
footer{background:var(--forest);color:var(--on-forest-muted);font-size:14px;padding-block:52px 28px;border-top:1px solid rgba(236,230,216,.12)}
.foot{display:grid;gap:30px 24px;grid-template-columns:1fr 1fr}
.f-brand{grid-column:1/-1}
@media (min-width:800px){.foot{grid-template-columns:1.6fr 1fr 1fr 1fr}.f-brand{grid-column:auto}}
.f-brand a{font-family:var(--serif);font-size:26px;color:var(--on-forest);text-decoration:none;line-height:1.1}
.f-brand p{margin-top:8px;font-family:var(--serif);font-style:italic;font-size:18px;color:var(--gold-hi)}
.f-col{display:grid;gap:9px;align-content:start}
.f-col b{color:var(--on-forest);font-weight:900;letter-spacing:.16em;text-transform:uppercase;font-size:11px;margin-bottom:4px}
.f-col a{text-decoration:none;color:var(--on-forest-muted);transition:color .2s}
.f-col a:hover{color:var(--gold-hi)}
.f-base{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 24px;margin-top:40px;padding-top:18px;
  border-top:1px solid rgba(236,230,216,.14);font-size:12.5px}

/* lightbox */
dialog.lb{padding:0;border:0;background:transparent;max-width:min(96vw,1600px);width:100%}
dialog.lb::backdrop{background:rgba(16,20,18,.92)}
.lb img{display:block;width:100%;max-height:86vh;object-fit:contain}
.lb .bar2{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:10px;color:var(--on-forest)}
.lb .bar2 p{font-size:14px;color:var(--on-forest-muted)}
.lb .arrow{background:transparent;color:var(--on-forest);border-color:rgba(236,230,216,.4)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
  var ids=['single','duo','trio'];
  var tabs=ids.map(function(i){return document.getElementById('t-'+i)});
  var jump=document.querySelectorAll('.jump a');
  function pick(id,focus){
    if(ids.indexOf(id)<0) id='single';
    ids.forEach(function(i,n){
      var on=i===id;
      tabs[n].setAttribute('aria-selected',on);tabs[n].tabIndex=on?0:-1;
      document.getElementById('p-'+i).hidden=!on;
    });
    jump.forEach(function(a){a.href='#'+id+'-'+a.dataset.s});
    if(focus) tabs[ids.indexOf(id)].focus();
    if(location.hash.slice(1)!==id) history.replaceState(null,'','#'+id);
  }
  tabs.forEach(function(t,n){
    t.addEventListener('click',function(){pick(ids[n]);var p=document.querySelector('.picker');
      var top=document.getElementById('p-'+ids[n]).getBoundingClientRect().top+scrollY-p.offsetHeight;
      if(scrollY>top) scrollTo({top:top,behavior:'smooth'});});
    t.addEventListener('keydown',function(e){
      var d=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;
      if(d){e.preventDefault();pick(ids[(n+d+3)%3],true);}
    });
  });
  var h=location.hash.slice(1).split('-')[0];
  pick(h);
  if(location.hash.indexOf('-')>0){var el=document.getElementById(location.hash.slice(1));if(el)el.scrollIntoView();}
  addEventListener('hashchange',function(){var k=location.hash.slice(1);if(ids.indexOf(k)>=0){pick(k);
    document.getElementById('p-'+k).scrollIntoView({behavior:'smooth'});}});

  // photo viewers
  var lb=document.getElementById('lb'),lbImg=lb.querySelector('img'),lbCap=lb.querySelector('p'),cur=null;
  document.querySelectorAll('.viewer').forEach(function(v){
    var data=JSON.parse(v.dataset.gal),i=0,img=v.querySelector('.main'),cap=v.querySelector('.cap'),cnt=v.querySelector('.count');
    var th=v.querySelectorAll('.th');
    function go(n){
      i=(n+data.length)%data.length;var d=data[i];
      img.classList.add('out');
      var pre=new Image();pre.onload=pre.onerror=function(){
        img.srcset=d.s+' 800w, '+d.l+' 1600w';img.src=d.l;img.alt=d.c;img.classList.remove('out');};
      pre.src=innerWidth>900?d.l:d.s;
      cap.textContent=d.c;cnt.textContent=(i+1)+' / '+data.length;
      th.forEach(function(t,k){t.toggleAttribute('aria-current',k===i);if(k===i)t.setAttribute('aria-current','true');});
      th[i].scrollIntoView({block:'nearest',inline:'nearest'});
    }
    v.querySelector('.prev').onclick=function(){go(i-1)};
    v.querySelector('.next').onclick=function(){go(i+1)};
    th.forEach(function(t,k){t.onclick=function(){go(k)}});
    var f=v.querySelector('.frame'),x0=null;
    f.addEventListener('pointerdown',function(e){x0=e.clientX});
    f.addEventListener('pointerup',function(e){if(x0===null)return;var dx=e.clientX-x0;x0=null;
      if(Math.abs(dx)>40){go(i+(dx<0?1:-1));f.dataset.sw=1;}});
    f.addEventListener('click',function(){if(f.dataset.sw){delete f.dataset.sw;return;}
      cur={go:function(n){go(n);show();},i:function(){return i}};show();if(lb.showModal)lb.showModal();});
    function show(){lbImg.src=data[i].l;lbImg.alt=data[i].c;lbCap.textContent=data[i].c;}
    v.addEventListener('keydown',function(e){if(e.key==='ArrowRight')go(i+1);if(e.key==='ArrowLeft')go(i-1);});
  });
  lb.querySelector('.prev').onclick=function(){cur.go(cur.i()-1)};
  lb.querySelector('.next').onclick=function(){cur.go(cur.i()+1)};
  lb.querySelector('.close').onclick=function(){lb.close()};
  lb.addEventListener('click',function(e){if(e.target===lb)lb.close()});
  lb.addEventListener('keydown',function(e){if(e.key==='ArrowRight')cur.go(cur.i()+1);if(e.key==='ArrowLeft')cur.go(cur.i()-1);});

  // chips: layouts and floor plans
  document.querySelectorAll('.chips:not(.mini)').forEach(function(c){
    var panes=c.nextElementSibling.querySelectorAll('.pane');
    c.querySelectorAll('.chip').forEach(function(b){b.onclick=function(){
      c.querySelectorAll('.chip').forEach(function(x){x.setAttribute('aria-pressed',x===b)});
      panes.forEach(function(p){p.hidden=p.dataset.k!==b.dataset.k});
    }});
  });

  // material board
  var big=document.getElementById('mbImg'),F={g:'mbG',name:'mbName',ref:'mbRef',spec:'mbSpec',where:'mbWhere'};
  var tiles=document.querySelectorAll('.tile');
  tiles.forEach(function(t){t.onclick=function(){
    var m=JSON.parse(t.dataset.m);
    tiles.forEach(function(x){x.setAttribute('aria-pressed',x===t)});
    big.classList.add('out');
    var pre=new Image();pre.onload=function(){big.src=t.dataset.img;big.classList.remove('out')};pre.src=t.dataset.img;
    Object.keys(F).forEach(function(k){document.getElementById(F[k]).textContent=m[k]});
    if(innerWidth<900) document.querySelector('.detail').scrollIntoView({behavior:'smooth',block:'start'});
  }});
  document.querySelectorAll('.chips.mini .chip').forEach(function(b,_,all){b.onclick=function(){
    all.forEach(function(x){x.setAttribute('aria-pressed',x===b)});
    tiles.forEach(function(t){t.hidden=b.dataset.f!=='all'&&t.dataset.g!==b.dataset.f});
  }});
})();
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500'
         '&family=Lato:wght@400;700;900&display=swap">')

DESCRIPTION = ("Brazilian modern homes for Austin lots: Casa 01 on its own, a Casa 02 pair, or the pair plus a Casita. "
               "Photos, site layouts, floor plans and the material board.")


def page(preview=False):
    seg = "".join(
        f'<button role="tab" type="button" id="t-{o["id"]}" aria-controls="p-{o["id"]}" aria-selected="{"true" if i == 0 else "false"}"'
        f'{"" if i == 0 else " tabindex=\"-1\""}><b>{esc(o["name"])}</b><span>{esc(o["sub"])}</span></button>'
        for i, o in enumerate(OPTIONS))
    opts = "".join(option_html(o, i == 0) for i, o in enumerate(OPTIONS))
    if preview:      # the Artifact preview: the host adds the document skeleton
        head = (f'<title>Single, Duo and Trio</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'{FONTS}<style>{CSS}</style>\n')
        tail = ""
    else:
        head = None
        tail = "</body></html>"
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Homes · Brazilian Modern Homes</title>
<meta name="description" content="{esc(DESCRIPTION)}">
<meta name="theme-color" content="#1d2520">
<meta property="og:type" content="website"><meta property="og:title" content="The Homes · Brazilian Modern Homes">
<meta property="og:description" content="{esc(DESCRIPTION)}"><meta property="og:image" content="{SITE_URL}{URL}og.jpg">
{f'<meta property="og:url" content="{SITE_URL}/homes/">' if SITE_URL else ""}
<meta name="twitter:card" content="summary_large_image">
{FONTS}<style>{CSS}</style></head><body>
@@BODY@@<header class="top">
  <div class="wrap bar">
    <a class="brand" href="/">Brazilian Modern Homes</a>
    <nav class="links" aria-label="Site"><a href="/house/"><span class="lg">Casa 01 in </span>3D</a>
      <a class="lg" href="#materials">Materials</a><a class="pill" href="/#join">Join<span class="lg"> the list</span></a></nav>
  </div>
  <div class="wrap hello">
    <div class="eyebrow">The homes</div>
    <h1>One way of building, three sizes.</h1>
    <p class="lede">A courtyard house on its own lot, a pair of two-story homes, or the pair plus a Casita.
      Limestone, cedar and cobogó in every one.</p>
  </div>
</header>
<div class="picker">
  <div class="wrap">
    <div class="seg" role="tablist" aria-label="Choose a home">{seg}</div>
    <nav class="jump" aria-label="On this page"><a data-s="photos" href="#single-photos">Photos</a><a data-s="layouts" href="#single-layouts">Site</a>
      <a data-s="plans" href="#single-plans">Plans</a><a href="#materials">Materials</a></nav>
  </div>
</div>
<main>
{opts}
{board_html()}
<section class="band dark end">
  <div class="wrap">
    <div class="eyebrow">Next</div>
    <h2>Take a closer look.</h2>
    <div class="cta-row">
      <a class="btn primary" href="/#join">Join the early list</a>
      <a class="btn ghost" href="/house/">Casa 01 in 3D</a>
      <a class="btn ghost" href="/Casa01_Lookbook.pdf" target="_blank" rel="noopener">Casa 01 lookbook</a>
      <a class="btn ghost" href="/Phase2_Lookbook.pdf" target="_blank" rel="noopener">Duo + Trio lookbook</a>
    </div>
  </div>
</section>
</main>
<footer>
  <div class="wrap foot">
    <div class="f-brand"><a href="/">Brazilian Modern Homes</a><p>Brazilian soul. Texas materials.</p></div>
    <nav class="f-col" aria-label="The homes"><b>The homes</b><a href="#single">Single · Casa 01</a><a href="#duo">Duo · Casa 02 pair</a>
      <a href="#trio">Trio · with a Casita</a><a href="#materials">Materials</a></nav>
    <nav class="f-col" aria-label="Explore"><b>Explore</b><a href="/house/">Casa 01 in 3D</a>
      <a href="/Casa01_Lookbook.pdf" target="_blank" rel="noopener">Casa 01 lookbook</a>
      <a href="/Phase2_Lookbook.pdf" target="_blank" rel="noopener">Duo + Trio lookbook</a></nav>
    <nav class="f-col" aria-label="Get started"><b>Get started</b><a href="/#join">Join the early list</a></nav>
  </div>
  <div class="wrap"><div class="f-base"><span>© 2026 Brazilian Modern Homes · Austin, Texas</span><span>Renderings are concept designs.</span></div></div>
</footer>
<dialog class="lb" id="lb" aria-label="Photo">
  <img src="" alt="">
  <div class="bar2"><p></p><span class="nav"><button class="arrow prev" type="button" aria-label="Previous photo">←</button>
  <button class="arrow next" type="button" aria-label="Next photo">→</button>
  <button class="arrow close" type="button" aria-label="Close">✕</button></span></div>
</dialog>
<script>{JS}</script>
'''
    if preview:
        return head + doc.split("@@BODY@@", 1)[1]
    return doc.replace("@@BODY@@", "") + tail


def og():
    im = Image.open(render_src("duo_street")).convert("RGB")
    w, h = im.size
    ch = round(w / 1.905)
    top = max(0, min(h - ch, round(h * 0.08)))
    im.crop((0, top, w, top + ch)).resize((1200, 630), Image.LANCZOS).save(os.path.join(IMG, "og.jpg"), quality=84)


def preview(out):
    """A self-contained copy for a private Artifact preview: relative image paths, Casa 01 photos copied in."""
    global URL, C01
    URL, C01 = "img/", "img/c01/"
    os.makedirs(os.path.join(out, "img", "c01"), exist_ok=True)
    for f in os.listdir(IMG):
        shutil.copy(os.path.join(IMG, f), os.path.join(out, "img", f))
    land = os.path.join(CASA01, "landing", "site", "img")
    for k, _ in C01_GAL:
        for w in (800, 1600):
            shutil.copy(os.path.join(land, f"{k}-{w}.jpg"), os.path.join(out, "img", "c01", f"{k}-{w}.jpg"))
    open(os.path.join(out, "homes.html"), "w").write(page(preview=True))
    print("wrote preview", os.path.join(out, "homes.html"))


if __name__ == "__main__":
    images()
    og()
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w").write(page())
    print("wrote", os.path.join(SITE, "index.html"))
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
