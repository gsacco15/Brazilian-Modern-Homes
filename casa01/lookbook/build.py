"""Build the Casa 01 lookbook (print HTML -> PDF, and a web page) from the
renders, the SVG drawings and design.py.

    python3 casa01/lookbook/build.py
    node casa01/lookbook/make_pdf.js
"""
import html
import math
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
sys.path.insert(0, CASA)
import design as D  # noqa: E402

RENDERS = os.path.join(CASA, "renders")
DRAW = os.path.join(CASA, "drawings")
IMG = os.path.join(HERE, "img")
WEB = os.path.join(HERE, "web")

VIEWS = ["street", "street_dusk", "entry", "courtyard", "interior", "kitchen", "gallery", "veranda", "rear", "aerial"]
SWATCHES = [
    ("limestone", "Lueders limestone", "Pedra São Tomé / moledo", "Sawn-face ashlar, 3 course heights"),
    ("cobogo", "Concrete cobogó", "Cobogó, Recife 1929", "12x12x4 precast, white cement"),
    ("cedar_z", "Western red cedar", "Freijó / ipê", "Clear T&G soffits, 2x4 slats, natural oil"),
    ("stucco", "Warm-white stucco", "White mineral plaster", "Smooth 3-coat, sand finish"),
    ("floor", "Polished concrete", "Cimento queimado", "Slab-on-grade, light grind + seal"),
    ("pavers", "Limestone pavers", "São Tomé paving", "24x36 thermal-finish, courtyard + veranda"),
    ("oak", "Rift white oak", "Tauari interiors", "Kitchen cabinets, credenza, desks"),
    ("granite", "Honed black granite", "Brazilian dark stone", "Island + counters, 1.5\" honed"),
    ("tile", "Green glazed tile", "Azulejo", "4x4 handmade-look backsplash"),
    ("bronze", "Dark bronze aluminum", "Slim steel frames", "Fascia, window frames, posts"),
    ("dg", "Decomposed granite", "Terra batida", "Stabilized paths, meadow mulch"),
    ("linen", "Natural linen", "Linho", "Upholstery + outdoor cushions"),
]


# ------------------------------------------------------------------ helpers
def ft(v):
    f = int(v + 1e-6)
    i = round((v - f) * 12)
    if i == 12:
        f, i = f + 1, 0
    return f"{f}'-{i}\""


def perim(poly):
    return sum(math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def svg_inline(name):
    s = open(os.path.join(DRAW, name)).read()
    s = re.sub(r'(<svg[^>]*?) width="\d+" height="\d+"', r'\1', s, count=1)
    return s.replace("<svg ", '<svg class="dwg" preserveAspectRatio="xMidYMid meet" ', 1)


def prep_images():
    os.makedirs(IMG, exist_ok=True)
    have = {}
    for v in VIEWS:
        src = os.path.join(RENDERS, f"{v}.png")
        if not os.path.exists(src):
            continue
        dst = os.path.join(IMG, f"{v}.jpg")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            Image.open(src).convert("RGB").save(dst, quality=86, optimize=True, progressive=True)
        have[v] = f"img/{v}.jpg"
    for key, *_ in SWATCHES:
        src = os.path.join(RENDERS, "swatches", f"{key}.png")
        if os.path.exists(src):
            dst = os.path.join(IMG, f"sw_{key}.jpg")
            Image.open(src).convert("RGB").resize((360, 360), Image.LANCZOS).save(dst, quality=88)
            have["sw_" + key] = f"img/sw_{key}.jpg"
    return have


def quantities():
    c = D.COBOGO
    nx, nz = int(c["x1"] - c["x0"]), int(c["z1"] - c["z0"])
    lw = D.LIMESTONE_WALL
    win = D.EXT_WALLS[0]["openings"][0]
    lime = (lw["x1"] - lw["x0"]) * (lw["z1"] - lw["z0"]) - win["w"] * (win["head"] - win["sill"])
    soffit = sum((z["x1"] - z["x0"]) * (z["y1"] - z["y0"]) for z in D.CEDAR_SOFFITS)
    ceil = sum((z["x1"] - z["x0"]) * (z["y1"] - z["y0"]) for z in D.CEDAR_CEILINGS)
    s = D.CEDAR_SCREEN
    slats = int((s["y1"] - s["y0"]) / (s["slat_w"] + s["gap"]))
    sliders = [o for w in D.EXT_WALLS for o in w["openings"] if o["kind"] == "slider"]
    windows = [o for w in D.EXT_WALLS for o in w["openings"] if o["kind"] in ("fixed", "casement")]
    glass_lf = sum(o["w"] for o in sliders)
    return [
        ("Cobogó screen", f"{nx * nz} blocks", f"{nx} x {nz} courses, {nx * nz} sf, on cast curb"),
        ("Limestone feature wall", f"{lime:.0f} sf", f"{lw['x1'] - lw['x0']:.1f}' long x {lw['z1']:.0f}' high, one slot window"),
        ("Cedar soffits (outside)", f"{soffit:.0f} sf", "Entry canopy, courtyard eaves, veranda"),
        ("Cedar ceilings (inside)", f"{ceil:.0f} sf", "Great room + gallery, same boards as soffit"),
        ("Cedar slat screen", f"{slats} slats", f"2x4 @ 5\" o.c., {s['y1'] - s['y0']:.1f}' run x 10' high"),
        ("Sliding glass walls", f"{len(sliders)} units", f"{glass_lf:.1f} lf total, 9'-0\" tall, dark bronze"),
        ("Windows", f"{len(windows)} units", "Casements (egress) + fixed slot / clerestory / kitchen"),
        ("Roof plate", f"{D.poly_area(D.ROOF):,.0f} sf", f"Low-slope TPO, {perim(D.ROOF):.0f} lf of 15\" bronze fascia"),
        ("Steel posts", f"{len(D.POSTS)} posts", "4\" square HSS, dark bronze"),
    ]


def room_rows():
    rows = []
    for r in D.ROOMS:
        if r["name"] in ("Cl.",):
            continue
        xs = [p[0] for p in r["poly"]]
        ys = [p[1] for p in r["poly"]]
        rows.append((r["name"], f"{ft(max(xs) - min(xs))} x {ft(max(ys) - min(ys))}", f"{D.poly_area(r['poly']):.0f}"))
    return rows


# ------------------------------------------------------------------ copy
A = D.area_schedule()
FACTS = [
    (f"{A['conditioned']:,.0f}", "sf conditioned"),
    ("3 / 2", "bed / bath"),
    (f"{A['veranda']:.0f}", "sf veranda"),
    (f"{A['courtyard']:.0f}", "sf courtyard"),
    ("12'-3\"", "to top of roof"),
]
MOVES = [
    ("One thin roof", "A single 15-inch roof edge runs the full 54-foot street front. Bedrooms, entry canopy and "
     "courtyard all sit under one horizontal line."),
    ("Enter through a garden", "A Lueders limestone wall and a full-height cobogó screen hide a private pátio. "
     "You open a cedar gate, walk under the canopy, and reach the front door inside the garden."),
    ("A cool room outside", "The great room opens both ways: south to the courtyard, north to a 276 sf "
     "veranda under the heritage oak, with the cedar ceiling running straight through."),
]
CLIMATE = [
    ("Cobogó faces south", "It filters low winter sun and summer breezes into the courtyard, and gives privacy "
     "from the street without a solid wall."),
    ("4' eave over south glass", "At Austin's latitude (30.3°N) the June noon sun (83°) stops at the courtyard "
     "paving. The December sun (36°) reaches 13 feet into the great room."),
    ("Solid west wall", "Bedrooms take side windows only, and the long west wall stays nearly blank against "
     "afternoon heat."),
    ("North veranda", "The coolest outdoor room on the lot in July: shaded by the roof and the oak, and open "
     "to evening breezes."),
]
CONVENTIONAL = [
    "Slab-on-grade foundation, polished as the finished floor",
    "2x6 wood-frame walls, stucco and limestone veneer outside",
    "Engineered joists with a low-slope TPO roof (1/4\" per foot)",
    "Standard 9'-0\" aluminum sliders, no structural glass",
    "Ducted heat pump, conventional plumbing stacked at kitchen + baths",
    "Breeze blocks laid like CMU, reinforced into steel jambs",
]


CSS = r"""
@font-face{font-family:'Cormorant Garamond';font-weight:500;src:url(fonts/CormorantGaramond-500-latin.woff2) format('woff2')}
@font-face{font-family:'Cormorant Garamond';font-weight:600;src:url(fonts/CormorantGaramond-600-latin.woff2) format('woff2')}
@font-face{font-family:'Cormorant Garamond';font-weight:500;font-style:italic;src:url(fonts/CormorantGaramond-500i-latin.woff2) format('woff2')}
@font-face{font-family:'Lato';font-weight:400;src:url(fonts/Lato-400-latin.woff2) format('woff2')}
@font-face{font-family:'Lato';font-weight:700;src:url(fonts/Lato-700-latin.woff2) format('woff2')}
@font-face{font-family:'Lato';font-weight:900;src:url(fonts/Lato-900-latin.woff2) format('woff2')}
@font-face{font-family:'Lato';font-weight:400;src:url(fonts/Lato-400-latin-ext.woff2) format('woff2');unicode-range:U+0100-02AF}
:root{--ink:#1d2520;--paper:#f6f4ee;--card:#ffffff;--sage:#5f7458;--gold:#b8955a;--line:#dcd8cd;--muted:#6b6f68;--stone:#ece5d4;
--serif:'Cormorant Garamond',Georgia,'Times New Roman',serif;--sans:'Lato','Helvetica Neue',Arial,sans-serif}
@page{size:1333px 750px;margin:0}
*{box-sizing:border-box}
html,body{margin:0;background:#888}
body{font-family:var(--sans);color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:1333px;height:750px;background:var(--paper);position:relative;overflow:hidden;page-break-after:always;break-after:page}
.page:last-child{page-break-after:auto}
.bar{position:absolute;top:0;left:0;right:0;height:7px;background:var(--sage)}
.head{position:absolute;left:50px;right:50px;top:30px}
.eyebrow{font:700 11px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sage)}
h1,h2{font-family:var(--serif);font-weight:500;margin:6px 0 0;letter-spacing:-.005em;line-height:1.05}
h2{font-size:40px}
.sub{font-size:13px;color:var(--muted);margin-top:6px}
.rule{height:1px;background:var(--line);margin-top:14px}
.foot{position:absolute;left:50px;right:50px;bottom:22px;display:flex;justify-content:space-between;font:700 9px/1 var(--sans);letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
.body{position:absolute;left:50px;right:50px;top:150px;bottom:52px}
img{display:block}
.fill{width:100%;height:100%;object-fit:cover}
.cap{font-size:12px;color:var(--muted);line-height:1.45}
.tag{display:inline-block;font:700 10px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--ink);background:var(--stone);padding:6px 9px;border-radius:2px}
/* cover */
.cover{display:grid;grid-template-columns:420px 1fr}
.cover .panel{background:var(--ink);color:#f3efe4;padding:56px 54px;position:relative}
.cover .panel .eyebrow{color:#cdbb92}
.cover h1{font-size:76px;color:#fff;margin-top:34px;line-height:.95}
.cover .goldrule{width:120px;height:4px;background:var(--gold);margin-top:30px}
.cover .tagline{font:700 15px/1.3 var(--sans);letter-spacing:.12em;color:#cdbb92;text-transform:uppercase;margin-top:18px}
.cover p{font-size:15px;line-height:1.55;color:#dcd6c8;margin-top:26px;max-width:300px}
.cover .bottom{position:absolute;left:54px;bottom:44px;font:700 10px/1.6 var(--sans);letter-spacing:.14em;color:#cdbb92;text-transform:uppercase}
/* full bleed */
.bleed img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.bleed .label{position:absolute;left:44px;bottom:40px;background:rgba(29,37,32,.86);color:#f3efe4;padding:18px 22px;max-width:470px}
.bleed .label .eyebrow{color:#cdbb92}
.bleed .label h2{color:#fff;font-size:32px}
.bleed .label p{font-size:12.5px;line-height:1.5;margin:8px 0 0;color:#dcd6c8}
.callouts{position:absolute;right:40px;bottom:40px;display:flex;flex-direction:column;gap:6px;align-items:flex-end}
.callouts span{background:rgba(246,244,238,.92);font:700 10px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;padding:7px 10px;color:var(--ink)}
/* grids */
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px;height:100%}
.two figure,.one figure{margin:0;display:flex;flex-direction:column;gap:10px;min-height:0}
.two figure .ph{flex:1;min-height:0;overflow:hidden;background:#ddd}
figcaption{font-size:12px;line-height:1.45;color:var(--muted)}
figcaption b{color:var(--ink);font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:11px;margin-right:6px}
.facts{display:flex;gap:0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.facts div{flex:1;padding:14px 16px;border-left:1px solid var(--line)}
.facts div:first-child{border-left:0;padding-left:0}
.facts .n{font-family:var(--serif);font-size:32px;line-height:1;white-space:nowrap}
.facts .l{font:700 10px/1.2 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:6px}
.moves{display:grid;grid-template-columns:1fr;gap:14px}
.move{display:grid;grid-template-columns:34px 1fr;gap:10px}
.move .k{font-family:var(--serif);font-size:30px;color:var(--gold);line-height:1}
.move h3{margin:0;font:700 14px/1.2 var(--sans);letter-spacing:.04em}
.move p{margin:4px 0 0;font-size:12.5px;line-height:1.5;color:#3d433e}
.dwgwrap{background:#fff;border:1px solid var(--line);height:100%;min-height:0;position:relative;overflow:hidden}
svg.dwg{position:absolute;left:10px;top:10px;width:calc(100% - 20px);height:calc(100% - 20px);display:block}
table{border-collapse:collapse;width:100%;font-size:11.5px}
th{font:700 9.5px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;padding:7px 8px;border-bottom:1px solid var(--ink)}
td{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.side{display:flex;flex-direction:column;gap:14px}
.note{background:#e8ebe4;padding:12px 14px;font-size:11.5px;line-height:1.5;color:#33392f}
.note b{font:700 9.5px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sage);display:block;margin-bottom:6px}
.sw{display:grid;grid-template-columns:repeat(6,1fr);gap:14px 14px}
.sw .t{display:flex;flex-direction:column;gap:6px}
.sw img{width:100%;aspect-ratio:1/1;object-fit:cover;border:1px solid var(--line)}
.sw h4{margin:0;font:700 11px/1.2 var(--sans)}
.sw .br{font-size:10.5px;color:var(--gold);font-style:italic;font-family:var(--serif);font-size:13px;line-height:1.1}
.sw .sp{font-size:10px;color:var(--muted);line-height:1.35}
.list{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:7px;font-size:12px;line-height:1.4}
.list li{padding-left:16px;position:relative}
.list li:before{content:"";position:absolute;left:0;top:7px;width:7px;height:1px;background:var(--gold)}
.kv{display:grid;grid-template-columns:1fr auto;font-size:12px;border-top:1px solid var(--line)}
.kv div{padding:6px 0;border-bottom:1px solid var(--line)}
.kv div:nth-child(2n){text-align:right;font-variant-numeric:tabular-nums;font-weight:700}
"""


def page(n, eyebrow, title, sub, inner, footer=True):
    f = (f'<div class="foot"><span>Brazilian Modern Homes / Casa 01 concept design</span><span>{n:02d}</span></div>'
         if footer else "")
    return (f'<section class="page"><div class="bar"></div><div class="head"><div class="eyebrow">{eyebrow}</div>'
            f'<h2>{title}</h2><div class="sub">{sub}</div><div class="rule"></div></div>'
            f'<div class="body">{inner}</div>{f}</section>')


def fig(src, cap_b, cap):
    return (f'<figure><div class="ph"><img class="fill" src="{src}" alt="{html.escape(cap_b)}"></div>'
            f'<figcaption><b>{cap_b}</b>{cap}</figcaption></figure>')


def bleed(n, src, eyebrow, title, text, callouts=()):
    co = "".join(f"<span>{c}</span>" for c in callouts)
    return (f'<section class="page bleed"><img src="{src}" alt="{html.escape(title)}">'
            f'<div class="label"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{text}</p></div>'
            f'<div class="callouts">{co}</div></section>')


def build_print(img):
    P = []
    hero = img.get("street", "")
    P.append(f'''<section class="page cover"><div class="panel"><div class="eyebrow">Concept design package / November 2026</div>
<div class="goldrule"></div><h1>Casa 01<br>Casa Pátio</h1><div class="tagline">Brazilian modern for Austin</div>
<p>A 1,620 sf, three-bedroom courtyard house. One thin roof, one private garden, and one limestone wall, built with ordinary Texas framing.</p>
<div class="bottom">Brazilian soul. Texas materials.<br>Renders + plans + finishes</div></div>
<div style="position:relative"><img class="fill" src="{hero}" alt="Casa 01 street view"></div></section>''')
    facts = "".join(f'<div><div class="n">{a}</div><div class="l">{b}</div></div>' for a, b in FACTS)
    moves = "".join(f'<div class="move"><div class="k">{i + 1}</div><div><h3>{t}</h3><p>{p}</p></div></div>'
                    for i, (t, p) in enumerate(MOVES))
    P.append(page(2, "01 / The idea", "Three moves make the house",
                  "Everything else is deliberately ordinary, so the money goes where you can see it.",
                  f'''<div style="display:grid;grid-template-columns:440px 1fr;gap:28px;height:100%">
<div style="display:flex;flex-direction:column;gap:22px"><div class="moves">{moves}</div><div class="facts">{facts}</div></div>
<figure style="margin:0;display:flex;flex-direction:column;gap:8px;min-height:0"><div style="flex:1;min-height:0;overflow:hidden"><img class="fill" src="{img.get("aerial", "")}" alt="Aerial view"></div>
<figcaption><b>Aerial</b>The L-shaped plan wraps the pátio. The roof plate covers the entry and veranda; the courtyard stays open to the sky.</figcaption></figure></div>'''))
    P.append(bleed(3, img.get("street", ""), "02 / Street", "A long, low line on the street",
                   "Limestone wall, cedar gate, cobogó screen, under one 54-foot roof edge. Front yard: decomposed "
                   "granite, agave, sotol and Mexican feather grass. No lawn to water.",
                   ["Lueders limestone ashlar", "Cedar slat pivot gate", "12x12 concrete cobogó", "15\" dark bronze fascia"]))
    P.append(bleed(4, img.get("street_dusk", ""), "03 / Dusk", "The screen turns into a lantern",
                   "Courtyard lights wash the inside face of the cobogó, so the circles glow at night. In-grade "
                   "grazers rake the limestone. Low path lights mark the stepping slabs.",
                   ["Courtyard backlight through cobogó", "2700K in-grade grazers"]))
    P.append(page(5, "04 / Arrival", "You enter through the garden",
                  "Through the gate, under a cedar canopy, past the pátio to a cedar pivot door.",
                  f'<div class="two">{fig(img.get("entry", ""), "Covered entry", "Sun through the cobogó draws circles on the limestone pavers. The front door is on the left, inside the screen.")}'
                  f'{fig(img.get("courtyard", ""), "Pátio", "Dwarf palmetto, ferns and muhly grass under a limbed-up oak. The gallery glass (right) lines the whole garden.")}</div>'))
    P.append(bleed(6, img.get("interior", ""), "05 / Great room", "One room between two gardens",
                   "Dining and living open south to the pátio and north to the veranda. Cedar ceiling, polished "
                   "concrete floor, warm-white walls: three materials do most of the work.",
                   ["Cedar T&G ceiling", "Polished concrete slab", "Leather + linen + walnut"]))
    P.append(page(7, "06 / Interiors", "Kitchen and gallery",
                  "Light oak, black stone and one green tile: a Brazilian palette with materials stocked in Austin.",
                  f'<div class="two">{fig(img.get("kitchen", ""), "Kitchen", "Rift white oak cabinets, honed black granite island with waterfall ends, green glazed tile backsplash, open shelf.")}'
                  f'{fig(img.get("gallery", ""), "Gallery", "The bedroom hall is a 30-foot glass wall on the pátio. Bedrooms open off it; the front door is at the far end.")}</div>'))
    P.append(page(8, "07 / Veranda", "Outdoor living under the oak",
                  "276 sf covered, north-facing, with a limestone grill counter and two ceiling fans.",
                  f'<div class="two">{fig(img.get("veranda", ""), "Veranda", "The great room ceiling continues outside as the soffit. Teak table for eight, churrasqueira at the far end.")}'
                  f'{fig(img.get("rear", ""), "Rear yard", "The house sits forward on the lot to protect the heritage live oak. Buffalo grass and native beds behind.")}</div>'))
    site = [("Lot", "65' x 125' (8,125 sf)"), ("Zoning (assumed)", "SF-3, central Austin"),
            ("Setbacks", "25' front / 5' side / 10' rear"), ("Conditioned", f"{A['conditioned']:,.0f} sf"),
            ("Roof incl. eaves + veranda", f"{A['roof']:,.0f} sf"),
            ("Building cover (approx.)", f"{(A['roof']) / A['lot'] * 100:.0f}% of lot (40% max)"),
            ("Parking", "Ribbon pad, east side"), ("Trees", "Heritage oak kept; house pulled forward")]
    kv = "".join(f"<div>{a}</div><div>{b}</div>" for a, b in site)
    P.append(page(9, "08 / Site", "Site plan",
                  "Typical central-Austin infill lot. Street to the south, pátio and veranda to the private sides.",
                  f'''<div style="display:grid;grid-template-columns:1fr 380px;gap:26px;height:100%;grid-template-rows:minmax(0,1fr)"><div class="dwgwrap">{svg_inline("01_site_plan.svg")}</div>
<div class="side"><div class="kv">{kv}</div><div class="note"><b>Check before design development</b>Zoning, impervious cover, tree ordinance and utility locations must be confirmed for the actual lot. Numbers here assume a generic SF-3 lot.</div></div></div>'''))
    rr = "".join(f"<tr><td>{a}</td><td>{b}</td><td class='num'>{c}</td></tr>" for a, b, c in room_rows())
    P.append(page(10, "09 / Plan", "Floor plan",
                  "Bedroom wing to the west, living bar to the north, pátio in the corner they make.",
                  f'''<div style="display:grid;grid-template-columns:1fr 330px;gap:22px;height:100%;grid-template-rows:minmax(0,1fr)"><div class="dwgwrap" style="padding:4px">{svg_inline("02_floor_plan.svg")}</div>
<div class="side"><table><tr><th>Room</th><th>Clear size</th><th style="text-align:right">sf</th></tr>{rr}</table>
<div class="kv"><div>Conditioned (gross)</div><div>{A["conditioned"]:,.0f} sf</div><div>Veranda (covered)</div><div>{A["veranda"]:.0f} sf</div><div>Pátio + covered entry</div><div>{A["courtyard"]:.0f} sf</div></div></div></div>'''))
    P.append(page(11, "10 / Elevations", "Street and garden elevations",
                  "South (street) above, north (veranda) below. One roof height everywhere: 12'-3\" to the top of the fascia.",
                  f'''<div style="display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:14px;height:100%"><div class="dwgwrap">{svg_inline("03_elevation_south.svg")}</div><div class="dwgwrap">{svg_inline("04_elevation_north.svg")}</div></div>'''))
    P.append(page(12, "10 / Elevations", "Side elevations",
                  "East (cedar screen to the driveway) above, west (quiet side, solid against afternoon sun) below.",
                  f'''<div style="display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:14px;height:100%"><div class="dwgwrap">{svg_inline("05_elevation_east.svg")}</div><div class="dwgwrap">{svg_inline("06_elevation_west.svg")}</div></div>'''))
    cl = "".join(f'<div class="move"><div class="k">{i + 1}</div><div><h3>{t}</h3><p>{p}</p></div></div>'
                 for i, (t, p) in enumerate(CLIMATE))
    P.append(page(13, "11 / Section + climate", "Section A-A: built for Austin sun",
                  "Cut north-south through the entry, pátio, great room and veranda, looking west.",
                  f'''<div style="display:grid;grid-template-columns:1fr 330px;gap:22px;height:100%;grid-template-rows:minmax(0,1fr)"><div class="dwgwrap">{svg_inline("07_section_aa.svg")}</div><div class="moves">{cl}</div></div>'''))
    P.append(page(14, "12 / Signature detail", "The cobogó block",
                  "One custom-looking block, made from standard precast. The circles complete across the joints.",
                  f'''<div style="display:grid;grid-template-columns:1fr 360px;gap:24px;height:100%;grid-template-rows:minmax(0,1fr)"><div class="dwgwrap">{svg_inline("08_cobogo_detail.svg")}</div>
<div class="side"><figure style="margin:0;display:flex;flex-direction:column;gap:8px;height:300px"><div style="flex:1;overflow:hidden"><img class="fill" src="{img.get("entry", "")}" alt="Cobogó in light" style="object-position:12% 50%"></div><figcaption><b>In light</b>Morning and winter sun cast the pattern onto the pavers.</figcaption></figure>
<div class="note"><b>Sourcing</b>US-made breeze blocks come in circle patterns close to this one. A precaster can also cast a custom mold for 210 blocks. Get both prices.</div></div></div>'''))
    sw = "".join(f'''<div class="t"><img src="{img.get("sw_" + k, "")}" alt="{n}"><h4>{n}</h4><div class="br">{br}</div><div class="sp">{sp}</div></div>'''
                 for k, n, br, sp in SWATCHES)
    P.append(page(15, "13 / Finishes", "Finish board",
                  "Each tile is rendered with the same material used in the renders. Gold italics: the Brazilian reference it replaces.",
                  f'<div class="sw">{sw}</div>'))
    q = "".join(f"<tr><td>{a}</td><td class='num'>{b}</td><td>{c}</td></tr>" for a, b, c in quantities())
    conv = "".join(f"<li>{c}</li>" for c in CONVENTIONAL)
    lo, hi = 325 * A["conditioned"], 425 * A["conditioned"]
    P.append(page(16, "14 / For the builder", "Quantities and planning budget",
                  "Counts come straight from the 3D model, so a builder can price the signature elements early.",
                  f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:28px;height:100%">
<div><table><tr><th>Signature element</th><th style="text-align:right">Qty</th><th>Notes</th></tr>{q}</table></div>
<div class="side"><div><div class="eyebrow" style="margin-bottom:8px">Kept conventional</div><ul class="list">{conv}</ul></div>
<div class="kv"><div>Construction at $325–$425 / sf</div><div>${lo / 1000:,.0f}K–${hi / 1000:,.0f}K</div>
<div>Site work + utilities</div><div>$20K–$50K</div><div>Design, engineering, permits</div><div>$25K–$50K</div>
<div>Contingency (~10%)</div><div>${lo * 0.1 / 1000:,.0f}K–${hi * 0.1 / 1000:,.0f}K</div>
<div>Total, excluding land</div><div>${(lo * 1.1 + 45000) / 1000:,.0f}K–${(hi * 1.1 + 100000) / 1000:,.0f}K</div></div>
<div class="note"><b>Planning numbers, not bids</b>Ranges carry over from the earlier feasibility notes. Next step: price these quantities with two Austin builders, then adapt the plan to a real lot.</div></div></div>'''))
    return P


def write_print(img):
    pages = build_print(img)
    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Casa 01 Lookbook</title>'
           f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    out = os.path.join(HERE, "print.html")
    open(out, "w").write(doc)
    return out


if __name__ == "__main__":
    img = prep_images()
    print("images:", sorted(img))
    print(write_print(img))
    import webpage
    print(webpage.write_web(img))
