"""Comparison sheets for the Casa 02 facade study.

    python3 phase2/study/sheet.py
    node casa01/signoff/print_pdf.js phase2/study/out/facade_options.html phase2/study/Phase2_Facade_Options.pdf
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")

OPTIONS = [
    ("base", "As drawn", "The concept as it stands: limestone and cedar bases, a plain white upper floor."),
    ("A", "A · Cedar veil", "The upper floor stands behind a cedar slat screen, front and back: the Brazilian "
                            "muxarabi. Windows sit where the rooms need them; the screen gives the facade its order."),
    ("B", "B · Stepped", "The upper floor slides 8 ft back. The street sees a one-story front with a roof "
                         "terrace; at the back the upper floor cantilevers over the pátio on two slim columns."),
    ("C", "C · Cobogó lantern", "The entry and stair column rises two stories in cobogó. On a pair the two "
                                "columns meet at the centre and glow at night, like Casa 01's screen."),
]
VIEWS = [("street", "Street, day"), ("dusk", "Street, dusk"), ("aerial", "From above"),
         ("alley_trio", "Alley trio: the Casita at the street")]

# criterion, as drawn, A, B, C   (L1-D1 duo and the trios on 50-ft lots)
COMPARE = [
    ("What the street sees", "Two carport gates, two doors, a plain white box above",
     "A warm wooden box floating over a stone and cedar base", "A one-story front with a terrace; the upper floor recedes",
     "A two-story cobogó lantern at the centre, cedar gates either side"),
    ("Privacy upstairs", "Windows only", "Best: screened front and back", "Terrace faces the street",
     "Stair and entry behind the screen; bedrooms as drawn"),
    ("At night", "Lit windows", "Soft glow through the slats", "Glow on the terrace",
     "Strongest: the lantern, as at Casa 01"),
    ("Link to Casa 01", "Weak", "Strong (cedar, Brazilian screen)", "Moderate (the low street edge)",
     "Strongest (cobogó, the dusk lantern)"),
    ("Floor area per home", "1,350 sf", "1,350 sf", "1,350 sf, plus a 160 sf terrace and a covered back porch",
     "1,350 sf"),
    ("Footprint", "Within the cap", "Within the cap (the screen projects 1'-4\", inside the 2 ft allowed)",
     "+160 sf per home: fine for duos, but the 50-ft trios go over the cap (2,520 of 2,500 sf)",
     "Within the cap (the panel projects 1 ft)"),
    ("Cost (relative)", "Base", "+ cedar screen, about 400 sf per home", "++ steel cantilever, terrace waterproofing",
     "+ about 180 blocks per home"),
    ("Upkeep", "Low", "Cedar oil every 2–3 years", "Terrace membrane", "Low (concrete)"),
    ("Wildfire code", "—", "In a wildfire zone the slats must be fire-retardant cedar or an aluminum wood-look",
     "—", "Noncombustible: no issue"),
    ("Works on", "Every layout", "Every layout", "Duos and wide or corner lots, not 50-ft trios",
     "Every layout where the stair column faces a street or alley"),
]

RECOMMEND = ("Lead with C, the cobogó lantern, and borrow A's cedar veil for the pátio side. C gives Casa 02 the "
             "same identity as Casa 01 at no cost in floor area or footprint, it costs little to keep up, it meets "
             "the wildfire code, and it works on every layout. The cedar veil on the back adds upstairs privacy and "
             "afternoon shade where the homes face each other's gardens. Keep B for wide and corner duos, where the "
             "footprint allows a roof terrace.")

DIRECTION = ("Casa 02 takes option C as drawn: the two-story cobogó lantern at the entry and stair, cedar gates "
             "at the carports. The only change is at the Casita: its cobogó garden wall gets a 4-ft cedar slat gate, "
             "the same slats as the Casa 02 carport gates, so the Casita at the street carries both materials. "
             "The cedar veil on the back of the upper floor (from option A) is not used. "
             "Top: the duo by day and at dusk. Bottom: the alley trio, with the Casita and its gate at the street.")

CSS = open(os.path.join(ROOT, "casa01", "signoff", "signoff_v2.py")).read().split('CSS = """')[1].split('"""')[0]
CSS += """
.grid{display:grid;grid-template-columns:110px repeat(4,1fr);gap:6px;align-items:center}
.grid img{width:100%;display:block;border:1px solid #dcd6c8}
.grid .h{font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}
.grid .r{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#5b625b}
.cmp td,.cmp th{font-size:10px;padding:5px 6px;vertical-align:top}
.cmp td:first-child{font-weight:700;width:12%}
.big{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.big img{width:100%;display:block;border:1px solid #dcd6c8}
.lead{font-size:12px;line-height:1.45;margin:0}
"""


def title_block(sheet, title):
    return (f'<aside class="tb"><div class="brand">Brazilian Modern Homes<small>Residential design · Austin</small></div>'
            f'<div class="proj">Phase 2<br>Casa 02 facade<small>Three-option study</small></div>'
            f'<div class="grow"></div><div class="kv"><span>Sheet title</span><b>{title}</b><span>Scale</span><b>3D views</b>'
            f'<span>Date / phase</span><b>Nov 2026 · Concept</b></div><div class="sheet">{sheet}</div>'
            f'<div class="warn">Low-detail massing. For choosing a direction.</div></aside>')


def img(key, view):
    f = f"{key}_{view}.png"
    return f'<img src="{f}">' if os.path.exists(os.path.join(OUT, f)) else '<div style="height:80px;background:#eee"></div>'


def main():
    pages = []
    head = '<div></div>' + "".join(f'<div class="h">{n}</div>' for _k, n, _d in OPTIONS)
    rows = "".join(f'<div class="r">{vn}</div>' + "".join(img(k, v) for k, _n, _d in OPTIONS) for v, vn in VIEWS)
    pages.append(f'<section class="page"><div class="main" style="grid-template-rows:auto auto 1fr;align-content:start">'
                 f'<h1>Casa 02 facade · three options side by side</h1>'
                 f'<p class="lead">Same plans, same lots, same cameras: only the street face changes. The top three rows '
                 f'show the side-by-side duo on a 50 × 125 lot (L1-D1); the last row shows the alley trio (L2-T2), '
                 f'where A, B and C also give the Casita a covered porch and a cobogó garden wall.</p>'
                 f'<div class="grid">{head}{rows}</div></div>{title_block("F-1", "All options")}</section>')
    th = "".join(f"<th>{n}</th>" for _k, n, _d in OPTIONS)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in COMPARE)
    pages.append(f'<section class="page"><div class="main" style="grid-template-rows:auto auto auto;align-content:start">'
                 f'<h1>How they compare</h1><table class="cmp"><thead><tr><th></th>{th}</tr></thead><tbody>{tr}</tbody></table>'
                 f'<div class="box rec"><b>Claude\'s recommendation</b>{RECOMMEND}</div></div>'
                 f'{title_block("F-2", "Comparison")}</section>')
    for i, (k, n, d) in enumerate(OPTIONS[1:]):
        pages.append(f'<section class="page"><div class="main" style="grid-template-rows:auto auto auto auto;align-content:start">'
                     f'<h1>{n}</h1><p class="lead">{d}</p>'
                     f'<div class="big">{img(k, "street")}{img(k, "dusk")}</div>'
                     f'<div class="big">{img(k, "aerial")}{img(k, "alley_trio")}</div></div>'
                     f'{title_block(f"F-{i + 3}", n)}</section>')
    pages.append(f'<section class="page"><div class="main" style="grid-template-rows:auto auto auto auto;align-content:start">'
                 f'<h1>Direction chosen · C, with a cedar gate at the Casita</h1><p class="lead">{DIRECTION}</p>'
                 f'<div class="big">{img("C", "street")}{img("C", "dusk")}</div>'
                 f'<div class="big">{img("Cplus", "alley_trio")}{img("Cplus", "alley_dusk")}</div></div>'
                 f'{title_block("F-6", "Direction chosen")}</section>')
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Casa 02 facade options</title>'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(os.path.join(OUT, "facade_options.html"), "w").write(html)
    print("wrote", os.path.join(OUT, "facade_options.html"))


if __name__ == "__main__":
    main()
