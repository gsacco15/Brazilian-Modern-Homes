"""Build the Casa 01 lookbook (print HTML -> PDF, and a web page) from the
renders, the SVG drawings and design.py.

    python3 casa01/lookbook/build.py
    node casa01/lookbook/make_pdf.js
"""
import html
import json
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

VIEWS = ["street", "street_dusk", "gate", "entry", "courtyard", "interior", "kitchen", "gallery", "veranda", "rear",
         "aerial", "bath", "bath2"]
ORTHO_VIEWS = ["plan_render", "site_render", "elev_s", "elev_n", "elev_e", "elev_w"]
SWATCHES = [
    ("limestone", "Lueders limestone", "Pedra São Tomé / moledo", "Sawn-face ashlar, 3 course heights"),
    ("cobogo", "Concrete cobogó", "Cobogó, Recife 1929", "12x12x4 precast, white cement"),
    ("cedar_z", "Western red cedar", "Freijó / ipê", "Clear T&G soffits, 2x4 slats, natural oil"),
    ("stucco", "Warm-white stucco", "White mineral plaster", "Smooth 3-coat, sand finish"),
    ("floor", "Polished concrete", "Cimento queimado", "Slab-on-grade, light grind + seal"),
    ("pavers", "Limestone pavers", "São Tomé paving", "24x36 thermal-finish, courtyard + veranda"),
    ("oak", "Rift white oak", "Tauari interiors", "Kitchen cabinets, credenza, desks"),
    ("granite", "Honed black granite", "Brazilian dark stone", "Island + counters, 1.5\" honed"),
    ("tile", "Green glazed tile", "Azulejo", "4x4 handmade-look backsplash; zellige-look in the baths"),
    ("bronze", "Dark bronze aluminum", "Slim steel frames", "Fascia, window frames, posts"),
    ("dg", "Decomposed granite", "Terra batida", "Stabilized paths, meadow mulch"),
    ("calcada", "Black stone mosaic", "Calçada portuguesa", "50 sf at the entry, light concrete band"),
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
    s = open(os.path.join(DRAW, name)).read().replace("__IMG__", "img/ortho")
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
    os.makedirs(os.path.join(IMG, "ortho"), exist_ok=True)
    for v in ORTHO_VIEWS:
        src = os.path.join(RENDERS, "ortho", f"{v}.png")
        if not os.path.exists(src):
            continue
        dst = os.path.join(IMG, "ortho", f"{v}.jpg")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            im = Image.open(src).convert("RGBA")
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            Image.alpha_composite(bg, im).convert("RGB").save(dst, quality=85, optimize=True, progressive=True)
        have["ortho_" + v] = f"img/ortho/{v}.jpg"
    for key, *_ in SWATCHES:
        src = os.path.join(RENDERS, "swatches", f"{key}.png")
        if os.path.exists(src):
            dst = os.path.join(IMG, f"sw_{key}.jpg")
            Image.open(src).convert("RGB").resize((360, 360), Image.LANCZOS).save(dst, quality=88)
            have["sw_" + key] = f"img/sw_{key}.jpg"
    return have


def quantities():
    c = D.COBOGO
    em = D.ENTRY_MOSAIC
    mos = (em["x1"] - em["x0"] - 2 * em["band"]) * (em["y1"] - em["y0"] - 2 * em["band"])
    nx, nz = int(c["x1"] - c["x0"]), int(c["z1"] - c["z0"])
    lw = D.LIMESTONE_WALL
    win = D.EXT_WALLS[0]["openings"][0]
    lime = (lw["x1"] - lw["x0"]) * (lw["z1"] - lw["z0"]) - win["w"] * (win["head"] - win["sill"])
    soffit = sum((z["x1"] - z["x0"]) * (z["y1"] - z["y0"]) for z in D.CEDAR_SOFFITS)
    ceil = sum((z["x1"] - z["x0"]) * (z["y1"] - z["y0"]) for z in D.CEDAR_CEILINGS)
    s = D.CEDAR_SCREEN
    run = (s["y1"] - s["y0"]) - sum(b - a for a, b in s.get("openings", []))
    run += sum((sc.get("x1", 0) - sc.get("x0", 0)) if sc["axis"] == "x" else (sc["y1"] - sc["y0"])
               for sc in getattr(D, "SLAT_SCREENS", []))
    slats = int(run / (s["slat_w"] + s["gap"]))
    area = D.area_schedule()
    sl = getattr(D, "CARPORT_SLIDER", None)
    sk = getattr(D, "SKYLIGHTS", [])
    ndoors = sum(1 for p in D.PARTITIONS for o in p["openings"])
    sliders = [o for w in D.EXT_WALLS for o in w["openings"] if o["kind"] == "slider"]
    windows = [o for w in D.EXT_WALLS for o in w["openings"] if o["kind"] in ("fixed", "casement")]
    glass_lf = sum(o["w"] for o in sliders)
    return [
        ("Cobogó screen", f"{nx * nz} blocks", f"{nx} x {nz} courses, {nx * nz} sf, on cast curb"),
        ("Limestone feature wall", f"{lime:.0f} sf", f"{lw['x1'] - lw['x0']:.1f}' long x {lw['z1']:.0f}' high, one slot window"),
        ("Cedar soffits (outside)", f"{soffit:.0f} sf", "Entry canopy, courtyard eaves, veranda"),
        ("Cedar ceilings (inside)", f"{ceil:.0f} sf", "Great room only, same boards as the soffits"),
        ("Cedar slat screens", f"{slats} slats", f"2x4 @ 5\" o.c., {run:.0f}' run x 10' high, carport + pátio sides"),
        ("Sliding glass walls", f"{len(sliders)} units", f"{glass_lf:.1f} lf total, stock sizes, 9'-0\" tall, dark bronze"),
        ("Carport", f"{area.get('carport', 0):,.0f} sf", "Slab at the courtyard level under the main roof; one car"),
        ("Sliding cedar carport gate", "1 (option)" if sl else "—",
         f"{(sl['x1'] - sl['x0']):.0f}' wide, motorized; track strip, pad + conduit in the base" if sl else ""),
        ("Skylights", f"{len(sk)} units", "Fixed, laminated low-E: primary shower, hall bath tub, walk-in"),
        ("Interior doors", f"{ndoors} openings", "Rift oak veneer, solid core, brass levers; bypass closets"),
        ("Windows", f"{len(windows)} units", "Casements (egress) + fixed slot / clerestory / kitchen"),
        ("Roof plate", f"{D.poly_area(D.ROOF):,.0f} sf", f"Low-slope TPO, {perim(D.ROOF):.0f} lf of 15\" bronze fascia"),
        ("Steel posts", f"{len(D.POSTS)} posts", "4\" square HSS, dark bronze"),
        ("Entry calçada portuguesa", f"{mos:.0f} sf", "Black basalt mosaic or Antika Onyx Black, 6\" concrete band"),
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
    ("One thin roof", "A single 15-inch roof edge runs the full 57-foot street front. Bedrooms, entry canopy and "
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
.facts div{flex:1;padding:12px 8px;border-left:1px solid var(--line);min-width:0}
.facts div:first-child{border-left:0;padding-left:0}
.facts .n{font-family:var(--serif);font-size:26px;line-height:1;white-space:nowrap}
.facts .l{font:700 8.5px/1.25 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:6px}
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
.sheetpage{background:#fff}
.sheet{position:absolute;left:22px;right:22px;top:20px;bottom:22px;border:1.6px solid var(--ink);display:grid;grid-template-columns:minmax(0,1fr) 196px}
.draw{position:relative;padding:14px 16px;min-width:0;min-height:0;display:flex;gap:16px}
.frame{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px;min-height:0}
.frame .dwgwrap{border:0;flex:1}
.dtitle{display:flex;align-items:center;gap:10px;border-top:1.6px solid var(--ink);padding-top:6px;font:700 11px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase}
.dtitle .no{width:24px;height:24px;border:1.5px solid var(--ink);border-radius:50%;display:grid;place-items:center;font:900 11px/1 var(--sans)}
.dtitle .sc{margin-left:auto;font-weight:400;color:var(--muted);letter-spacing:.06em}
.tb{border-left:1.6px solid var(--ink);display:flex;flex-direction:column;font-size:11px}
.tb>div{padding:10px 12px;border-bottom:1px solid var(--ink)}
.tb-brand{font:900 12.5px/1.2 var(--sans);letter-spacing:.16em;background:var(--ink);color:#f3efe4}
.tb-brand small{display:block;font:700 9px/1.4 var(--sans);letter-spacing:.14em;color:#cdbb92;margin-top:4px}
.tb-proj{font-family:var(--serif);font-size:21px;line-height:1.05}
.tb-proj span{display:block;font:700 9.5px/1.6 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.tb-k{font:700 8.5px/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.tb-v{font:700 11.5px/1.3 var(--sans);margin:2px 0 8px}
.tb-side{flex:1;overflow:hidden}
.tb-num{font:900 34px/1 var(--sans);letter-spacing:.02em}
.tb-num small{display:block;font:700 8.5px/1.4 var(--sans);letter-spacing:.14em;color:var(--muted)}
.tb-note{font:700 8.5px/1.4 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#a0472f;border-bottom:0!important}
.sched{font-size:9.5px}
.sched th{font-size:8px;padding:5px 5px}
.sched td{padding:4px 5px}
.code{display:inline-grid;place-items:center;width:20px;height:20px;border:1.3px solid var(--ink);border-radius:50%;font:900 8.5px/1 var(--sans)}
"""


def page(n, eyebrow, title, sub, inner, footer=True):
    f = (f'<div class="foot"><span>Brazilian Modern Homes / Casa 01 concept design</span><span>{n:02d}</span></div>'
         if footer else "")
    return (f'<section class="page"><div class="bar"></div><div class="head"><div class="eyebrow">{eyebrow}</div>'
            f'<h2>{title}</h2><div class="sub">{sub}</div><div class="rule"></div></div>'
            f'<div class="body">{inner}</div>{f}</section>')


def sheet(n, code, title, scale, inner, side=""):
    return (f'<section class="page sheetpage"><div class="sheet"><div class="draw">{inner}</div>'
            f'<aside class="tb"><div class="tb-brand">BRAZILIAN MODERN HOMES<small>RESIDENTIAL DESIGN · AUSTIN</small></div>'
            f'<div class="tb-proj">Casa 01<br>Casa Pátio<span>Central Austin, Texas</span></div>'
            f'<div class="tb-side">{side}</div>'
            f'<div><div class="tb-k">Sheet title</div><div class="tb-v">{title}</div><div class="tb-k">Scale</div>'
            f'<div class="tb-v">{scale}</div><div class="tb-k">Date / Phase</div><div class="tb-v">Nov 2026 · Concept</div></div>'
            f'<div class="tb-num"><small>SHEET</small>{code}</div><div class="tb-note">Concept design. Not for construction.</div>'
            f'</aside></div><div class="foot" style="bottom:6px"><span></span><span>{n:02d}</span></div></section>')


def frame(svgname, no, title, scale, style=""):
    return (f'<div class="frame" style="{style}"><div class="dwgwrap">{svg_inline(svgname)}</div>'
            f'<div class="dtitle"><span class="no">{no}</span>{title}<span class="sc">{scale}</span></div></div>')


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
<p>A {A["conditioned"]:,.0f} sf, three-bedroom courtyard house with a covered carport. One thin roof, one private garden, and one limestone wall, built with ordinary Texas framing.</p>
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
                   "Limestone wall, cedar pivot gate, cobogó screen and a sliding cedar carport gate, under one "
                   "57-foot roof edge. The car is never part of the facade. Front yard: decomposed granite, agave, "
                   "sotol and Mexican feather grass. No lawn to water.",
                   ["Lueders limestone ashlar", "Cedar slat pivot gate", "12x12 concrete cobogó",
                    "Sliding cedar carport gate (option)", "15\" dark bronze fascia"]))
    P.append(bleed(4, img.get("street_dusk", ""), "03 / Dusk", "The screen turns into a lantern",
                   "Courtyard lights wash the inside face of the cobogó, so the circles glow at night, and the "
                   "carport lights glow through the gate slats. In-grade grazers rake the limestone. Low path lights "
                   "mark the stepping slabs.",
                   ["Courtyard backlight through cobogó", "2700K in-grade grazers"]))
    P.append(page(5, "04 / Arrival", "You enter through the garden",
                  "On foot through the cedar gate, by car through a cedar side gate from the carport: both land in "
                  "the covered entry, on one level, at the cedar pivot door.",
                  f'<div class="two">{fig(img.get("gate", img.get("courtyard", "")), "Through the main gate", "Step in and the pátio opens to the right under the oak; the front door is on your left, inside the screen. The carport side gate is at the far end.")}'
                  f'{fig(img.get("entry", ""), "Covered entry", "Black calçada underfoot, the cobogó beside you, the cedar pivot door ahead. Sun through the screen draws circles on the pavers.")}</div>'))
    P.append(bleed(6, img.get("courtyard", ""), "05 / Pátio", "One garden, open to the sky",
                   f"The pátio wraps behind the carport to the primary bedroom: {A['courtyard']:.0f} sf with the "
                   "covered entry. Dwarf palmetto, ferns and muhly under a limbed-up oak; cedar slats on the carport "
                   "sides, and a slat screen on the east edge lets the morning light in.",
                   ["One L-shaped courtyard", "Cedar slat screens", "Limbed-up oak, native shade garden"]))
    P.append(bleed(7, img.get("interior", ""), "06 / Great room", "One room between two gardens",
                   "Dining and living open south to the pátio and north to the veranda. Cedar ceiling, polished "
                   "concrete floor, warm-white walls: three materials do most of the work. A low walnut-framed "
                   "sofa with loose linen cushions faces the room.",
                   ["Cedar T&G ceiling", "Polished concrete slab", "Walnut + linen + leather"]))
    P.append(page(8, "07 / Interiors", "Kitchen and gallery",
                  "Light oak, black stone and one green tile: a Brazilian palette with materials stocked in Austin.",
                  f'<div class="two">{fig(img.get("kitchen", ""), "Kitchen", "Rift white oak cabinets, honed black granite island with waterfall ends, green glazed tile backsplash, open shelf.")}'
                  f'{fig(img.get("gallery", ""), "Gallery", "The bedroom hall is a 30-foot glass wall on the pátio. Rift-oak doors open off it to the bedrooms and the hall bath; the front door is at the far end.")}</div>'))
    P.append(page(9, "08 / Veranda", "Outdoor living under the oak",
                  "276 sf covered, north-facing, with a limestone grill counter and two ceiling fans.",
                  f'<div class="two">{fig(img.get("veranda", ""), "Veranda", "The great room ceiling continues outside as the soffit. Teak table for eight, churrasqueira at the far end.")}'
                  f'{fig(img.get("rear", ""), "Rear yard", "The house sits forward on the lot to protect the heritage live oak. Buffalo grass and native beds behind.")}</div>'))
    n = 10
    if img.get("bath"):
        bf = "".join(f"<tr><td>{a}</td><td><i>{b}</i></td><td>{c}</td></tr>" for a, b, c in D.BATH_FINISHES)
        P.append(page(n, "09 / Primary bath", "A spa-style wet room",
                      "7'-10\" square: a curbless walk-in shower with a skylight in the middle, floating oak vanity, "
                      "honed concrete floor.",
                      f'''<div style="display:grid;grid-template-columns:1fr 400px;gap:24px;height:100%;grid-template-rows:minmax(0,1fr)">
<figure style="margin:0;display:flex;flex-direction:column;gap:8px;min-height:0"><div style="flex:1;min-height:0;overflow:hidden"><img class="fill" src="{img["bath"]}" alt="Primary bath render"></div>
<figcaption><b>Primary bath</b>Green zellige-look tile to the ceiling, a fixed glass panel, brass rain head, limestone bench, a skylight overhead and a garden window into a fenced side yard.</figcaption></figure>
<div class="side"><div class="dwgwrap" style="height:300px">{svg_inline("09_bath_plan.svg")}</div>
<table class="sched"><tr><th>Element</th><th>Brazilian ref.</th><th>Austin spec</th></tr>{bf}</table></div></div>'''))
        n += 1
    if img.get("bath2"):
        P.append(page(n, "10 / Hall bath", "The house's one tub, done like the primary",
                      "Terracotta instead of green, the same oak, brass and stone. A fixed glass panel, no curtain, "
                      "and a skylight over the tub.",
                      f'''<div style="display:grid;grid-template-columns:1fr 400px;gap:24px;height:100%;grid-template-rows:minmax(0,1fr)">
<figure style="margin:0;display:flex;flex-direction:column;gap:8px;min-height:0"><div style="flex:1;min-height:0;overflow:hidden"><img class="fill" src="{img["bath2"]}" alt="Hall bath render"></div>
<figcaption><b>Hall bath</b>Terracotta zellige-look tile to the ceiling around the tub, a tiled niche, open oak shelves, a pill mirror with brass sconces and a rectangular vessel on limestone.</figcaption></figure>
<div class="side"><div class="dwgwrap" style="height:300px">{svg_inline("10_hall_bath_plan.svg")}</div>
<div class="note"><b>A per-client swap</b>Clients without small children can trade the tub for a walk-in shower like the primary's in the same footprint (about +$2–4K). Floors stay concrete either way.</div></div></div>'''))
        n += 1
    if img.get("ortho_site_render"):
        rows = json.load(open(os.path.join(DRAW, "plant_schedule.json")))
        tr = "".join(f"<tr><td><span class='code'>{c}</span></td><td><b>{cm}</b><br><i>{bt}</i></td><td>{sz}</td>"
                     f"<td class='num'>{q if q else 'area'}</td><td>{w}</td></tr>" for c, cm, bt, sz, w, nt, q in rows)
        P.append(sheet(n, "L-100", "Landscape plan", "1\" = 20'-0\" (approx.)",
                       frame("21_landscape_plan.svg", 1, "Landscape plan", "Graphic scale") +
                       f'''<div style="width:470px;display:flex;flex-direction:column;gap:10px"><div class="eyebrow">Plant schedule</div>
<table class="sched"><tr><th>Key</th><th>Plant</th><th>Size</th><th style="text-align:right">Qty</th><th>Water</th></tr>{tr}</table>
<div class="note"><b>Planting intent</b>Xeriscape front meadow on decomposed granite, a shady tropical-looking pátio of native palmetto and fern, buffalo-grass lawn under the heritage oak. Drip irrigation on a smart controller; check plant choices against Austin's Grow Green guide.</div></div>''',
                       side='<div class="tb-k">Legend</div><div class="tb-v">Codes match the schedule. Lot line dashed white, setbacks dashed gold.</div>'))
        n += 1
    if img.get("ortho_plan_render"):
        rr = "".join(f"<tr><td>{a}</td><td>{b}</td><td class='num'>{c}</td></tr>" for a, b, c in room_rows())
        P.append(sheet(n, "A-100", "Rendered floor plan", "1/8\" = 1'-0\" (approx.)",
                       frame("20_plan_rendered.svg", 1, "Floor plan, rendered", "Cut at 5'-6\" above floor") +
                       f'''<div style="width:380px;display:flex;flex-direction:column;gap:10px"><div class="eyebrow">Room schedule</div>
<table class="sched"><tr><th>Room</th><th>Clear size</th><th style="text-align:right">sf</th></tr>{rr}</table>
<div class="kv"><div>Conditioned (gross)</div><div>{A["conditioned"]:,.0f} sf</div><div>Veranda (covered)</div><div>{A["veranda"]:.0f} sf</div><div>Pátio + covered entry</div><div>{A["courtyard"]:.0f} sf</div></div></div>'''))
        n += 1
    sch = json.load(open(os.path.join(DRAW, "schedules.json")))
    dr = "".join(f"<tr><td><span class='code'>{d['tag']}</span></td><td>{d['name']}</td><td>{ft(d['w'])} x {ft(d['h'])}</td>"
                 f"<td>{d['type']}</td></tr>" for d in sch["doors"])
    wgroups = {}
    for w in sch["windows"]:
        g = wgroups.setdefault(w["tag"], dict(w=w["w"], h=w["h"], sill=w["sill"], kind=w["kind"], names=[]))
        g["names"].append(w["name"])
    wr = "".join(f"<tr><td><b>{t}</b></td><td class='num'>{len(g['names'])}</td><td>{ft(g['w'])} x {ft(g['h'])}</td>"
                 f"<td>{'sliding' if g['kind'] == 'slider' else g['kind']}</td><td>{ft(g['sill']) if g['sill'] else '–'}</td></tr>"
                 for t, g in sorted(wgroups.items()))
    kn = "".join(f"<div style='display:grid;grid-template-columns:18px 1fr;gap:4px;font-size:8.5px;line-height:1.25;margin-bottom:3px'>"
                 f"<b>{i + 1}</b><span>{k}</span></div>" for i, k in enumerate(sch["keynotes"]))
    P.append(sheet(n, "A-101", "Floor plan", "1/8\" = 1'-0\" (approx.)",
                   frame("30_floor_plan_cd.svg", 1, "Floor plan", "Graphic scale") +
                   f'''<div style="width:400px;display:flex;flex-direction:column;gap:8px;min-height:0">
<div class="eyebrow">Door schedule</div><table class="sched"><tr><th>No.</th><th>Location</th><th>Size</th><th>Type</th></tr>{dr}</table>
<div class="eyebrow" style="margin-top:4px">Window schedule</div><table class="sched"><tr><th>Mark</th><th style="text-align:right">Qty</th><th>Size</th><th>Type</th><th>Sill</th></tr>{wr}</table></div>''',
                   side=f'<div class="tb-k" style="margin-bottom:6px">Keynotes</div>{kn}'))
    n += 1
    P.append(sheet(n, "A-102", "Roof plan + site plan", "As noted",
                   frame("31_roof_plan_cd.svg", 1, "Roof plan", "1/16\" = 1'-0\" (approx.)") +
                   frame("01_site_plan.svg", 2, "Site plan", "1\" = 30'-0\" (approx.)", style="flex:0 0 360px")))
    n += 1
    if img.get("ortho_elev_s"):
        P.append(sheet(n, "A-200", "Elevations, rendered", "1/8\" = 1'-0\" (approx.)",
                       '<div style="flex:1;display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:10px;min-width:0">' +
                       frame("22_elev_s.svg", 1, "South elevation (street)", "Rendered") +
                       frame("22_elev_n.svg", 2, "North elevation (veranda)", "Rendered") + "</div>"))
        n += 1
        P.append(sheet(n, "A-201", "Elevations, rendered", "1/8\" = 1'-0\" (approx.)",
                       '<div style="flex:1;display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:10px;min-width:0">' +
                       frame("22_elev_e.svg", 3, "East elevation", "Rendered") +
                       frame("22_elev_w.svg", 4, "West elevation", "Rendered") + "</div>"))
        n += 1
    P.append(sheet(n, "A-202", "Exterior elevations", "1/8\" = 1'-0\" (approx.)",
                   '<div style="flex:1;display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:10px;min-width:0">' +
                   frame("32_elev_s_cd.svg", 1, "South elevation (street)", "Graphic scale") +
                   frame("33_elev_n_cd.svg", 2, "North elevation (veranda)", "Graphic scale") + "</div>"))
    n += 1
    P.append(sheet(n, "A-203", "Exterior elevations", "1/8\" = 1'-0\" (approx.)",
                   '<div style="flex:1;display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:10px;min-width:0">' +
                   frame("34_elev_e_cd.svg", 3, "East elevation", "Graphic scale") +
                   frame("35_elev_w_cd.svg", 4, "West elevation", "Graphic scale") + "</div>"))
    n += 1
    cl = "".join(f'<div class="move"><div class="k">{i + 1}</div><div><h3>{t}</h3><p>{p}</p></div></div>'
                 for i, (t, p) in enumerate(CLIMATE))
    P.append(sheet(n, "A-300", "Building section", "1/8\" = 1'-0\" (approx.)",
                   frame("07_section_aa.svg", 1, "Section A-A with Austin solstice sun", "Looking west") +
                   f'<div class="moves" style="width:300px">{cl}</div>'))
    n += 1
    P.append(sheet(n, "A-500", "Signature detail", "3\" = 1'-0\"",
                   frame("08_cobogo_detail.svg", 1, "Cobogó breeze block", "Block, section, tiled field") +
                   f'''<div class="side" style="width:300px"><figure style="margin:0;display:flex;flex-direction:column;gap:8px;height:300px"><div style="flex:1;overflow:hidden"><img class="fill" src="{img.get("entry", "")}" alt="Cobogó in light" style="object-position:12% 50%"></div><figcaption><b>In light</b>Morning and winter sun cast the pattern onto the pavers.</figcaption></figure>
<div class="note"><b>Sourcing</b>US-made breeze blocks come in circle patterns close to this one. A precaster can also cast a custom mold for {int(D.COBOGO["x1"] - D.COBOGO["x0"]) * int(D.COBOGO["z1"] - D.COBOGO["z0"])} blocks. Get both prices.</div></div>'''))
    n += 1
    sw = "".join(f'''<div class="t"><img src="{img.get("sw_" + k, "")}" alt="{n}"><h4>{n}</h4><div class="br">{br}</div><div class="sp">{sp}</div></div>'''
                 for k, n, br, sp in SWATCHES)
    P.append(page(n, "11 / Finishes", "Finish board",
                  "Each tile is rendered with the same material used in the renders. Gold italics: the Brazilian reference it replaces.",
                  f'<div class="sw">{sw}</div>'))
    q = "".join(f"<tr><td>{a}</td><td class='num'>{b}</td><td>{c}</td></tr>" for a, b, c in quantities())
    conv = "".join(f"<li>{c}</li>" for c in CONVENTIONAL)
    lo, hi = 325 * A["conditioned"], 425 * A["conditioned"]
    P.append(page(n + 1, "12 / For the builder", "Quantities and planning budget",
                  "Counts come straight from the 3D model, so a builder can price the signature elements early.",
                  f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:28px;height:100%">
<div><table><tr><th>Signature element</th><th style="text-align:right">Qty</th><th>Notes</th></tr>{q}</table></div>
<div class="side"><div><div class="eyebrow" style="margin-bottom:8px">Kept conventional</div><ul class="list">{conv}</ul></div>
<div class="kv"><div>Construction at $325–$425 / sf</div><div>${lo / 1000:,.0f}K–${hi / 1000:,.0f}K</div>
<div>Site work + utilities</div><div>$20K–$50K</div><div>Design, engineering, permits</div><div>$25K–$50K</div>
<div>Entry calçada allowance (designer)</div><div>$1K–$4.5K</div>
<div>Carport (slab, roof, posts, gate rough-in)</div><div>$15K–$25K</div>
<div>Contingency (~10%)</div><div>${lo * 0.1 / 1000:,.0f}K–${hi * 0.1 / 1000:,.0f}K</div>
<div>Total, excluding land</div><div>${(lo * 1.1 + 61000) / 1000:,.0f}K–${(hi * 1.1 + 129500) / 1000:,.0f}K</div>
<div>Option: sliding cedar carport gate</div><div>+$7K–$12K</div></div>
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
