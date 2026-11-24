"""Phase 2 lookbook: the duo and trio homes, Casa 02 + Casita. Same template as the Casa 01 lookbook.

    python3 phase2/lookbook/build.py
    node phase2/lookbook/make_pdf.js            -> phase2/Phase2_Lookbook.pdf

Organized in five parts: I The duo, II Inside, III The trio, IV The homes (plans, elevations, sections),
V Finishes. Images: the final high-detail renders (phase2/render/final, falling back to the earlier sets),
the material swatches (made for the web page by phase2/web/build.py, else Casa 01's), and drawings generated
live from the model: plans and site plans by the concept kit, elevations by phase2/plans/plans.py.
"""
import html
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
sys.path.insert(0, P2)
sys.path.insert(0, os.path.join(P2, "concepts"))
import concepts as C  # noqa: E402  (plans and site plans from the model)
from model.finishes import EXTERIOR, INTERIOR, KITCHEN, BATHS, DETAILS  # noqa: E402

H = C.H
IMG = os.path.join(HERE, "img")
RENDER_DIRS = [os.path.join(P2, "render", d) for d in ("final", "hifi_v2", "hifi")]
SW_DIRS = [os.path.join(P2, "web", "site", "img"), os.path.join(ROOT, "casa01", "renders", "swatches")]
ELEV = os.path.join(P2, "plans", "out")
VIEWS = ["duo_street", "duo_dusk", "duo_entry", "duo_garden", "kitchen", "primary_bath", "upper_hall",
         "trio_street", "side_drive", "trio_aerial"]
esc = html.escape

A = H.area_summary()
FACTS = [(f"{A['carport_total']:,.0f}", "sf Casa 02 · 3 bed / 2.5 bath"), (f"{A['suite_total']:,.0f}", "sf with the suite · 3 + den"),
         (f"{A['casita']:,.0f}", "sf Casita · 1 bed + flex"), ("2–3", "homes on one lot"), ("50–65'", "typical Austin lots")]
MOVES = [
    ("Two or three homes, one lot", "Austin's HOME rules allow two or three homes on a standard lot. A pair of Casa 02s "
     "makes a duo; add the one-story Casita and it is a trio, on lots 50 to 65 feet wide."),
    ("One family of parts", "Casa 02 and the Casita share Casa 01's palette: white stucco, cedar, cobogó, Lueders "
     "limestone and black calçada. Two plans, mirrored and turned, fit every layout."),
    ("A lantern at the street", "A two-story cobogó screen stands over the front doors and the stair. By day it shades "
     "and screens; at night the stair light turns it into a lantern."),
    ("Light from above", "Skylights over the stair, the primary shower, the tub, the walk-in and the laundry; a cedar "
     "sunshade over the back slider; every home opens to its own pátio."),
]
PARTS = [("I", "The duo", "Two Casa 02s on one lot"), ("II", "Inside", "Kitchen, baths, the stair"),
         ("III", "The trio", "The pair plus a Casita"), ("IV", "The homes", "Plans, elevations, sections"),
         ("V", "Finishes", "The material board")]


# ---------------------------------------------------------------- helpers
def prep_images():
    os.makedirs(IMG, exist_ok=True)
    have = {}
    for v in VIEWS:
        src = next((os.path.join(d, f"{v}.png") for d in RENDER_DIRS if os.path.exists(os.path.join(d, f"{v}.png"))), None)
        if not src:
            print("  missing render:", v)
            continue
        dst = os.path.join(IMG, f"{v}.jpg")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            Image.open(src).convert("RGB").save(dst, quality=88, optimize=True, progressive=True)
        have[v] = f"img/{v}.jpg"
    for m in EXTERIOR + INTERIOR:
        k = m["key"]
        src = next((p for d in SW_DIRS for p in (os.path.join(d, f"sw_{k}.jpg"), os.path.join(d, f"{k}.png"))
                    if os.path.exists(p)), None)
        if src:
            dst = os.path.join(IMG, f"sw_{k}.jpg")
            Image.open(src).convert("RGB").resize((360, 360), Image.LANCZOS).save(dst, quality=86)
            have["sw_" + k] = f"img/sw_{k}.jpg"
    return have


def svg_fit(s):
    s = re.sub(r'(<svg[^>]*?) width="[\d.]+" height="[\d.]+"', r'\1', s, count=1)
    return s.replace("<svg ", '<svg class="dwg" preserveAspectRatio="xMidYMid meet" ', 1)


def elev(key):
    return svg_fit(open(os.path.join(ELEV, f"elev_{key}.svg")).read())


def site(lid):
    return next(f() for f in C.SITES if f()["id"] == lid)


def clean(note):
    return re.sub(r"\s*\([^)]*(P2-\d+|impervious)[^)]*\)", "", note)


CSS = open(os.path.join(ROOT, "casa01", "lookbook", "build.py")).read().split('CSS = r"""')[1].split('"""')[0]
CSS = CSS.replace("url(fonts/", "url(../../casa01/lookbook/fonts/")
CSS += """
.bleed{background:#111}
.bleed img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.bleed .label.top{bottom:auto;top:40px}
.bleed .callouts{position:absolute;right:40px;bottom:40px;display:flex;flex-direction:column;gap:6px;align-items:flex-end}
.bleed .callouts span{background:rgba(29,37,32,.82);color:#f3efe4;font:700 10px/1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;padding:8px 10px}
.bleed .part{position:absolute;left:44px;top:34px;font:700 10px/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;
  color:#f3efe4;background:rgba(29,37,32,.7);padding:7px 10px}
.bleed .part.low{top:auto;bottom:40px}
.cover .panel h1{font-size:64px;line-height:.98;margin:18px 0 0}
.cover .goldrule{height:2px;width:64px;background:var(--gold);margin-top:18px}
.cover .tagline{font-family:var(--serif);font-style:italic;font-size:22px;color:#cdbb92;margin-top:16px;text-transform:none;letter-spacing:0;font-weight:500}
.cover .bottom{position:absolute;left:54px;bottom:50px;font:700 10px/1.6 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#cdbb92}
.cover .eyebrow{color:#cdbb92}
.facts{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;border-top:1px solid var(--line);padding-top:14px}
.facts .n{font-family:var(--serif);font-size:30px;line-height:1}
.two{display:grid;grid-template-columns:1fr 1fr;gap:22px;height:100%}
figure{margin:0;display:flex;flex-direction:column;gap:8px;min-height:0}
figure .ph{flex:1;min-height:0;overflow:hidden}
figcaption{font-size:12px;color:var(--muted);line-height:1.45}
figcaption b{display:block;font:700 11px/1.3 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:3px}
.contents{display:flex;flex-direction:column;border-top:1px solid var(--line)}
.contents div{display:grid;grid-template-columns:40px 1fr auto;gap:10px;align-items:baseline;padding:11px 0;border-bottom:1px solid var(--line)}
.contents .r{font-family:var(--serif);font-size:24px;color:var(--gold);line-height:1}
.contents h3{margin:0;font-family:var(--serif);font-weight:500;font-size:24px;line-height:1}
.contents small{display:block;font-size:11px;color:var(--muted);margin-top:3px}
.contents .pg{font:700 10px/1 var(--sans);letter-spacing:.12em;color:var(--muted)}
.cols{display:grid;gap:14px;height:100%}
.cols .p{display:flex;flex-direction:column;gap:6px;min-height:0}
.cols .dwgwrap{flex:1}
.cols h4,.dl h4,.lay2 h4{margin:0;font:700 11px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase}
.cols small{font-size:10.5px;color:var(--muted);line-height:1.35}
.lay2{display:grid;grid-template-columns:270px 1fr 310px 1fr;gap:22px;height:100%}
.lay2 .info{display:flex;flex-direction:column;gap:10px;min-width:0}
.lay2 h3{margin:0;font-family:var(--serif);font-weight:500;font-size:24px;line-height:1.05}
.lay2 .kv{grid-template-columns:auto 1fr}
.lay2 .kv div:nth-child(2n){text-align:right}
.lay2 ul{margin:0;padding-left:16px;font-size:11.5px;line-height:1.45;color:#3d433e;display:flex;flex-direction:column;gap:5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:14px 18px;height:100%}
.grid2 .p{display:flex;flex-direction:column;gap:5px;min-height:0}
.grid2 .dwgwrap{flex:1}
.grid2 h4{margin:0;font:700 10.5px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase}
.casita{display:grid;grid-template-columns:1fr 1.25fr;gap:18px;height:100%}
.casita .right{display:grid;grid-template-rows:1fr 1fr 1fr;gap:10px;min-height:0}
.casita .p{display:flex;flex-direction:column;gap:5px;min-height:0}
.casita .dwgwrap{flex:1}
.casita h4{margin:0;font:700 10.5px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase}
.dl{display:grid;grid-template-columns:1fr 1fr 1fr;gap:26px}
.dl .g{display:flex;flex-direction:column;gap:2px}
.dl h4{padding-bottom:8px;border-bottom:1px solid var(--ink);margin-bottom:4px}
.dl .row{padding:7px 0;border-bottom:1px solid var(--line);font-size:11.5px;line-height:1.45;color:#3d433e}
.dl .row b{display:block;font:700 10px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink);margin-bottom:2px}
.strip{position:absolute;left:0;right:0;bottom:0;display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.strip img{width:100%;height:74px;object-fit:cover;border:1px solid var(--line)}
.strip span{display:block;font:700 9.5px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:6px}
.sw{grid-template-columns:repeat(7,1fr)!important;gap:14px 14px!important}
.sw img{aspect-ratio:1.2/1!important}
.sw .grp{grid-column:1/-1;font:700 10px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sage);border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:2px}
"""

FOOT = "Brazilian Modern Homes / Phase 2 · Duo + Trio"


def page(n, eyebrow, title, sub, inner):
    return (f'<section class="page"><div class="bar"></div><div class="head"><div class="eyebrow">{eyebrow}</div>'
            f'<h2>{title}</h2><div class="sub">{sub}</div><div class="rule"></div></div>'
            f'<div class="body">{inner}</div><div class="foot"><span>{FOOT}</span><span>{n:02d}</span></div></section>')


def bleed(src, part, eyebrow, title, text, callouts=(), top=False):
    co = "".join(f"<span>{c}</span>" for c in callouts)
    pt = f'<div class="part{" low" if top else ""}">{part}</div>' if part else ""
    return (f'<section class="page bleed"><img src="{src}" alt="{esc(title)}">{pt}'
            f'<div class="label{" top" if top else ""}"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{text}</p></div>'
            f'<div class="callouts">{co}</div></section>')


def fig(src, b, cap):
    return (f'<figure><div class="ph"><img class="fill" src="{src}" alt="{esc(b)}"></div>'
            f'<figcaption><b>{b}</b>{cap}</figcaption></figure>')


def layout_info(s):
    m = C.check_site(s)
    kinds = {}
    for h in s["homes"]:
        kinds.setdefault(h["kind"], []).append(h["beds"])
    homes = "; ".join(f"{len(v)} × {k}" if len(v) > 1 else k for k, v in kinds.items())
    kv = [("Lot", f'{s["lot"]["W"]:.0f} x {s["lot"]["L"]:.0f} ft'), ("Homes", homes), ("Floor area", f'{m["fa"]:,.0f} sf'),
          ("Parking", f'{m["parking"]} on site'), ("Paving", f'{m["ic"]:,.0f} of {m["ic_cap"]:,.0f} sf')]
    kvs = "".join(f"<div>{a}</div><div>{b}</div>" for a, b in kv)
    notes = "".join(f"<li>{esc(clean(n))}</li>" for n in s["notes"][:3])
    return (f'<div class="info"><div class="eyebrow">{s["id"]}</div><h3>{esc(s["name"])}</h3>'
            f'<div class="kv">{kvs}</div><ul>{notes}</ul></div>')


def build(img):
    P = []
    n = 0

    def nxt():
        nonlocal n
        n += 1
        return n

    nxt()
    P.append(f'''<section class="page cover"><div class="panel"><div class="eyebrow">Phase 2 · November 2026</div>
<div class="goldrule"></div><h1>Casa 02<br>+ Casita</h1><div class="tagline">Duo and trio homes for Austin lots</div>
<p style="font-size:13px;line-height:1.6;color:#d9d3c4;margin-top:26px;max-width:300px">Two or three homes on one lot,
in the same Brazilian modern language as Casa 01: a cobogó lantern at the street, cedar gates, Lueders limestone
walls and a white upper floor.</p>
<div class="bottom">Brazilian soul. Texas materials.<br>Renders + layouts + drawings + finishes</div></div>
<div style="position:relative"><img class="fill" src="{img.get("duo_dusk", "")}" alt="Casa 02 duo at dusk"></div></section>''')

    # contents: page numbers are fixed by the order below
    starts = {"I": 3, "II": 7, "III": 10, "IV": 14, "V": 17}
    moves = "".join(f'<div class="move"><div class="k">{i + 1}</div><div><h3>{t}</h3><p>{p}</p></div></div>'
                    for i, (t, p) in enumerate(MOVES))
    facts = "".join(f'<div><div class="n">{a}</div><div class="l">{b}</div></div>' for a, b in FACTS)
    cont = "".join(f'<div><span class="r">{r}</span><span><h3>{t}</h3><small>{s}</small></span><span class="pg">P. {starts[r]:02d}</span></div>'
                   for r, t, s in PARTS)
    P.append(page(nxt(), "The idea", "More homes on the same lot, with the same soul",
                  "Phase 2 turns Casa 01's language into a repeatable family for Austin's HOME rules.",
                  f'<div style="display:grid;grid-template-columns:1.25fr 1fr;gap:40px;height:100%">'
                  f'<div style="display:flex;flex-direction:column;gap:18px"><div class="moves">{moves}</div>'
                  f'<div class="facts">{facts}</div></div>'
                  f'<div><div class="eyebrow" style="margin-bottom:10px">Contents</div><div class="contents">{cont}</div></div>'
                  f'</div>'))

    # I. the duo -------------------------------------------------------------
    P.append(bleed(img.get("duo_street", ""), "I · The duo", "The duo · 50 x 125 lot", "Stone, cedar, cobogó",
                   "A side-by-side pair reads as one composition: limestone walls at the outer corners, cedar carport "
                   "gates, and one cobogó lantern over the two front doors. Low limestone walls at each walk hold the "
                   "mailbox, the house number and a light.",
                   ["Lueders limestone corner", "Cedar slat gate", "Two-story cobogó", "Mailbox wall"])); nxt()
    P.append(bleed(img.get("duo_dusk", ""), "I · The duo", "At dusk", "The lantern",
                   "The stair rises right behind the cobogó. With the stair light on, the screen glows the way Casa 01's "
                   "does, and the carports' cedar ceilings warm the street.",
                   ["Cobogó lit from within", "Cedar carport ceiling", "Path lights"])); nxt()
    P.append(page(nxt(), "I · The duo", "Through the screen, out to the garden",
                  "The front door sits inside the cobogó, on a calçada threshold. At the back, each home opens wide to its own pátio.",
                  f'<div class="two">'
                  f'{fig(img.get("duo_entry", ""), "The entry", "The front door under the screen, beside the cedar carport gate and the limestone corner wall. The carport side door is the step-free entry, across a black calçada rug.")}'
                  f'{fig(img.get("duo_garden", ""), "The pátio", "A 16-ft slider opens the kitchen and dining room to a São Tomé limestone terrace, shaded by a cedar sunshade, and a garden under a live oak.")}'
                  f'</div>'))
    a, b = site("L1-D1"), site("L4-D2")
    P.append(page(nxt(), "I · The duo", "Two ways to set the pair",
                  "Side by side on a 50 ft lot, or front and back down a shared drive on a 65 ft lot, where the bay becomes a ground-floor suite.",
                  f'<div class="lay2"><div class="dwgwrap">{svg_fit(C.site_svg(a))}</div>{layout_info(a)}'
                  f'<div class="dwgwrap">{svg_fit(C.site_svg(b))}</div>{layout_info(b)}</div>'))

    # II. inside -------------------------------------------------------------
    P.append(bleed(img.get("kitchen", ""), "II · Inside", "The kitchen", "Oak, green tile, black granite",
                   "One wall of rift oak under a single oak shelf and green zellige-look tile; a 10 ft honed granite "
                   "island with an oak table built onto its living-room side, seating four. The stair and its cedar "
                   "slats rise beside it.",
                   ["Rift white oak", "Green glazed tile", "Honed black granite", "Opal globe pendants"], top=True)); nxt()
    P.append(page(nxt(), "II · Inside", "Baths and the stair, lit from above",
                  "Skylights where they count: over the primary shower, the tub, the stair, the walk-in and the laundry.",
                  f'<div class="two">'
                  f'{fig(img.get("primary_bath", ""), "The primary bath", "Seen from the walk-in shower: green tile to the ceiling under a skylight; a floating oak vanity with a limestone top and vessel sink, a round brass mirror between two sconces, a wall-hung wc.")}'
                  f'{fig(img.get("upper_hall", ""), "The upstairs hall", "A skylight over the open oak stair washes the hall with daylight under a cedar ceiling; cedar slats screen the stair, and the landing desk sits behind the cobogó.")}'
                  f'</div>'))
    cols = []
    for title, rows in (("Kitchen", KITCHEN), ("Baths", BATHS), ("Details", DETAILS)):
        r = "".join(f'<div class="row"><b>{esc(k)}</b>{esc(v)}</div>' for k, v in rows)
        cols.append(f'<div class="g"><h4>{title}</h4>{r}</div>')
    P.append(page(nxt(), "II · Inside", "Kitchens, baths and the small things",
                  "The finish schedule for every Casa 02 and Casita. The same family as Casa 01, sized for a smaller home.",
                  f'<div class="dl">{"".join(cols)}</div>'
                  f'<div class="strip">' + "".join(
                      f'<div><img src="{img.get("sw_" + m["key"], "")}" alt=""><span>{esc(m["name"])}</span></div>'
                      for m in INTERIOR) + '</div>'))

    # III. the trio ----------------------------------------------------------
    P.append(bleed(img.get("trio_street", ""), "III · The trio", "The trio · Casita at the street", "A garden wall, a cedar gate",
                   "On an alley lot the one-story Casita faces the street behind its walled garden: a limestone wall, "
                   "cobogó between cedar posts and a cedar slat gate, with a covered porch inside. The pair sits back "
                   "and parks off the alley.",
                   ["Limestone wall", "Cobogó panel", "Cedar garden gate"], top=True)); nxt()
    P.append(bleed(img.get("side_drive", ""), "III · The trio", "The trio · 65 x 125 lot, one drive", "A stone wall to the street",
                   "One 12 ft drive along the side serves all three homes. Each Casa 02 parks across its front, turning in "
                   "from the drive, so the street sees a full limestone wall under the cobogó.",
                   ["Shared drive", "Limestone street wall", "Cobogó above"])); nxt()
    P.append(bleed(img.get("trio_aerial", ""), "III · The trio", "The trio · 50 x 125 lot", "Three homes, three gardens",
                   "The pair at the street, the Casita in the back garden on a stepping-stone path. Every home has its own "
                   "pátio; solar on the roofs, skylights over the stairs and baths.",
                   ["Casita behind", "Private pátios", "Rooftop solar"], top=True)); nxt()
    lay = []
    for lid in ("L1-T1", "L2-T2", "L3-T1", "L4-T1"):
        s = site(lid)
        m = C.check_site(s)
        lay.append(f'<div class="p"><h4>{lid} · {s["lot"]["W"]:.0f} x {s["lot"]["L"]:.0f}'
                   f'{" · alley" if s["lot"].get("alley") else ""}{" · corner" if s["lot"].get("corner") else ""}</h4>'
                   f'<div class="dwgwrap">{svg_fit(C.site_svg(s))}</div>'
                   f'<small><b>{esc(s["name"])}</b><br>{m["fa"]:,.0f} sf · parking for {m["parking"]} of {m["n"]} · '
                   f'paving {m["ic"]:,.0f} of {m["ic_cap"]:,.0f} sf</small></div>')
    P.append(page(nxt(), "III · The trio", "Four ways to fit three homes",
                  "Each passes Austin's floor-area, building-cover, impervious-cover and front-yard paving limits. "
                  "The Casita goes behind, at the street, on the corner, or down a shared drive.",
                  f'<div class="cols" style="grid-template-columns:repeat(4,1fr)">{"".join(lay)}</div>'))

    # IV. the homes ----------------------------------------------------------
    pl = [("Ground floor, carport", C.plan_svg(H.CASA02_GF_CARPORT, note_front="FRONT"), f"{A['carport_gf']:,.0f} sf + carport · most lots"),
          ("Ground floor, side drive", C.plan_svg(H.CASA02_GF_SIDE, note_front="FRONT"), f"{A['carport_gf']:,.0f} sf + carport · shared drive"),
          ("Ground floor, suite", C.plan_svg(H.CASA02_GF_SUITE, note_front="FRONT"), f"{A['suite_gf']:,.0f} sf · parking on a pad"),
          ("Upper floor", C.plan_svg(H.CASA02_UPPER, note_front="FRONT"), f"{A['upper']:,.0f} sf · every version")]
    cols = "".join(f'<div class="p"><h4>{t}</h4><div class="dwgwrap">{svg_fit(s)}</div><small>{c}</small></div>'
                   for t, s, c in pl)
    P.append(page(nxt(), "IV · The homes", "Casa 02 plans",
                  "20 x 39 ft, two stories. Three ground floors for three kinds of lot, one upper floor. "
                  "Dimensioned plans and schedules: Phase2_Casa02_Plans.pdf.",
                  f'<div class="cols" style="grid-template-columns:repeat(4,1fr)">{cols}</div>'))
    el = [("Front, carport version", "front_gc"), ("Back, toward the pátio", "back_gc"),
          ("Outer side, carport version", "side_gc"), ("Section through the stair", "sect_a")]
    cells = "".join(f'<div class="p"><h4>{t}</h4><div class="dwgwrap">{elev(k)}</div></div>' for t, k in el)
    P.append(page(nxt(), "IV · The homes", "Casa 02 elevations and section",
                  "Limestone at the corner walls, the cobogó lantern, a dark bronze band between the floors, a 15 in fascia. "
                  "9'-6\" ceilings downstairs, cedar under the roof upstairs.",
                  f'<div class="grid2">{cells}</div>'))
    P.append(page(nxt(), "IV · The homes", "The Casita",
                  f"20 x 32 ft, one story, {A['casita']:,.0f} sf: living and kitchen, a flex room, a bedroom and bath, "
                  "and a covered porch on its walled garden.",
                  f'<div class="casita"><div class="p"><h4>Plan</h4><div class="dwgwrap">'
                  f'{svg_fit(C.plan_svg(H.CASITA, scale=15.0, note_front="FRONT"))}</div></div>'
                  f'<div class="right"><div class="p"><h4>Front</h4><div class="dwgwrap">{elev("cs_front")}</div></div>'
                  f'<div class="p"><h4>Side</h4><div class="dwgwrap">{elev("cs_side")}</div></div>'
                  f'<div class="p"><h4>Section</h4><div class="dwgwrap">{elev("cs_sect")}</div></div></div></div>'))

    # V. finishes ------------------------------------------------------------
    def tiles(items):
        return "".join(f'<div class="t"><img src="{img.get("sw_" + m["key"], "")}" alt="{esc(m["name"])}"><h4>{esc(m["name"])}</h4>'
                       f'<div class="br">{esc(m["ref"])}</div><div class="sp">{esc(m["where"])}</div></div>' for m in items)
    ext = [m for m in EXTERIOR if m["key"] != "dg"]
    inn = INTERIOR + [m for m in EXTERIOR if m["key"] == "dg"]
    P.append(page(nxt(), "V · Finishes", "The material board",
                  "Fourteen materials, the same in every home. Each pairs a Brazilian modern original with what an Austin builder buys.",
                  f'<div class="sw"><div class="grp">Outside</div>{tiles(ext)}<div class="grp">Inside and garden</div>{tiles(inn)}</div>'))
    rows = "".join(f'<tr><td><b>{esc(m["name"])}</b></td><td>{esc(m["spec"])}</td></tr>' for m in EXTERIOR + INTERIOR)
    P.append(page(nxt(), "V · Finishes", "The specification",
                  "What to order, by material. Quantities and pricing come with the builder bid.",
                  f'<table style="font-size:11px">{rows}</table>'))

    items = [("Concept sheets", "Phase2_Concepts.pdf: C-1 to C-8, the plans and the six site plans with their checks"),
             ("Developed drawings", "Phase2_Casa02_Plans.pdf: A-101 to A-104 plans, A-201 to A-204 elevations, A-301 sections"),
             ("AutoCAD", "Phase2_Concepts.dxf: every plan as a block, every site and sheet as a paper-space layout"),
             ("Facade study", "Phase2_Facade_Options.pdf: the three options and the direction chosen"),
             ("Test-fit", "Phase2_TestFit.pdf: 19 layouts on six standard Austin lots"),
             ("Website", "/homes/: Single, Duo and Trio, with photos, layouts, plans and the material board")]
    nx = ["Structure and MEP with the engineer: the shared wall, the cobogó frame, the stair",
          "Pricing with two Austin builders from these drawings",
          "A Lot Fit Study on a real lot, then the city's HOME review"]
    li = "".join(f"<li>{t}</li>" for t in nx)
    trs = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td></tr>" for a, b in items)
    P.append(page(nxt(), "In the package", "What's drawn, and what's next",
                  "Everything comes from one model, so a change shows up in the drawings, the AutoCAD file, the renders and the website.",
                  f'<div style="display:grid;grid-template-columns:1.3fr 1fr;gap:34px">'
                  f'<div><table>{trs}</table></div><div class="side"><div class="eyebrow">Next</div>'
                  f'<ul class="list">{li}</ul><div class="note"><b>Concept design</b>Not for construction. Confirm '
                  f'zoning, utilities, trees and fire access with the City of Austin before pricing.</div></div></div>'))
    # check the contents page numbers against where each part really starts
    real = {}
    for i, p in enumerate(P, 1):
        mm = re.search(r'class="(?:eyebrow|part[^"]*)">(I|II|III|IV|V) · ', p)
        if mm and mm.group(1) not in real:
            real[mm.group(1)] = i
    assert real == starts, (real, starts)
    return P


def main():
    img = prep_images()
    pages = build(img)
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><title>Phase 2 lookbook</title>'
           f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(os.path.join(HERE, "print.html"), "w").write(doc)
    print("wrote", os.path.join(HERE, "print.html"), len(pages), "pages; images:", sorted(k for k in img if not k.startswith("sw_")))


if __name__ == "__main__":
    main()
