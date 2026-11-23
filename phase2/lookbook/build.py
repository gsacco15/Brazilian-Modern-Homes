"""Phase 2 lookbook: Casa 02 + Casita, the duo and trio homes. Same template as the Casa 01 lookbook.

    python3 phase2/lookbook/build.py
    node phase2/lookbook/make_pdf.js            -> phase2/Phase2_Lookbook.pdf

Images: the high-detail renders (phase2/render/hifi), the Casa 01 material swatches (same materials), and the
plans and site plans drawn live from the model by the concept kit (phase2/concepts).
"""
import html
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
sys.path.insert(0, os.path.join(P2, "concepts"))
sys.path.insert(0, os.path.join(ROOT, "casa01", "lookbook"))
import concepts as C  # noqa: E402  (plans and site plans from the model)

H = C.H
IMG = os.path.join(HERE, "img")
RENDERS = os.path.join(P2, "render", "hifi")
SWATCH_SRC = os.path.join(ROOT, "casa01", "renders", "swatches")
VIEWS = ["duo_street", "duo_dusk", "duo_entry", "duo_garden", "trio_street", "trio_aerial"]

SWATCHES = [
    ("stucco", "Warm-white stucco", "White mineral plaster", "The upper floor and the walls"),
    ("cobogo", "Concrete cobogó", "Cobogó, Recife 1929", "12x12 blocks: the two-story lantern and the Casita's garden wall"),
    ("cedar_z", "Western red cedar", "Freijó / ipê", "Carport and garden gates, stair slats, soffits, the carport ceiling"),
    ("limestone", "Lueders limestone", "Pedra São Tomé / moledo", "Sawn-face ashlar, 3 course heights: the stone base and piers"),
    ("calcada", "Black stone mosaic", "Calçada portuguesa", "About 50 sf a home: carport rug, threshold, Casita stoop"),
    ("pavers", "Limestone pavers", "São Tomé paving", "24x36 thermal finish: terraces and stepping stones"),
    ("bronze", "Dark bronze aluminum", "Slim steel frames", "Window frames, the floor band, fascia, columns"),
    ("oak", "Rift white oak", "Tauari interiors", "Front doors, open stair treads, cabinets"),
    ("floor", "Polished concrete", "Cimento queimado", "Ground floors, slab on grade"),
    ("dg", "Decomposed granite", "Terra batida", "Front yards of agave, sotol and feather grass"),
]

A = H.area_summary()
FACTS = [(f"{A['carport_total']:,.0f}", "sf Casa 02 · 3 bed / 2.5 bath"), (f"{A['suite_total']:,.0f}", "sf with the suite · 3 + den"),
         (f"{A['casita']:,.0f}", "sf Casita · 1 bed + flex"), ("2–3", "homes on one lot"), ("50–65'", "typical Austin lots")]
MOVES = [
    ("Two or three homes, one lot", "Austin's HOME rules allow two or three homes on a standard lot. A pair of Casa 02s "
     "makes a duo; add the one-story Casita and it is a trio, on lots 50 to 65 feet wide."),
    ("One family of parts", "Casa 02 and the Casita share Casa 01's palette: white stucco, cedar slats, cobogó, "
     "Lueders limestone and black calçada. Two plans, mirrored and turned, fit every layout."),
    ("A lantern at the street", "A two-story cobogó screen stands over the front door and the stair landing. By day it "
     "shades and screens; at night the landing light turns it into a lantern."),
    ("A stone base, a floating white box", "The ground floor's outer side is limestone ashlar, with a stone pier at the "
     "carport corner; the white upper floor floats on a dark bronze band above it."),
]


# ---------------------------------------------------------------- helpers
def prep_images():
    os.makedirs(IMG, exist_ok=True)
    have = {}
    for v in VIEWS:
        src = os.path.join(RENDERS, f"{v}.png")
        if not os.path.exists(src):
            continue
        dst = os.path.join(IMG, f"{v}.jpg")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            Image.open(src).convert("RGB").save(dst, quality=88, optimize=True, progressive=True)
        have[v] = f"img/{v}.jpg"
    for k, *_ in SWATCHES:
        src = os.path.join(SWATCH_SRC, f"{k}.png")
        if os.path.exists(src):
            dst = os.path.join(IMG, f"sw_{k}.jpg")
            if not os.path.exists(dst):
                Image.open(src).convert("RGB").resize((360, 360)).save(dst, quality=86)
            have["sw_" + k] = f"img/sw_{k}.jpg"
    return have


def svg_fit(s):
    s = re.sub(r'(<svg[^>]*?) width="[\d.]+" height="[\d.]+"', r'\1', s, count=1)
    return s.replace("<svg ", '<svg class="dwg" preserveAspectRatio="xMidYMid meet" ', 1)


CSS = open(os.path.join(ROOT, "casa01", "lookbook", "build.py")).read().split('CSS = r"""')[1].split('"""')[0]
CSS = CSS.replace("url(fonts/", "url(../../casa01/lookbook/fonts/")
CSS += """
.bleed{background:#111}
.bleed img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.bleed .label{position:absolute;left:44px;bottom:40px;max-width:520px;background:rgba(246,244,238,.94);padding:22px 26px}
.bleed .label h2{font-size:34px}
.bleed .label p{margin:8px 0 0;font-size:13px;line-height:1.5;color:#3d433e}
.bleed .callouts{position:absolute;right:40px;bottom:40px;display:flex;flex-direction:column;gap:6px;align-items:flex-end}
.bleed .callouts span{background:rgba(29,37,32,.82);color:#f3efe4;font:700 10px/1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;padding:8px 10px}
.cover .panel h1{font-size:64px;line-height:.98;margin:18px 0 0}
.cover .goldrule{height:2px;width:64px;background:var(--gold);margin-top:18px}
.cover .tagline{font-family:var(--serif);font-style:italic;font-size:22px;color:#cdbb92;margin-top:16px}
.cover .bottom{position:absolute;left:54px;bottom:50px;font:700 10px/1.6 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#cdbb92}
.cover .eyebrow{color:#cdbb92}
.facts{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;border-top:1px solid var(--line);padding-top:14px}
.facts .n{font-family:var(--serif);font-size:32px;line-height:1}
.two{display:grid;grid-template-columns:1fr 1fr;gap:22px;height:100%}
figure{margin:0;display:flex;flex-direction:column;gap:8px;min-height:0}
figure .ph{flex:1;min-height:0;overflow:hidden}
figcaption{font-size:12px;color:var(--muted);line-height:1.45}
figcaption b{display:block;font:700 11px/1.3 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:3px}
.plans{display:grid;grid-template-columns:1fr 1fr 1fr 1.15fr;gap:14px;height:100%}
.plans .p{display:flex;flex-direction:column;gap:6px;min-height:0}
.plans .dwgwrap{flex:1}
.plans h4,.lay h4{margin:0;font:700 11px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase}
.plans small,.lay small{font-size:10.5px;color:var(--muted);line-height:1.35}
.lay{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;height:100%}
.lay .p{display:flex;flex-direction:column;gap:6px;min-height:0}
.lay .dwgwrap{flex:1}
.sw{grid-template-columns:repeat(5,1fr)!important;gap:16px 18px!important}
.sw img{aspect-ratio:1.35/1!important}
"""


def page(n, eyebrow, title, sub, inner):
    return (f'<section class="page"><div class="bar"></div><div class="head"><div class="eyebrow">{eyebrow}</div>'
            f'<h2>{title}</h2><div class="sub">{sub}</div><div class="rule"></div></div>'
            f'<div class="body">{inner}</div><div class="foot"><span>Brazilian Modern Homes / Phase 2 · Casa 02 + '
            f'Casita</span><span>{n:02d}</span></div></section>')


def bleed(src, eyebrow, title, text, callouts=()):
    co = "".join(f"<span>{c}</span>" for c in callouts)
    return (f'<section class="page bleed"><img src="{src}" alt="{html.escape(title)}">'
            f'<div class="label"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{text}</p></div>'
            f'<div class="callouts">{co}</div></section>')


def fig(src, b, cap):
    return (f'<figure><div class="ph"><img class="fill" src="{src}" alt="{html.escape(b)}"></div>'
            f'<figcaption><b>{b}</b>{cap}</figcaption></figure>')


def build(img):
    P = []
    P.append(f'''<section class="page cover"><div class="panel"><div class="eyebrow">Phase 2 · November 2026</div>
<div class="goldrule"></div><h1>Casa 02<br>+ Casita</h1><div class="tagline">Duo and trio homes for Austin lots</div>
<p style="font-size:13px;line-height:1.6;color:#d9d3c4;margin-top:26px;max-width:300px">Two or three homes on one lot,
in the same Brazilian modern language as Casa 01: a cobogó lantern at the street, cedar gates, a limestone base
and a white upper floor.</p>
<div class="bottom">Brazilian soul. Texas materials.<br>Renders + plans + layouts + finishes</div></div>
<div style="position:relative"><img class="fill" src="{img.get("duo_dusk", "")}" alt="Casa 02 duo at dusk"></div></section>''')
    moves = "".join(f'<div class="move"><div class="k">{i + 1}</div><div><h3>{t}</h3><p>{p}</p></div></div>'
                    for i, (t, p) in enumerate(MOVES))
    facts = "".join(f'<div><div class="n">{a}</div><div class="l">{b}</div></div>' for a, b in FACTS)
    P.append(page(2, "The idea", "More homes on the same lot, with the same soul",
                  "Phase 2 turns Casa 01's language into a repeatable family for Austin's HOME rules.",
                  f'<div style="display:grid;grid-template-columns:1fr 1.25fr;gap:30px;height:100%">'
                  f'<div style="display:flex;flex-direction:column;gap:20px"><div class="moves">{moves}</div>'
                  f'<div class="facts">{facts}</div></div>'
                  f'{fig(img.get("trio_aerial", ""), "A trio on a 50 x 125 lot", "Two Casa 02s at the street, the Casita in the back garden, solar on the roofs. Each home has its own pátio.")}'
                  f'</div>'))
    P.append(bleed(img.get("duo_street", ""), "The duo · 50 x 125 lot",
                   "Stone, cedar, cobogó",
                   "A side-by-side pair reads as one composition: limestone at the outer corners, cedar carport gates, "
                   "and the two cobogó screens meeting at the center over the front doors.",
                   ["Lueders limestone pier", "Cedar slat gate", "Two-story cobogó", "Bronze floor band"]))
    P.append(bleed(img.get("duo_dusk", ""), "At dusk", "The lantern",
                   "The stair lands upstairs right behind the cobogó. When the landing light is on, the screen glows "
                   "the way Casa 01's does, and the carport's cedar ceiling warms the street.",
                   ["Cobogó lit from within", "Cedar carport ceiling", "Path lights"]))
    P.append(page(5, "Arrive and live", "Through the screen, out to the garden",
                  "The front door sits inside the cobogó, on a calçada threshold. At the back, the house opens wide to its own pátio.",
                  f'<div class="two">'
                  f'{fig(img.get("duo_entry", ""), "The entry", "The front door is under the screen, beside the cedar carport gate and the limestone corner pier. The carport door is the step-free entry, on a black calçada rug.")}'
                  f'{fig(img.get("duo_garden", ""), "The pátio", "A 16-ft slider opens the kitchen and dining room to a São Tomé limestone terrace and a buffalo-grass garden under a live oak. The open oak stair rises behind cedar slats.")}'
                  f'</div>'))
    P.append(bleed(img.get("trio_street", ""), "The trio · Casita at the street",
                   "A garden wall, a cedar gate",
                   "On an alley lot the one-story Casita faces the street behind its own walled garden: limestone piers, "
                   "a cobogó panel and a cedar slat gate, with a covered porch inside. The pair parks off the alley.",
                   ["Limestone piers", "Cedar garden gate", "Covered porch"]))
    # plans
    pl = [("Ground floor, carport", C.plan_svg(H.CASA02_GF_CARPORT), f"{A['carport_gf']:,.0f} sf + 210 sf carport"),
          ("Ground floor, suite", C.plan_svg(H.CASA02_GF_SUITE), f"{A['suite_gf']:,.0f} sf · for wide lots"),
          ("Upper floor", C.plan_svg(H.CASA02_UPPER, note_front="FRONT"), f"{A['upper']:,.0f} sf · both versions"),
          ("Casita", C.plan_svg(H.CASITA, scale=15.0, note_front="FRONT"), f"{A['casita']:,.0f} sf + covered porch")]
    cols = "".join(f'<div class="p"><h4>{t}</h4><div class="dwgwrap">{svg_fit(s)}</div><small>{c}</small></div>'
                   for t, s, c in pl)
    P.append(page(7, "The homes", "Casa 02 and the Casita",
                  "Casa 02: 20 x 39 ft, two stories; the bay at the front is a carport or a bedroom suite. The Casita: "
                  "20 x 32 ft, one story. Developed plans: Phase2_Casa02_Plans.pdf.",
                  f'<div class="plans">{cols}</div>'))
    # layouts
    lay = []
    for fn in C.SITES:
        s = fn()
        m = C.check_site(s)
        homes = ", ".join(h["kind"] for h in s["homes"])
        lay.append(f'<div class="p"><h4>{s["id"]} · {s["lot"]["W"]:.0f} x {s["lot"]["L"]:.0f}</h4>'
                   f'<div class="dwgwrap">{svg_fit(C.site_svg(s))}</div>'
                   f'<small><b>{html.escape(s["name"])}</b><br>{homes}<br>{m["fa"]:,.0f} sf · parking for '
                   f'{m["parking"]} of {m["n"]}</small></div>')
    P.append(page(8, "The layouts", "Five ways onto a lot",
                  "Each layout passes Austin's floor-area, footprint, impervious-cover and front-yard paving caps. "
                  "Site plans: Phase2_Concepts.pdf and the AutoCAD file.",
                  f'<div class="lay">{"".join(lay)}</div>'))
    sw = "".join(f'<div class="t"><img src="{img.get("sw_" + k, "")}" alt="{n}"><h4>{n}</h4><div class="br">{br}</div>'
                 f'<div class="sp">{sp}</div></div>' for k, n, br, sp in SWATCHES)
    P.append(page(9, "Finishes", "The same palette as Casa 01",
                  "Each staple used once per home, where it counts: stone at the base, calçada at the door, cedar "
                  "where hands touch, cobogó where light comes through.",
                  f'<div class="sw">{sw}</div>'))
    items = [("Concept sheets", "Phase2_Concepts.pdf: plans, the five site plans with their checks, 3D views"),
             ("Developed plans", "Phase2_Casa02_Plans.pdf: A-101 to A-103, dimensions, door and window schedules"),
             ("AutoCAD", "Phase2_Concepts.dxf: every plan as a block, every site and sheet as a layout"),
             ("Facade study", "Phase2_Facade_Options.pdf: the three options and the direction chosen"),
             ("Test-fit", "Phase2_TestFit.pdf: 19 layouts on six standard Austin lots")]
    nxt = ["Elevations and sections for Casa 02 and the Casita",
           "The side-parking ground floor for lots with a drive",
           "Structure and MEP coordination with the engineer",
           "Pricing with a builder, then the city's HOME review"]
    li = "".join(f"<li>{t}</li>" for t in nxt)
    rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td></tr>" for a, b in items)
    P.append(page(10, "In the package", "What's drawn, and what's next",
                  "Everything comes from one model, so a change shows up in the drawings, the AutoCAD file and the renders.",
                  f'<div style="display:grid;grid-template-columns:1.3fr 1fr;gap:34px">'
                  f'<div><table>{rows}</table></div><div class="side"><div class="eyebrow">Next</div>'
                  f'<ul class="list">{li}</ul><div class="note"><b>Concept design</b>Not for construction. Confirm '
                  f'zoning, utilities, trees and fire access with the City of Austin before pricing.</div></div></div>'))
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
