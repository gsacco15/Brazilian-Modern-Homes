"""Casa 01 V2 layout sign-off sheets (HTML -> PDF).

    python3 casa01/signoff/build_v2.py        # V2 drawings first
    python3 casa01/signoff/signoff_v2.py      # -> casa01/signoff/signoff_v2.html
    node casa01/signoff/print_pdf.js casa01/signoff/signoff_v2.html casa01/signoff/Casa01_V2_Layout_Signoff.pdf
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
sys.path.insert(0, CASA)
import design as D  # noqa: E402

V1 = os.path.join(CASA, "drawings")
V2 = os.path.join(CASA, "drawings", "v2")
RED = "#c0392b"

# numbered changes: (marker position in feet on the V2 plan, title, detail)
CHANGES = [
    ((36.6, 75.6), "Bigger great room",
     "Living bar extended 4 ft east. Living is now about 14 ft wide (262 sf, was 196); dining 193 sf (was 164). "
     "The dining table turns north-south, so it no longer crowds the sofa."),
    ((51.5, 64.0), "Primary suite moved 4 ft east",
     "Same bedroom, walk-in and spa bath, shifted with the new east wall. The bath door moved so it clears the vanity."),
    ((54.0, 40.5), "Carport behind a sliding cedar gate",
     "One car, 11 x 20 ft, at the front-east corner under the same thin roof. A motorized sliding cedar gate (D16) closes "
     "it from the street and parks behind the cobogó when open. Cedar gate D15 leads into the covered entry and the front door."),
    ((53.2, 54.0), "One L-shaped courtyard",
     "The courtyard wraps behind the carport to the primary bedroom, whose 8 ft slider (D3) and window open onto it. "
     "Cedar slats line the carport's two courtyard sides, and a new slat screen on the east edge brings in morning light. "
     "763 sf with the covered entry (V1: 771)."),
    ((10.2, 52.6), "Bedroom wing 2 ft narrower",
     "Bedrooms 2 and 3 are 14'-3\" wide (were 16'-3\"), about 155 sf each, still fitting a queen bed and desk. "
     "This keeps the courtyard 22'-6\" wide (V1: 26 ft) and the cobogó 17 ft (V1: 21 ft)."),
    ((15.8, 42.6), "Bath 2 re-planned",
     "Tub/shower on the far wall, vanity and toilet on the long walls; the door from the gallery swings into clear floor."),
    ((19.3, 51.6), "Door swings cleared",
     "Bedroom 2 and 3 doors moved clear of the beds, the laundry door now swings out, the primary bath door clears the vanity. "
     "Every door has a tag (D1-D16), including the front pivot door D1."),
    ((32.0, 81.6), "Stock-size glass",
     "Veranda slider 16 ft (was a custom 18 ft), courtyard slider a stock 12 ft 3-panel (was 9'-6\"), primary 8 ft slider "
     "+ 4 ft window. The gallery glass wall stays as is."),
    ((46.25, 75.6), "Two skylights",
     "Over the windowless Bath 2 and the walk-in closet (dashed X)."),
    ((3.0, 59.6), "HVAC: one outdoor unit",
     "AC pad in the west side yard. Two hidden air handlers: AHU-1 above the laundry, AHU-2 above the walk-in. Dropped "
     "8'-6\" ceilings only over laundry, closets, Bath 2 and walk-in (dash-dot). Living spaces stay 10 ft."),
    ((9.7, 59.0), "Laundry + water heater",
     "Stacked washer/dryer and a heat-pump water heater in the laundry."),
    ((16.8, 76.4), "Kitchen trimmed 1 ft",
     "North counter run shortened by 1 ft so the dining area gets the space; island and window move with it."),
]

SPEC_CHANGES = [
    "Cedar ceiling in the great room only; bedrooms, gallery and baths painted (soffits, veranda and street edge stay cedar).",
    "Buff Lueders limestone at the street wall.",
    "Zellige-look glazed porcelain in the primary shower (same look, lower cost).",
    "Roof: low-slope TPO behind the bronze fascia stays the working assumption (marked TBD).",
]
KEPT = ["Gallery glass wall (a signature feature)", "Laundry location", "Front cedar pivot door + entry gate",
        "Arrival: carport, cedar gate, covered entry, front door", "Black calçada entry",
        "Cobogó screen, limestone wall, thin roof", "Cedar veranda", "3 bedrooms / 2 baths"]
LATER = ["Roof drainage, fascia depth, hail assembly", "Powder room, flex room, drop zone, storage", "Cobogó sourcing",
         "Low-maintenance wood", "Backup power + EV", "Acoustics, screened veranda, outdoor shower",
         "Courtyard drainage, oak root zone, impervious cover", "Structure, code, budget re-run",
         "Other elevations, renders, 3D model and lookbook V2 (after sign-off)"]


def svg_file(path, markers=None, mapping=None):
    s = open(path).read()
    s = re.sub(r'<svg ', '<svg preserveAspectRatio="xMidYMid meet" ', s, count=1)
    s = re.sub(r'width="\d+" height="\d+"', 'width="100%" height="100%"', s, count=1)
    if markers:
        m = mapping
        g = []
        for i, ((x, y), _t, _d) in enumerate(markers, 1):
            X = m["pad"] + (x - m["x0"]) * m["scale"]
            Y = m["pad"] + (m["y1"] - y) * m["scale"]
            g.append(f'<g transform="translate({X:.1f},{Y:.1f})"><path d="M0 -13 L12 8 L-12 8 Z" fill="#ffffff" '
                     f'stroke="{RED}" stroke-width="2.2"/><text y="5" text-anchor="middle" font-family="Lato,Arial" '
                     f'font-size="10.5" font-weight="900" fill="{RED}">{i}</text></g>')
        s = s.replace("</svg>", "".join(g) + "</svg>")
    return s


def mapping_of(path):
    head = open(path).read(600)
    get = lambda k: float(re.search(fr'data-{k}="([-\d.]+)"', head).group(1))
    return dict(x0=get("x0"), y1=get("y1"), pad=get("pad"), scale=get("scale"))


def title_block(sheet, title, scale):
    return (f'<aside class="tb"><div class="brand">Brazilian Modern Homes<small>Residential design · Austin</small></div>'
            f'<div class="proj">Casa 01<br>Casa Pátio<small>V2 layout · for sign-off</small></div>'
            f'<div class="grow"></div><div class="kv"><span>Sheet title</span><b>{title}</b><span>Scale</span><b>{scale}</b>'
            f'<span>Date / phase</span><b>Nov 2026 · Design review</b></div><div class="sheet">{sheet}</div>'
            f'<div class="warn">Concept design. Not for construction.</div></aside>')


CSS = """
@page{size:17in 11in;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:Lato,"Helvetica Neue",Arial,sans-serif;color:#1b1d1f;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:17in;height:11in;padding:.35in;display:grid;grid-template-columns:1fr 2.3in;gap:.25in;page-break-after:always;overflow:hidden}
.main{border:1.5px solid #1b1d1f;padding:.22in;display:grid;gap:.18in;min-width:0;min-height:0}
.tb{border:1.5px solid #1b1d1f;display:flex;flex-direction:column}
.tb>div{border-bottom:1px solid #1b1d1f;padding:.14in}
.brand{background:#1d2520;color:#ece6d8;font-weight:900;letter-spacing:.14em;text-transform:uppercase;font-size:13px;line-height:1.2}
.brand small{display:block;color:#d2b47c;font-size:9px;margin-top:4px}
.proj{font-family:"Cormorant Garamond",Georgia,serif;font-size:24px;line-height:1.05}
.proj small{display:block;font-family:Lato,Arial;font-size:9px;letter-spacing:.14em;text-transform:uppercase;margin-top:6px;color:#5b625b}
.grow{flex:1}
.kv{display:grid;gap:2px;font-size:11px}.kv span{font-size:8.5px;letter-spacing:.14em;text-transform:uppercase;color:#5b625b;margin-top:6px}
.sheet{font-size:44px;font-weight:900;letter-spacing:-.01em}
.warn{color:#a3361f;font-size:9px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;border-bottom:0!important}
h1{margin:0;font-size:15px;letter-spacing:.14em;text-transform:uppercase}
h2{margin:0 0 6px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#5b625b}
.cols{display:grid;grid-template-columns:1.55fr 1fr;gap:.25in;min-height:0}
.plan{min-height:0;display:flex;align-items:center;justify-content:center}
.plan svg{max-height:100%}
ol.chg{margin:0;padding-left:0;list-style:none;counter-reset:c;display:grid;gap:5px;font-size:10.2px;line-height:1.33}
ol.chg li{counter-increment:c;padding-left:24px;position:relative}
ol.chg li::before{content:counter(c);position:absolute;left:0;top:0;color:#c0392b;font-weight:900;border:1.6px solid #c0392b;
  width:16px;height:14px;font-size:9px;display:grid;place-items:center;clip-path:polygon(50% 0,100% 100%,0 100%);padding-top:3px}
ol.chg b{display:block;font-size:11px}
ul{margin:0;padding-left:16px;font-size:10.5px;line-height:1.4}
table{border-collapse:collapse;width:100%;font-size:10.5px}
td,th{border-bottom:1px solid #dcd6c8;padding:4px 6px;text-align:left;vertical-align:top}
th{font-size:8.5px;letter-spacing:.12em;text-transform:uppercase;color:#5b625b}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.two{display:grid;grid-template-columns:1fr 1fr;gap:.25in;min-height:0}
.cap{font-size:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:900;margin-top:4px}
.box{border:1px solid #dcd6c8;padding:.12in;font-size:10.5px;line-height:1.4}
.box b{display:block;margin-bottom:2px}
.rec{border:2px solid #1d2520;background:#f5f2ea}
.sign{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.2in;font-size:11px}
.sign div{border-top:1px solid #1b1d1f;padding-top:4px}
.chk{display:flex;gap:.3in;font-size:12px}.chk span::before{content:"";display:inline-block;width:12px;height:12px;border:1.5px solid #1b1d1f;margin-right:6px;vertical-align:-2px}
.elev{display:grid;grid-template-rows:1fr auto;min-height:0}
"""


def main():
    p2 = os.path.join(V2, "30_floor_plan_cd.svg")
    m2 = mapping_of(p2)
    sched = json.load(open(os.path.join(V2, "schedules.json")))
    area = D.area_schedule()
    rooms = {r["name"]: D.poly_area(r["poly"]) for r in D.ROOMS}
    items = "".join(f'<li><b>{t}</b> {d}</li>' for _xy, t, d in CHANGES)
    spec = "".join(f"<li>{t}</li>" for t in SPEC_CHANGES)
    kept = "".join(f"<li>{t}</li>" for t in KEPT)
    later = "".join(f"<li>{t}</li>" for t in LATER)
    doors = "".join(f"<tr><td><b>{d['tag']}</b></td><td>{d['name']}</td><td>{d['type']}</td></tr>" for d in sched["doors"])
    knotes = "".join(f"<li>{k}</li>" for k in sched["keynotes"])
    cmp_rows = [("Conditioned area", "1,620 sf", f"{area['conditioned']:,.0f} sf"),
                ("Living / dining", "196 / 164 sf", f"{rooms['Living']:.0f} / {rooms['Dining']:.0f} sf"),
                ("Bedroom 2 / Bedroom 3", "176 / 181 sf", f"{rooms['Bedroom 2']:.0f} / {rooms['Bedroom 3']:.0f} sf"),
                ("Bath 2", "63 sf", f"{rooms['Bath 2']:.0f} sf"),
                ("Courtyard + covered entry", "771 sf", f"{area['courtyard']:,.0f} sf"),
                ("Courtyard width / cobogó", "26'-0\" / 21 ft", "22'-6\" / 17 ft"),
                ("Carport", "—", f"{area['carport']:,.0f} sf, sliding cedar gate"),
                ("Roof plate", "2,760 sf", f"{area['roof']:,.0f} sf"), ("Bedrooms / baths", "3 / 2", "3 / 2"),
                ("Skylights", "—", "2")]
    cmp = "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>" for a, b, c in cmp_rows)
    cost = [("Conditioned area +20 sf net (great room +80, bedroom wing −60)", "Adds about $5–10K"),
            ("Carport, no storage", "Adds about $15–25K"), ("Motorized sliding cedar gate", "Adds about $6–10K"),
            ("East slat screen", "Adds about $1–2K"), ("Two skylights", "Adds $4–8K"), ("HVAC option A", "About $0–8K"),
            ("Cedar ceilings scaled back", "Saves $15–30K"), ("Stock-size glass", "Saves about $10–25K"),
            ("Zellige-look porcelain", "Saves $3–8K")]
    costr = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in cost)
    tb1 = title_block("V2-1", "Floor plan, changes", "1/8\" = 1'-0\" (approx.)")
    tb2 = title_block("V2-2", "Street front", "1/8\" = 1'-0\" (approx.)")
    tb4 = title_block("V2-4", "Site plan + carport", "1\" = 20'-0\" (approx.)")
    pages = []
    # 1: V2 plan with change markers
    pages.append(
        f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr"><h1>V2 floor plan · numbered changes from V1</h1>'
        f'<div class="cols"><div class="plan">{svg_file(p2, CHANGES, m2)}</div>'
        f'<div style="min-height:0;overflow:hidden"><h2>What changed (red triangles on the plan)</h2><ol class="chg">{items}</ol>'
        f'<h2 style="margin-top:10px">Spec changes (no plan change)</h2><ul>{spec}</ul></div></div></div>'
        + tb1 + '</section>')
    # 2: street front V1 vs V2
    pages.append(
        f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr 1fr auto"><h1>Street front · V1 vs V2</h1>'
        f'<div class="elev"><div class="plan">{svg_file(os.path.join(V1, "32_elev_s_cd.svg"))}</div>'
        f'<div class="cap">V1 · limestone 23\'-6" · cedar gate 4\' · cobogó 21\' · open parking pad beside it</div></div>'
        f'<div class="elev"><div class="plan">{svg_file(os.path.join(V2, "32_elev_s_cd.svg"))}</div>'
        f'<div class="cap" style="color:#c0392b">V2 · limestone 21\'-6" · cedar gate 4\' · cobogó 17\' · sliding cedar carport gate 11\'</div></div>'
        f'<div class="two"><div class="box"><b>How the front reads</b>One long roof edge over four screened parts: stone, cedar, '
        f'cobogó, cedar. The carport gate repeats the pivot gate\'s slats, so the car is never part of the facade and the front '
        f'reads as one composition rather than a house plus a garage.</div>'
        f'<div class="box"><b>How the gate works</b>Motorized, full height to the soffit. Closed when the car is in. When it '
        f'opens it slides west and parks behind the cobogó, where the slats show through the circles. Remote, keypad and '
        f'safety sensors standard.</div></div></div>' + tb2 + '</section>')
    # 3: V1 vs V2 plans
    pages.append(
        f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr auto"><h1>V1 vs V2 plans, same scale</h1>'
        f'<div class="two"><div style="display:grid;grid-template-rows:1fr auto;min-height:0"><div class="plan">'
        f'{svg_file(os.path.join(V1, "30_floor_plan_cd.svg"))}</div><div class="cap">V1 · as presented</div></div>'
        f'<div style="display:grid;grid-template-rows:1fr auto;min-height:0"><div class="plan">{svg_file(p2)}</div>'
        f'<div class="cap" style="color:#c0392b">V2 · for sign-off</div></div></div>'
        f'<table><tr><th>Area</th><th style="text-align:right">V1</th><th style="text-align:right">V2</th></tr>{cmp}</table></div>'
        f'{title_block("V2-3", "V1 vs V2 plans", "Same scale")}</section>')
    # 4: site plan + carport options
    pages.append(
        f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr"><h1>Site plan · where the carport goes</h1>'
        f'<div class="cols" style="grid-template-columns:1fr 1.15fr"><div class="plan">{svg_file(os.path.join(V2, "01_site_plan.svg"))}</div>'
        f'<div style="display:grid;gap:.14in;align-content:start">'
        f'<div class="box rec"><b>Chosen · Front-east carport, one courtyard, sliding cedar gate</b>11 x 20 ft for one car under '
        f'the main roof, behind a sliding cedar gate. It is the only spot on a 65 ft lot that fits a car behind the 25 ft front '
        f'setback and outside the 5 ft side setbacks. You arrive under the roof and walk through a cedar gate into the covered '
        f'entry. The courtyard wraps behind it as one space; the bedroom wing gives up 2 ft so the courtyard stays 22\'-6" wide. '
        f'The roof edge lands on the side setback line; eave rules to verify.</div>'
        f'<div class="box"><b>Rear carport off a side driveway (not chosen)</b>About 90 ft of driveway down the east side (more '
        f'paving against the 45% impervious cover limit), no room left for the bigger great room, cars beside the primary bedroom '
        f'and veranda, the carport in the heritage oak\'s protected root zone, and no arrival through the courtyard gate.</div>'
        f'<div class="box"><b>In the front yard (not allowed)</b>Inside the 25 ft front setback.</div>'
        f'<div class="box"><b>Fallback · no carport on 65 ft lots</b>Keep V1\'s open parking pad and full courtyard; offer the '
        f'carport on 70+ ft lots, where it fits in the side yard (Phase 2 lot types).</div>'
        f'<h2 style="margin-top:6px">Rough cost effect vs V1 (estimates)</h2><table>{costr}'
        f'<tr><td><b>Net</b></td><td><b>About break-even, give or take $30K; confirmed in the budget re-run (P1-44)</b></td></tr></table>'
        f'</div></div></div>' + tb4 + '</section>')
    # 5: decision log + doors + sign-off
    pages.append(
        f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr auto"><h1>Decision log + sign-off</h1>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1.2fr;gap:.25in;min-height:0">'
        f'<div><h2>Kept as is</h2><ul>{kept}</ul><h2 style="margin-top:12px">Saved for later (tracker)</h2><ul>{later}</ul></div>'
        f'<div><h2>Keynotes</h2><ol style="margin:0;padding-left:18px;font-size:10.5px;line-height:1.4">{knotes}</ol></div>'
        f'<div><h2>Doors (every door tagged)</h2><table><tr><th>No.</th><th>Location</th><th>Type</th></tr>{doors}</table></div></div>'
        f'<div style="display:grid;gap:.16in"><h2>Design sign-off · V2 layout</h2><div class="chk"><span>Approved as drawn</span>'
        f'<span>Approved with the changes noted</span><span>Revise and resubmit</span></div>'
        f'<div class="box" style="min-height:.8in"><b>Changes / notes</b></div>'
        f'<div class="sign"><div>Name</div><div>Signature</div><div>Date</div></div></div></div>'
        f'{title_block("V2-5", "Decisions + sign-off", "—")}</section>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Casa 01 V2 Layout Sign-off</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500&family=Lato:wght@400;700;900&display=swap">'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    out = os.path.join(HERE, "signoff_v2.html")
    open(out, "w").write(html)
    print("wrote", out)


if __name__ == "__main__":
    main()
