"""Casa 02 developed floor plans: A-101 ground floor with carport, A-102 ground floor with suite, A-103 upper floor.

    python3 phase2/plans/plans.py
    node casa01/signoff/print_pdf.js phase2/plans/out/plans.html phase2/plans/Phase2_Casa02_Plans.pdf

Drawn from the same model as the concept sheets, the AutoCAD file and the 3D views (phase2/model/homes.py), with
the concept drawing kit (phase2/concepts/concepts.py). This adds what a developed plan needs: dimension strings,
door and window tags with their schedules, room sizes and areas, and the general notes.
Dimensions run to the outside face of exterior walls and to the centreline of partitions; areas likewise.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.join(P2, "concepts"))
sys.path.insert(0, HERE)
import concepts as C  # noqa: E402  (plan drawing kit; it also puts the model and Casa 01 kit on the path)

C.LANTERN_LABEL = False     # the screen gets a leader label here, clear of the tags at the front

H, DR, tp = C.H, C.DR, C.tp
INK, MID, LIGHT = C.INK, C.MID, C.LIGHT
fmt = DR.fmt_ft

DOOR_HEAD = 8.0
WIN_HEAD = 8.5
SILL = {"high": 5.5, "egress": 2.25, "fluted below 5'": 2.25, "egress, fluted below 5'": 2.25, "sill 3'-6\"": 3.5,
        "to the pátio, cedar-screened": 1.0, "behind the cobogó": 1.0}
WIN_NOTE = {"high": "High window, for light and privacy",
            "egress": "Egress: 5.7 sf clear opening, sill under 44 in",
            "fluted below 5'": "Fluted glass below 5 ft",
            "egress, fluted below 5'": "Egress; fluted glass below 5 ft",
            "sill 3'-6\"": "Above the sofa or desk",
            "to the pátio, cedar-screened": "Tall window to the pátio, cedar slat screen outside",
            "behind the cobogó": "Tall window behind the cobogó screen"}

SHEETS = [
    dict(no="A-101", plan=H.CASA02_GF_CARPORT, title="Ground floor, carport", floor=1,
         chains=dict(front=[0, 10.5, 14.25, 20], west=[0, 20, 27, 39], east=[0, 5.5, 9.5, 19.5, 27, 39])),
    dict(no="A-102", plan=H.CASA02_GF_SUITE, title="Ground floor, suite", floor=1,
         chains=dict(front=[0, 10.5, 14.25, 20], west=[0, 12.5, 20, 27, 39], east=[0, 5.5, 9.5, 19.5, 27, 39])),
    dict(no="A-104", plan=H.CASA02_GF_SIDE, title="Ground floor, side drive", floor=1,
         chains=dict(front=[0, 10.5, 16, 20], west=[0, 10.5, 16, 20, 27, 39], east=[0, 10.5, 19.5, 27, 39])),
    dict(no="A-103", plan=H.CASA02_UPPER, title="Upper floor, all versions", floor=2,
         chains=dict(front=[0, 10.5, 20], west=[0, 11, 16.5, 27, 39], east=[0, 6, 19.5, 23.5, 30, 39],
                     back=[0, 14, 20])),
]


# ---------------------------------------------------------------- openings, rooms
def room_area(plan, name):
    for r in plan["rooms"]:
        if r["name"] == name:
            x0, y0, x1, y1 = r["rect"]
            return (x1 - x0) * (y1 - y0)
    return 1e9 if name == "Outside" else 0.0


def room_at(plan, x, y):
    best = None
    for r in plan["rooms"]:
        x0, y0, x1, y1 = r["rect"]
        if x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6:
            a = (x1 - x0) * (y1 - y0)
            if best is None or a < best[0]:
                best = (a, r["name"])
    if best:
        return best[1]
    if 0 <= x <= plan["W"] and 0 <= y <= plan["D"]:
        return "Hall"
    return "Outside"


def openings(plan, floor):
    """Every door, slider and window with its tag, position and the rooms on each side."""
    doors, wins = [], []
    for w in plan["walls"]:
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        th = w["t"]
        for o in sorted(w["openings"], key=lambda o: o["off"]):
            m = o["off"] + o["w"] / 2
            px, py = ax + ux * m, ay + uy * m
            if w["ext"]:                                 # wall face runs 0..t to the left (inside)
                cx, cy = px + nx * th / 2, py + ny * th / 2
            else:
                cx, cy = px, py
            left = room_at(plan, cx + nx * 0.9, cy + ny * 0.9)
            right = room_at(plan, cx - nx * 0.9, cy - ny * 0.9)
            rec = dict(o=o, ext=w["ext"], p=(cx, cy), n=(nx, ny), u=(ux, uy), th=th, left=left, right=right)
            (doors if o["kind"] in ("door", "slider", "bypass") else wins).append(rec)
    for i, d in enumerate(doors):
        d["tag"] = f"{floor}{i + 1:02d}"
    for i, w_ in enumerate(wins):
        w_["tag"] = f"W{floor}{i + 1:02d}"
    return doors, wins


def door_row(d, plan):
    o = d["o"]
    if o["kind"] == "slider":
        frm, to = "Outside", d["left"]
        kind = "Sliding glass"
    elif o["kind"] == "bypass":
        a_, b_ = sorted((d["left"], d["right"]), key=lambda n: room_area(plan, n))
        frm, to = b_, a_
        kind = "Bypass sliding"
    else:
        swing_into = d["left"] if o["side"] == "L" else d["right"]
        frm = d["right"] if o["side"] == "L" else d["left"]
        frm, to = frm, swing_into
        kind = "Swing, exterior" if d["ext"] else "Swing"
    rooms = {frm, to}
    note = ""
    if d["ext"] and o["kind"] == "door" and "Carport" in rooms | {"Outside"} and d["n"] == (1.0, -0.0):
        note = ""
    if "Mech" in rooms:
        note = "Louvred, for the water heater's air"
    elif d["ext"] and o["kind"] == "door":
        if "Carport" in rooms and plan is H.CASA02_GF_SIDE:
            note = "Entry from the carport: oak, solid core, no step"
        elif "Carport" in rooms:
            note = "No-step entry from the carport; half glass"
        else:
            note = "Front door: oak, solid core, under the cobogó"
    elif o["kind"] == "slider":
        note = "Four panels, two sliding, to the pátio" if o["w"] >= 12 else "To the side pátio; detached sites only"
    elif "WC" in rooms:
        note = "2'-10\" for 32 in clear (visitability)"
    elif "Mech" in rooms:
        note = "Louvred, for the water heater's air"
    elif "Closet" in rooms or "Laundry" in rooms:
        note = "Solid core"
    loc = f"{frm} → {to}" if frm != to else to
    return [d["tag"], loc, f"{fmt(o['w'])} × {fmt(DOOR_HEAD)}", kind, note]


def win_row(w_, plan):
    o = w_["o"]
    sill = SILL.get(o.get("note", ""), 2.5)
    room = w_["left"] if w_["left"] != "Outside" else w_["right"]
    return [w_["tag"], room, f"{fmt(o['w'])} × {fmt(WIN_HEAD - sill)}", fmt(sill), fmt(WIN_HEAD),
            WIN_NOTE.get(o.get("note", ""), "")]


# ---------------------------------------------------------------- drawing
def tag_circle(svg, x, y, label, r=0.95):
    svg.circle(x, y, r, fill="#ffffff", stroke=INK, sw=0.7)
    svg.text(x, y, label, 6.4, weight=700, ls=0.2, extra='dy="2.3"')


def tag_diamond(svg, x, y, label, r=1.15):
    svg.poly([(x - r, y), (x, y + r * 0.8), (x + r, y), (x, y - r * 0.8)], fill="#ffffff", stroke=INK, sw=0.7)
    svg.text(x, y, label, 5.6, weight=700, ls=0.1, extra='dy="2"')


def fixture_notes(svg, plan):
    for f in plan.get("fixtures", []):
        if not f.get("note") or "rect" not in f:
            continue
        x0, y0, x1, y1 = f["rect"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        X, Y = svg.X(cx), svg.Y(cy)
        rot = -90 if (y1 - y0) > (x1 - x0) * 1.3 else 0
        room = max(x1 - x0, y1 - y0) * svg.s
        if len(f["note"]) * 5.2 * 0.56 > room:          # skip a note that does not fit its fixture
            continue
        svg.add(f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{C.FONT}" font-size="5.2" fill="{MID}" text-anchor="middle" '
                f'dy="2" transform="rotate({rot} {X:.1f} {Y:.1f})">{f["note"]}</text>')


def room_tags(svg, plan, fs=8.6):
    for r in plan["rooms"]:
        if r.get("label") is False:
            continue
        x0, y0, x1, y1 = r["rect"]
        lx, ly = r.get("lab", ((x0 + x1) / 2, (y0 + y1) / 2))
        narrow = (x1 - x0) < 7.5
        name = r.get("short", r["name"]) if narrow else r["name"]
        area = (x1 - x0) * (y1 - y0)
        svg.text(lx, ly, name.upper(), fs * (0.9 if narrow else 1.0), weight=700, ls=0.8, extra='dy="-2"')
        size = f"{area:,.0f} sf" if narrow else f"{fmt(x1 - x0)} × {fmt(y1 - y0)} · {area:,.0f} sf"
        if r.get("outdoor"):
            size += " · not floor area"
        svg.text(lx, ly, size, fs * 0.8, fill=MID, extra=f'dy="{fs * 1.05:.1f}"')
        if r.get("note") and not narrow:
            svg.text(lx, ly, r["note"], fs * 0.74, fill=MID, extra=f'dy="{fs * 2.1:.1f}"')


def chain(svg, pts, axis, at, off):
    """Dimension string through pts along x (axis "x", at y=at) or y (axis "y", at x=at), offset off, plus overall."""
    for a, b in zip(pts, pts[1:]):
        if axis == "x":
            svg.dim(a, at, b, at, off, size=7.6)
        else:
            svg.dim(at, a, at, b, off, size=7.6, horizontal=False)
    k = 1 if off > 0 else -1
    if axis == "x":
        svg.dim(pts[0], at, pts[-1], at, off + k * 2.3, size=8.2)
    else:
        svg.dim(at, pts[0], at, pts[-1], off + k * 2.3, size=8.2, horizontal=False)


def tag_positions(plan, doors, wins):
    """Where each tag goes, in the home's frame: doors outside an exterior wall or on the larger room's side
    (the hall, not the closet) unless another tag is there; windows outside. Shared with the AutoCAD export."""
    placed, out = [], []

    def free(x, y):
        return all(math.hypot(x - a, y - b) > 2.1 for a, b in placed)
    for d in doors:
        (cx, cy), (nx, ny) = d["p"], d["n"]
        if d["ext"]:
            tx, ty = cx - nx * 1.8, cy - ny * 1.8
        else:
            k = 1.0 if room_area(plan, d["left"]) >= room_area(plan, d["right"]) else -1.0
            tx, ty = cx + nx * k * 1.3, cy + ny * k * 1.3
            if not free(tx, ty):
                tx, ty = cx - nx * k * 1.3, cy - ny * k * 1.3
        placed.append((tx, ty))
        out.append(("door", d["tag"], tx, ty))
    for w_ in wins:
        (cx, cy), (nx, ny) = w_["p"], w_["n"]
        out.append(("window", w_["tag"], cx - nx * 2.0, cy - ny * 2.0))
    return out


def plan_svg(sh, doors, wins, scale=17.0):
    plan = sh["plan"]
    W, D = plan["W"], plan["D"]
    svg = DR.SVG(-8.2, -9.8, W + 9.5, D + (7.2 if sh["chains"].get("back") else (5.0 if plan.get("sunshade") else 3.0)),
                 scale=scale, pad=10)
    C.draw_plan(svg, plan, None, "full", fs=8.2, labels=False)
    room_tags(svg, plan)
    fixture_notes(svg, plan)
    for kind, label, x, y in tag_positions(plan, doors, wins):
        (tag_circle if kind == "door" else tag_diamond)(svg, x, y, label)
    ch = sh["chains"]
    chain(svg, ch["front"], "x", 0.0, -3.6)
    chain(svg, ch["west"], "y", 0.0, -3.4)
    chain(svg, ch["east"], "y", W, 3.4)
    if ch.get("back"):
        chain(svg, ch["back"], "x", D, 3.0)
    svg.text(W / 2, -9.0, "FRONT", 7.0, fill=MID, ls=1.4)
    lan = plan.get("lantern")
    if lan and not lan.get("upper_only"):               # leader to the cobogó screen
        svg.leader(lan["x"][1] - 0.4, (lan["y"][0] + lan["y"][1]) / 2, W + 1.0, -2.0,
                   "COBOGÓ SCREEN" + (", 2 STORIES" if lan.get("opening") is None else ""), size=6.2)
    svg.text(W + 6.9, D / 2, "", 6)
    X, Y = svg.X(W + 7.3), svg.Y(D * 0.5)
    svg.add(f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{C.FONT}" font-size="6.4" fill="{MID}" letter-spacing="1.2" '
            f'text-anchor="middle" transform="rotate(90 {X:.1f} {Y:.1f})">SHARED WALL OF A PAIR · 1-HOUR, NO OPENINGS</text>'
            if plan not in (H.CASA02_GF_SUITE, H.CASA02_GF_SIDE) else
            f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{C.FONT}" font-size="6.4" fill="{MID}" letter-spacing="1.2" '
            f'text-anchor="middle" transform="rotate(90 {X:.1f} {Y:.1f})">OUTER SIDE · DETACHED SITES (L4-D2, L4-T1)</text>')
    return C.svg_str(svg)


# ---------------------------------------------------------------- sheets
CSS = C.CSS + """
.ap{display:grid;grid-template-columns:auto 1fr;gap:.28in;min-height:0}
.ap .s{height:9.55in;display:flex;align-items:flex-start}
.ap .s svg{height:100%;width:auto}
.ap .r{display:grid;gap:.13in;align-content:start;min-width:0}
.sch{border-collapse:collapse;width:100%;font-size:9px}
.sch th{text-align:left;font-size:8px;letter-spacing:.08em;text-transform:uppercase;border-bottom:1.2px solid #1b1d1f;
        padding:2px 4px}
.sch td{border-bottom:1px solid #ebe6da;padding:2px 4px;vertical-align:top}
.sch td:first-child{font-weight:700;white-space:nowrap}
.gn{font-size:9.4px;line-height:1.38;margin:0;padding-left:15px}
.gn li{margin:0 0 2px}
.ar{display:flex;gap:18px;font-size:10px}
.evs{display:grid;grid-template-columns:1fr 1fr;gap:.3in;min-height:0;align-items:center}
.ev{display:flex;flex-direction:column;gap:6px;min-height:0}
.ev .s svg{width:100%;height:auto;max-height:7.4in}
.dtl{display:flex;justify-content:space-between;border-top:1.5px solid #1b1d1f;padding-top:5px;font-size:10px}
.dtl b{font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.dtl span{color:#5b625b}
.ar b{font-size:15px;display:block}
"""

GENERAL = [
    "Dimensions to the outside face of exterior walls and the centreline of partitions; areas the same way.",
    "Ceilings 9'-6\" on the ground floor, 9'-0\" upstairs. Doors 8'-0\" high; window heads at 8'-6\".",
    "Stair: 17 risers at 7 7/16 in (10'-6\" floor to floor), 16 treads at 10 1/8 in, 3'-3 3/4\" clear. Open oak "
    "treads with a riser bar (4 in sphere rule); wall handrail at 34–38 in; cedar slats on the open side, 4 in max "
    "gaps.",
    "Shared wall of a pair: 1-hour fire-resistance-rated, STC 50 or better, continuous to the roof deck, with no "
    "openings. Windows go on the front, back and outer side only; vent the dryer and the bath fans through the roof "
    "or the outer wall.",
    "Visitability (City of Austin, confirm at permit): a no-step entry, ground-floor doors with at least 30 in clear "
    "(the WC door 32 in), a ground-floor WC with a 30 × 48 in clear floor space, blocking for grab bars, switches at "
    "48 in max and outlets at 15 in min.",
    "Bedrooms have an egress window (5.7 sf clear, sill under 44 in). Smoke and CO alarms in each bedroom, the hall "
    "and each floor, interconnected.",
    "Mechanical closet under the top of the stair: air handler and a heat-pump water heater; louvred door, and duct "
    "the water heater if the closet has under 700 cu ft of air.",
]

SHEET_NOTES = {
    "A-101": ["The front door and the carport door both open into the gallery hall; the hall leads straight to the "
              "kitchen, past a built-in bench, coat hooks and a floor-to-ceiling pantry.",
              "The stair rises from the kitchen toward the front and lands upstairs behind the cobogó.",
              "Carport: open bay under the upper floor, open on the street and outer sides; a 9 ft cedar slat gate, "
              "a Lueders limestone pier at the corner and one steel column carry the floor above.",
              "Lueders limestone ashlar on the outer wall of the kitchen and living room. Black calçada rug at the "
              "carport door and a calçada threshold under the cobogó (about 58 sf, all under the house)."],
    "A-102": ["For wide lots where the car parks on a pad: the bay becomes a bedroom suite with its own bath.",
              "Drawn for a detached site (L4-D2), so the outer long wall takes an 8 ft slider to the side pátio. In a "
              "pair, that wall is the shared wall: no openings.",
              "Lueders limestone ashlar on the whole outer side and on the suite's street wall, as at Casa 01; a "
              "calçada threshold under the cobogó."],
    "A-104": ["For homes in a row on a shared drive (the 65-ft trio, L4-T1): the bay runs across the front and the car "
              "enters from the drive through a cedar gate. Upper floor as A-103.",
              "The street sees a full Lueders limestone wall with the cobogó above it on the upper floor only.",
              "You enter through the bay on a calçada walk; the living room opens east to its own pátio through an "
              "8 ft slider, and the back wall, 5 ft from the next home, takes a band of high windows."],
    "A-103": ["The stair lands at the front, in a bright landing behind the cobogó (room for a desk); the hall runs "
              "back along the open stair to the primary suite.",
              "Bath 2 sits between the two front bedrooms on the outer wall, with a window. Laundry upstairs, beside "
              "the bedrooms.",
              "Bed 3 becomes the den when the suite version is built downstairs."],
}


def title_block(sheet, title):
    return (f'<aside class="tb"><div class="brand">Brazilian Modern Homes<small>Residential design · Austin</small></div>'
            f'<div class="proj">Phase 2<br>Casa 02<small>Developed floor plans</small></div>'
            f'<div class="grow"></div><div class="kv"><span>Sheet title</span><b>{title}</b><span>Scale</span>'
            f'<b>Plan to scale</b><span>Date / phase</span><b>Nov 2026 · Design development</b></div>'
            f'<div class="sheet">{sheet}</div><div class="warn">Design development. Not for construction.</div></aside>')


def table(head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="sch"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def sheet_html(sh):
    plan = sh["plan"]
    doors, wins = openings(plan, sh["floor"])
    a = H.area_summary()
    if plan is H.CASA02_GF_CARPORT:
        areas = [("Ground floor", f"{a['carport_gf']:,.0f} sf"), ("Carport", "210 sf, not floor area"),
                 ("Home total", f"{a['carport_total']:,.0f} sf · 3 bed / 2.5 bath")]
    elif plan is H.CASA02_GF_SIDE:
        areas = [("Ground floor", f"{plan['enclosed']:,.0f} sf"), ("Carport", "210 sf, not floor area"),
                 ("Home total", f"{plan['enclosed'] + a['upper']:,.0f} sf · 3 bed / 2.5 bath")]
    elif plan is H.CASA02_GF_SUITE:
        areas = [("Ground floor", f"{a['suite_gf']:,.0f} sf"), ("Home total", f"{a['suite_total']:,.0f} sf"),
                 ("Bedrooms", "3 bed + den / 3.5 bath")]
    else:
        areas = [("Upper floor", f"{a['upper']:,.0f} sf"), ("With carport floor", f"{a['carport_total']:,.0f} sf"),
                 ("With suite floor", f"{a['suite_total']:,.0f} sf")]
    ar = "".join(f"<div>{k}<b>{v}</b></div>" for k, v in areas)
    dt = table(["Door", "From → to", "Size", "Type", "Notes"], [door_row(d, plan) for d in doors])
    wt = table(["Window", "Room", "Size", "Sill", "Head", "Notes"], [win_row(w_, plan) for w_ in wins])
    notes = "".join(f"<li>{t}</li>" for t in SHEET_NOTES[sh["no"]])
    gen = "".join(f"<li>{t}</li>" for t in GENERAL)
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr">'
            f'<h1>Casa 02 · {sh["title"]}</h1>'
            f'<div class="ap"><div class="s">{plan_svg(sh, doors, wins)}</div><div class="r">'
            f'<div class="ar">{ar}</div>'
            f'<div><h2>This floor</h2><ul class="gn">{notes}</ul></div>'
            f'<div><h2>Doors</h2>{dt}</div><div><h2>Windows</h2>{wt}</div>'
            f'<div><h2>General notes</h2><ul class="gn">{gen}</ul></div>'
            f'<p class="lead" style="font-size:9px;color:#5b625b">Circle: door tag. Diamond: window tag. Dashed: '
            f'overhead (the upper floor over the carport, the top of the stair, the cobogó header). Dotted cedar '
            f'line: cedar slats. Stone band: Lueders limestone ashlar. Dark rug: calçada portuguesa.</p></div></div></div>{title_block(sh["no"], sh["title"])}</section>')


ELEV_SHEETS = [
    ("A-201", "Casa 02 elevations · front and back", [("front_gc", "Front, carport version"), ("back_gc", "Back, toward the pátio")],
     ["Front: the cobogó lantern rises both floors over the entry and stair; a Lueders limestone pier wraps the "
      "carport corner; cedar slat gate.", "Back: a 16 ft slider under a cedar slat sunshade; the primary bedroom "
      "window above; skylight curbs on the roof."]),
    ("A-202", "Casa 02 elevations · sides", [("side_gc", "Outer side, carport version"), ("side_gd", "Drive side, side-drive version")],
     ["The shared wall of a pair has no openings (not shown). The outer side: open carport with one steel column, the "
      "stone wall turning the corner, stucco above.", "Side-drive version: the cedar gate opens the bay to the drive."]),
    ("A-203", "Casa 02 elevations · other fronts", [("front_gs", "Front, suite version"), ("front_gd", "Front, side-drive version")],
     ["Suite version: the suite's street wall in limestone with its egress window, as Casa 01's street wall.",
      "Side-drive version: a full limestone wall at the street, the cobogó on the upper floor only."]),
    ("A-204", "Casita elevations", [("cs_front", "Front"), ("cs_side", "Porch side")],
     ["One story, 12'-3\" to the roof edge; covered porch with a cedar ceiling on two bronze posts.",
      "Calçada stoop at the front door; skylights over the shower, the hall and the closet."]),
    ("A-301", "Sections", [("sect_a", "Section A, through the stair"), ("cs_sect", "Section C, Casita living + porch")],
     ["Section A: the open oak stair rises from the kitchen to the landing behind the cobogó, under a skylight that "
      "lights both floors; skylights over the laundry, the walk-in and the primary shower.",
      "Section C: the living room opens under the porch through a 10 ft slider."]),
]


def elev_sheet(no, title, items, notes):
    import elevations as EL
    dr = EL.all_drawings()
    cells = "".join(f'<div class="ev"><div class="s">{EL.to_svg(dr[k])}</div><div class="dtl"><b>{t}</b>'
                    f'<span>Scale to fit · feet above grade</span></div></div>' for k, t in items)
    li = "".join(f"<li>{t}</li>" for t in notes)
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr auto">'
            f'<h1>{title}</h1><div class="evs">{cells}</div><ul class="gn">{li}</ul></div>'
            f'{title_block(no, title.split(" · ")[-1].capitalize() if " · " in title else title)}</section>')


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = [sheet_html(sh) for sh in sorted(SHEETS, key=lambda x: x["no"])]
    pages += [elev_sheet(*e) for e in ELEV_SHEETS]
    for sh in SHEETS:
        d, w_ = openings(sh["plan"], sh["floor"])
        print(sh["no"], len(d), "doors", len(w_), "windows")
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Casa 02 plans</title>'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(os.path.join(OUT, "plans.html"), "w").write(html)
    print("wrote", os.path.join(OUT, "plans.html"))


if __name__ == "__main__":
    main()
