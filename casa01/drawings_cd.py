"""Construction-document style drawings (SketchUp LayOut / blueprint style) from design.py.

    python3 casa01/drawings_cd.py   ->  casa01/drawings/3*_*.svg + schedules.json

Technical linework only: dimension chains, grid bubbles, hatched walls, door and window
tags with schedules, numbered room tags, keynotes, section/elevation markers, roof plan.
"""
import json
import math
import os

import design as D
from drawings import (SVG, fmt_ft, hatch_defs, wall_rects, north_arrow, scale_bar, cobogo_elev,
                      limestone_courses, ground, human, FONT, INK, MID, LIGHT, GOLD, OUT)

LINE = "#111315"

# ------------------------------------------------------------------ data: tags & schedules
ROOM_NO = {"Living": 101, "Dining": 102, "Kitchen": 103, "Laundry": 104, "Primary Bedroom": 105, "Walk-in": 106,
           "Primary Bath": 107, "Bedroom 3": 108, "Bath 2": 109, "Bedroom 2": 110, "Gallery": 111}


def openings_schedule():
    """Doors (D#) and windows (W-#) from the design's openings."""
    doors, wins = [], []
    dn = 1
    wtypes = {}
    for w in D.EXT_WALLS:
        ax, ay = w["a"]
        bx, by = w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        for o in w["openings"]:
            cx, cy = ax + ux * (o["off"] + o["w"] / 2), ay + uy * (o["off"] + o["w"] / 2)
            h = o["head"] - o["sill"]
            if o["kind"] in ("pivot", "slider") and o["sill"] == 0 and "Gallery" not in o["name"]:
                typ = "Cedar-clad pivot, steel frame" if o["kind"] == "pivot" else f"{o.get('panels', 2)}-panel sliding glass"
                doors.append(dict(tag=f"D{dn}", name=o["name"], w=o["w"], h=h, type=typ,
                                  mat="Cedar / steel" if o["kind"] == "pivot" else "Dk. bronze alum., low-E",
                                  x=cx, y=cy, wall=w["id"]))
                dn += 1
            else:
                key = (o["kind"], round(o["w"], 2), round(h, 2))
                if key not in wtypes:
                    wtypes[key] = f"W-{len(wtypes) + 1}"
                wins.append(dict(tag=wtypes[key], name=o["name"], w=o["w"], h=h, sill=o["sill"], kind=o["kind"],
                                 x=cx, y=cy, wall=w["id"]))
    for p in D.PARTITIONS:
        ax, ay = p["a"]
        bx, by = p["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        for o in p["openings"]:
            cx, cy = ax + ux * (o["off"] + o["w"] / 2), ay + uy * (o["off"] + o["w"] / 2)
            if o["kind"] == "closet":
                doors.append(dict(tag=f"D{dn}", name="Closet", w=o["w"], h=8.0, type="Bypass sliding, 2 leaf",
                                  mat="Rift oak veneer", x=cx, y=cy))
            else:
                doors.append(dict(tag=f"D{dn}", name=o.get("name", "Interior"), w=o["w"], h=8.0,
                                  type="Flush, solid core", mat="Rift oak veneer", x=cx, y=cy))
            dn += 1
    g = D.ENTRY_GATE
    doors.append(dict(tag=f"D{dn}", name="Entry gate", w=g["x1"] - g["x0"], h=g["z1"] - g["z0"],
                      type="Pivot gate, cedar slats", mat="Cedar / steel", x=(g["x0"] + g["x1"]) / 2, y=g["y"]))
    cg = getattr(D, "CARPORT_GATE", None)
    if cg:
        dn += 1
        doors.append(dict(tag=f"D{dn}", name="Carport gate", w=cg["y1"] - cg["y0"], h=cg["z1"] - cg["z0"],
                          type="Swing gate, cedar slats", mat="Cedar / steel", x=cg["x"], y=(cg["y0"] + cg["y1"]) / 2,
                          wall="carport"))
    sl = getattr(D, "CARPORT_SLIDER", None)
    if sl and sl.get("installed", True):
        dn += 1
        doors.append(dict(tag=f"D{dn}", name="Carport sliding gate", w=sl["x1"] - sl["x0"], h=sl["z1"] - sl["z0"],
                          type="Sliding gate, cedar slats, motorized (add alt. 1)", mat="Cedar / steel",
                          x=(sl["x0"] + sl["x1"]) / 2, y=sl["y"], wall="carport-front"))
    return doors, wins


KEYNOTES = [
    "12x12x4 precast concrete cobogó screen, white cement, on cast curb",
    "Cedar slat pivot gate on dark bronze steel frame",
    "Lueders limestone veneer, sawn-face ashlar",
    "Cedar 2x4 slat screen @ 5\" o.c. on steel rails",
    "Black calçada portuguesa, 6\" light concrete band (50 sf)",
    "Limestone pavers 24x36, thermal finish",
    "Polished concrete slab, all interior floors",
    "Roof edge above, 15\" dark bronze fascia (dashed)",
    "4\" sq. HSS steel post, dark bronze",
    "Limestone-clad grill counter (churrasqueira)",
    "Courtyard planting bed + tree",
    "Walk-in shower, green zellige-look porcelain to ceiling",
    "Carport: concrete slab under the main roof, open to the drive",
    "AC condenser pad: 1 outdoor heat pump (2 concealed air handlers inside)",
    "Skylight above (low-slope roof)",
    "Dropped ceiling 8'-6\" for ducts + air handler (dash-dot); living spaces stay 10'-0\"",
    "Add alternate 1: motorized sliding cedar gate; parks behind the cobogó when open (dashed)",
    "Gate rough-in, built with the slab: 12\" concrete track strip, motor pad, conduit to house + east post",
    "Tub with fixed glass panel; terracotta zellige-look porcelain to the ceiling, tiled niche",
]


def cd_defs(svg):
    hatch_defs(svg)
    svg.defs.append('<pattern id="wallh" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                    '<rect width="6" height="6" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="6" stroke="#111315" '
                    'stroke-width="0.9"/></pattern>')
    svg.defs.append('<pattern id="stoneh" width="8" height="8" patternUnits="userSpaceOnUse">'
                    '<rect width="8" height="8" fill="#ffffff"/><path d="M0 0 L8 8 M8 0 L0 8" stroke="#111315" '
                    'stroke-width="0.7"/></pattern>')
    svg.defs.append('<pattern id="cdmosaic" width="7" height="7" patternUnits="userSpaceOnUse">'
                    '<rect width="7" height="7" fill="#ffffff"/><path d="M0 2 L3 0 L7 3 M2 7 L4 4 L7 6 M0 5 L3 4" '
                    'stroke="#6b6f73" stroke-width="0.5" fill="none"/></pattern>')
    svg.defs.append('<pattern id="paverh" width="18" height="12" patternUnits="userSpaceOnUse">'
                    '<rect width="18" height="12" fill="#ffffff"/><path d="M0 0 H18 M0 0 V12" stroke="#9a9ea2" '
                    'stroke-width="0.5"/></pattern>')
    svg.defs.append('<pattern id="tileh" width="5" height="5" patternUnits="userSpaceOnUse">'
                    '<rect width="5" height="5" fill="#ffffff"/><path d="M0 0 H5 M0 0 V5" stroke="#9a9ea2" '
                    'stroke-width="0.5"/></pattern>')


def tag_circle(svg, x, y, txt, r=0.95, size=8.5):
    svg.circle(x, y, r, fill="#ffffff", stroke=LINE, sw=1.0)
    svg.text(x, y, txt, size, weight=700, ls=0.3, extra='dy="3"')


def tag_hex(svg, x, y, txt, size=8):
    s = svg.s
    X, Y = svg.X(x), svg.Y(y)
    w, h = 15, 8
    pts = [(X - w, Y), (X - w + 5, Y - h), (X + w - 5, Y - h), (X + w, Y), (X + w - 5, Y + h), (X - w + 5, Y + h)]
    svg.add('<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) +
            f'" fill="#ffffff" stroke="{LINE}" stroke-width="1"/>')
    svg.add(f'<text x="{X:.1f}" y="{Y + 3:.1f}" font-family="{FONT}" font-size="{size}" text-anchor="middle" '
            f'font-weight="700" fill="{LINE}">{txt}</text>')


def keynote(svg, x, y, n, lx=None, ly=None):
    if lx is not None:
        svg.line(x, y, lx, ly, MID, 0.6)
        svg.add(f'<circle cx="{svg.X(x):.1f}" cy="{svg.Y(y):.1f}" r="2.2" fill="{LINE}"/>')
        x, y = lx, ly
    X, Y = svg.X(x), svg.Y(y)
    svg.add(f'<polygon points="{X:.1f},{Y - 9:.1f} {X + 9:.1f},{Y:.1f} {X:.1f},{Y + 9:.1f} {X - 9:.1f},{Y:.1f}" '
            f'fill="#ffffff" stroke="{LINE}" stroke-width="1"/>')
    svg.add(f'<text x="{X:.1f}" y="{Y + 3.2:.1f}" font-family="{FONT}" font-size="8" text-anchor="middle" '
            f'font-weight="700" fill="{LINE}">{n}</text>')


def grid(svg, xs, ys, xr, yr):
    for i, x in enumerate(xs):
        svg.line(x, yr[0], x, yr[1], "#7b8085", 0.6, extra='stroke-dasharray="14 4 3 4"')
        for yy in (yr[0] - 1.4, yr[1] + 1.4):
            svg.circle(x, yy, 1.4, fill="#ffffff", stroke=LINE, sw=1.0)
            svg.text(x, yy, "ABCDEFG"[i], 10, weight=700, extra='dy="3.5"')
    for i, y in enumerate(ys):
        svg.line(xr[0], y, xr[1], y, "#7b8085", 0.6, extra='stroke-dasharray="14 4 3 4"')
        for xx in (xr[0] - 1.4, xr[1] + 1.4):
            svg.circle(xx, y, 1.4, fill="#ffffff", stroke=LINE, sw=1.0)
            svg.text(xx, y, str(i + 1), 10, weight=700, extra='dy="3.5"')


def chain(svg, pts, at, horizontal, off, size=8):
    pts = sorted(set(round(p, 3) for p in pts))
    segs = [(a, b) for a, b in zip(pts, pts[1:]) if b - a >= 0.2]
    for i, (a, b) in enumerate(segs):
        lab = fmt_ft(b - a)
        L = len(lab) * (0.6 * size + 0.6) / svg.s          # label length in feet
        if L <= (b - a) + 0.15:
            if horizontal:
                svg.dim(a, at, b, at, off, size=size)
            else:
                svg.dim(at, a, at, b, off, horizontal=False, size=size)
            continue
        # label wider than its segment: past the chain's end, or on the other side of the line
        if horizontal:
            svg.dim(a, at, b, at, off, label=" ", size=size)
        else:
            svg.dim(at, a, at, b, off, label=" ", horizontal=False, size=size)
        if i == len(segs) - 1:
            c, dy = b + L / 2 + 0.35, -3
        elif i == 0:
            c, dy = a - L / 2 - 0.35, -3
        else:
            c, dy = (a + b) / 2, size + 2
        if horizontal:
            svg.text(c, at + off, lab, size, extra=f'dy="{dy}"')
        else:
            X, Y = svg.X(at + off), svg.Y(c)
            svg.add(f'<text x="{X:.2f}" y="{Y:.2f}" font-family="{FONT}" font-size="{size}" text-anchor="middle" '
                    f'fill="{INK}" letter-spacing="0.6" transform="rotate(-90 {X:.2f} {Y:.2f})" dy="{dy}">{lab}</text>')


def elev_marker(svg, x, y, n, sheet, dirn):
    """circle with a solid triangle pointing at the elevation."""
    X, Y = svg.X(x), svg.Y(y)
    ang = {"n": -90, "s": 90, "e": 0, "w": 180}[dirn]
    svg.add(f'<g transform="translate({X:.1f},{Y:.1f})"><g transform="rotate({ang})">'
            f'<path d="M 11 -9 L 22 0 L 11 9 Z" fill="{LINE}"/></g>'
            f'<circle r="11" fill="#ffffff" stroke="{LINE}" stroke-width="1.2"/>'
            f'<line x1="-11" y1="0" x2="11" y2="0" stroke="{LINE}" stroke-width="0.8"/>'
            f'<text y="-2" font-family="{FONT}" font-size="8" font-weight="700" text-anchor="middle" fill="{LINE}">{n}</text>'
            f'<text y="8" font-family="{FONT}" font-size="6.5" text-anchor="middle" fill="{LINE}">{sheet}</text></g>')


# ------------------------------------------------------------------ floor plan (CD)
def floor_plan_cd():
    svg = SVG(-14, 12, 78, 107, scale=11.2, pad=18)
    cd_defs(svg)
    svg.layer = "L-PAVE"
    # outdoor hardscape, light linework only
    for pv in D.PAVING:
        svg.rect(*pv["rect"], fill="url(#paverh)", stroke=MID if pv["name"] == "Veranda" else "none", sw=0.6)
    cp = getattr(D, "CARPORT", None)
    if cp:   # carport slab + a car outline for scale
        svg.rect(cp["x0"], cp["y0"], cp["x1"], cp["y1"], fill="#f4f4f2", stroke=MID, sw=0.6)
        cx, cy = (cp["x0"] + cp["x1"]) / 2, cp["y0"] + 9.6
        svg.rect(cx - 3.1, cy - 7.75, cx + 3.1, cy + 7.75, fill="none", stroke=MID, sw=0.6, extra='stroke-dasharray="5 3"')
        svg.text(cx, cy, "CAR", 7, fill=MID, ls=1.5, extra='dy="2.5"')
    em = D.ENTRY_MOSAIC
    svg.rect(em["x0"] + em["band"], em["y0"] + em["band"], em["x1"] - em["band"], em["y1"] - em["band"],
             fill="url(#cdmosaic)", stroke=LINE, sw=0.7)
    svg.layer = "L-PLNT"
    for pl in D.PLANTING:
        if pl["name"] in ("Courtyard garden", "Primary garden"):
            svg.poly(pl["poly"], fill="none", stroke=MID, sw=0.6, extra='stroke-dasharray="4 3"')
    B = D.PRIMARY_BATH
    sx0, sy0, sx1, sy1 = B["shower"]
    svg.layer = "A-FLOR-PATT"
    svg.rect(sx0, sy0, sx1, sy1, fill="url(#tileh)", stroke="none")
    hb = getattr(D, "HALL_BATH", None)
    if hb:   # fixed glass panel on the tub edge
        svg.layer = "A-GLAZ"
        gx, gy0, gy1 = hb["glass"]
        svg.line(gx, gy0 + 0.1, gx, gy1, "#5d8fa0", 2.0)
    # built-ins / fixtures only (no loose furniture on a CD plan)
    for it in D.FURNITURE:
        t = it["t"]
        x, y = it["x"], it["y"]
        w, d = it.get("w", 2), it.get("d", 2)
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - d / 2, y + d / 2
        svg.layer = ("P-FIXT" if t in ("tub", "shower", "vanity", "wc", "wc_wall") else "A-FLOR-APPL" if t in ("washer", "dryer") else "A-FLOR-CASE")
        if t in ("counter", "tall", "island", "credenza", "grill_counter"):
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=LINE, sw=0.8)
            if t == "tall":
                svg.line(x0, y0, x1, y1, MID, 0.5); svg.line(x0, y1, x1, y0, MID, 0.5)
            if t == "counter" and w > d:
                svg.rect(x - 1.4, y - 0.7, x + 1.4, y + 0.7, stroke=MID, sw=0.6)
            if t == "counter" and d > w:
                for cy in (y + 1.0, y + 2.2):
                    for cx in (x - 0.45, x + 0.45):
                        svg.circle(cx, cy, 0.32, stroke=MID, sw=0.6)
        elif t in ("tub", "shower"):
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=LINE, sw=0.8)
            svg.rect(x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, stroke=MID, sw=0.5)
        elif t == "vanity":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=LINE, sw=0.8)
            svg.circle(x, y, 0.5, stroke=MID, sw=0.6)
        elif t in ("wc", "wc_wall"):
            svg.circle(x, y, 0.65, stroke=LINE, sw=0.8)
        elif t in ("washer", "dryer"):
            svg.rect(x - 1.2, y - 1.2, x + 1.2, y + 1.2, fill="#ffffff", stroke=LINE, sw=0.8)
            lab = it.get("label") or ("W" if t == "washer" else "D")
            svg.add(f'<text x="{svg.X(x):.1f}" y="{svg.Y(y) + 3:.1f}" font-family="{FONT}" font-size="7" '
                    f'text-anchor="middle" fill="{MID}">{lab}</text>')
        elif t == "wh":
            svg.circle(x, y, 0.95, fill="#ffffff", stroke=LINE, sw=0.8)
            svg.add(f'<text x="{svg.X(x):.1f}" y="{svg.Y(y) + 3:.1f}" font-family="{FONT}" font-size="6.5" '
                    f'text-anchor="middle" fill="{MID}">WH</text>')
    gx0, gx1, gy = B["glass"]
    svg.layer = "A-GLAZ"
    svg.line(gx0, gy, gx1, gy, LINE, 1.6)
    bx0, by0, bx1, by1 = B["bench"]
    svg.layer = "A-FLOR-CASE"
    svg.rect(bx0, by0, bx1, by1, fill="#ffffff", stroke=LINE, sw=0.8)
    vx0, vy0, vx1, vy1 = B["vanity"]
    svg.rect(vx0, vy0, vx1, vy1, fill="#ffffff", stroke=LINE, sw=0.8)
    svg.layer = "P-FIXT"
    svg.circle(*B["sink"], 0.62, stroke=LINE, sw=0.8)
    rx1 = B["room"][2]
    svg.rect(rx1 - 1.3, 72.88, rx1, 73.52, fill="#ffffff", stroke=LINE, sw=0.8)
    svg.circle(rx1 - 1.05, 73.2, 0.3, stroke=LINE, sw=0.7)
    svg.layer = "A-ROOF-OTLN"
    # roof edge above + courtyard tree (thin)
    svg.poly(D.ROOF, fill="none", stroke=LINE, sw=0.8, extra='stroke-dasharray="10 4 2 4"')
    # walls: exterior hatched, partitions gray, limestone cross-hatched
    for w in D.EXT_WALLS:
        rects, spans, rect, (ux, uy, nx, ny) = wall_rects(w, D.EXT_T)
        svg.layer = "A-WALL"
        for r in rects:
            svg.rect(*r, fill="url(#wallh)", stroke=LINE, sw=1.3)
        for o in spans:
            s0, s1 = o["off"], o["off"] + o["w"]
            svg.layer = ("A-GLAZ" if o["kind"] in ("fixed", "casement") else "A-DOOR")
            if o["kind"] == "pivot":
                piv = s0 + o["w"] * 0.25
                ax, ay = w["a"]
                px, py = ax + ux * piv + nx * 0.25, ay + uy * piv + ny * 0.25
                svg.line(px, py, px + nx * 3.0, py + ny * 3.0, LINE, 1.6)
                svg.line(px, py, px - nx * 1.0, py - ny * 1.0, LINE, 1.6)
                continue
            for dd in (0.04, D.EXT_T - 0.04):
                xa, ya, xb, yb = rect(s0, s1, dd, dd)
                svg.line(xa, ya, xb, yb, LINE, 0.9)
            xa, ya, xb, yb = rect(s0, s1, D.EXT_T / 2, D.EXT_T / 2)
            svg.line(xa, ya, xb, yb, LINE, 0.5)
            for e in (s0, s1):
                xa, ya, xb, yb = rect(e, e, 0, D.EXT_T)
                svg.line(xa, ya, xb, yb, LINE, 1.3)
            n = o.get("panels", 1)
            for k in range(1, n):
                xa, ya, xb, yb = rect(s0 + k * o["w"] / n, s0 + k * o["w"] / n, 0.1, D.EXT_T - 0.1)
                svg.line(xa, ya, xb, yb, LINE, 1.0)
    svg.layer = "A-WALL-STONE"
    lw = D.LIMESTONE_WALL
    hole = D.EXT_WALLS[0]["openings"][0]
    hx0 = D.EXT_WALLS[0]["a"][0] + hole["off"]
    for (a, b) in ((lw["x0"], hx0), (hx0 + hole["w"], lw["x1"])):
        svg.rect(a, lw["y_face"], b, lw["y_back"], fill="url(#stoneh)", stroke=LINE, sw=1.1)
    for p in D.PARTITIONS:
        (ax, ay), (bx, by) = p["a"], p["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        t = D.INT_T / 2
        s = 0.0
        for o in sorted(p["openings"], key=lambda o: o["off"]) + [None]:
            e = o["off"] if o else L
            if e - s > 1e-6:
                svg.layer = "A-WALL-INTR"
                xs = [ax + ux * s + nx * t, ax + ux * e - nx * t]
                ys = [ay + uy * s + ny * t, ay + uy * e - ny * t]
                svg.rect(min(xs), min(ys), max(xs), max(ys), fill="#c9cbcd", stroke=LINE, sw=0.9)
            if o:
                s0 = o["off"]
                svg.layer = "A-DOOR"
                if o["kind"] == "closet":
                    for k, dd in enumerate((-0.07, 0.07)):
                        a0 = s0 + k * o["w"] / 2 - 0.05
                        a1 = a0 + o["w"] / 2 + 0.1
                        svg.line(ax + ux * a0 + nx * dd, ay + uy * a0 + ny * dd,
                                 ax + ux * a1 + nx * dd, ay + uy * a1 + ny * dd, LINE, 1.0)
                else:
                    sw_ = o.get("swing", 1)
                    hx, hy = ax + ux * s0, ay + uy * s0
                    lx, ly = hx + nx * o["w"] * sw_, hy + ny * o["w"] * sw_
                    svg.line(hx, hy, lx, ly, LINE, 1.1)
                    a0 = math.atan2(ly - hy, lx - hx)
                    a1 = math.atan2(uy, ux)
                    da = ((a1 - a0 + math.pi) % (2 * math.pi)) - math.pi
                    svg.arc(hx, hy, o["w"], a0, a0 + da, LINE, 0.5)
                s = o["off"] + o["w"]
    # cobogó, gate, cedar screen, posts
    svg.layer = "A-WALL-COBO"
    c = D.COBOGO
    for i in range(int(c["x1"] - c["x0"])):
        x = c["x0"] + i
        svg.rect(x + 0.02, c["y"], x + 0.98, c["y"] + c["t"], fill="#ffffff", stroke=LINE, sw=0.7)
        svg.circle(x + 0.5, c["y"] + c["t"] / 2, 0.09, stroke=LINE, sw=0.4)
    svg.layer = "A-DOOR"
    g = D.ENTRY_GATE
    svg.line(g["x0"] + 0.1, g["y"] + 0.15, g["x0"] + 0.1 + 3.5 * math.cos(math.radians(55)),
             g["y"] + 0.15 + 3.5 * math.sin(math.radians(55)), LINE, 1.3)
    svg.arc(g["x0"] + 0.1, g["y"] + 0.15, 3.8, 0, math.radians(55), LINE, 0.5)
    svg.layer = "A-SCRN"
    s_ = D.CEDAR_SCREEN
    y = s_["y0"]
    while y < s_["y1"]:
        if not any(a - 0.05 < y < b for (a, b) in s_.get("openings", [])):
            svg.rect(s_["x"] - s_["slat_d"], y, s_["x"], y + s_["slat_w"], fill=LINE, stroke="none")
        y += s_["slat_w"] + s_["gap"]
    for sc in getattr(D, "SLAT_SCREENS", []):
        if sc["axis"] == "x":
            x = sc["x0"] + 0.3
            while x < sc["x1"]:
                svg.rect(x, sc["y"], x + s_["slat_w"], sc["y"] + s_["slat_d"], fill=LINE, stroke="none")
                x += s_["slat_w"] + s_["gap"]
        else:
            y = sc["y0"] + 0.1
            while y < sc["y1"] - 0.1:
                svg.rect(sc["x"] - s_["slat_d"], y, sc["x"], y + s_["slat_w"], fill=LINE, stroke="none")
                y += s_["slat_w"] + s_["gap"]
    ri = getattr(D, "GATE_ROUGH_IN", None)
    if ri:   # built either way: track strip, motor pad, conduit (dashed)
        svg.layer = "A-GATE-RGH"
        x0, x1, yc, w = ri["strip"]
        svg.rect(x0, yc - w / 2, x1, yc + w / 2, fill="none", stroke=MID, sw=0.5, extra='stroke-dasharray="3 2"')
        svg.rect(*ri["motor_pad"], fill="#ffffff", stroke=LINE, sw=0.7)
        mx0, my0, mx1, my1 = ri["motor_pad"]
        svg.line(mx0, my0, mx1, my1, MID, 0.4)
        svg.line(mx0, my1, mx1, my0, MID, 0.4)
        for run in ri["conduit"]:
            svg.pline(run, stroke=MID, sw=0.6, extra='stroke-dasharray="8 2 2 2"')
    sl = getattr(D, "CARPORT_SLIDER", None)
    if sl and not sl.get("installed", True):
        sl = None
    if sl:   # closed position: a band of slats; open position: dashed, parked behind the cobogó
        svg.layer = "A-GATE-ALT"
        x = sl["x0"] + 0.1
        while x < sl["x1"] - 0.1:
            svg.rect(x, sl["y"] - 0.12, x + s_["slat_w"], sl["y"] + 0.12, fill=LINE, stroke="none")
            x += s_["slat_w"] + s_["gap"]
        w_ = sl["x1"] - sl["x0"]
        svg.rect(sl["park_x0"], sl["y"] - 0.12, sl["park_x0"] + w_, sl["y"] + 0.12, fill="none", stroke=MID, sw=0.6,
                 extra='stroke-dasharray="4 2"')
        svg.line(sl["x0"] - 0.6, sl["y"] + 0.9, sl["park_x0"] + w_ - 2.5, sl["y"] + 0.9, MID, 0.6)
        svg.line(sl["park_x0"] + w_ - 2.5, sl["y"] + 0.9, sl["park_x0"] + w_ - 1.9, sl["y"] + 1.3, MID, 0.6)
        svg.line(sl["park_x0"] + w_ - 2.5, sl["y"] + 0.9, sl["park_x0"] + w_ - 1.9, sl["y"] + 0.5, MID, 0.6)
    cg = getattr(D, "CARPORT_GATE", None)
    if cg:   # gate leaf swings into the carport
        svg.layer = "A-DOOR"
        w_ = cg["y1"] - cg["y0"]
        svg.line(cg["x"], cg["y0"], cg["x"] + w_ * math.cos(math.radians(60)), cg["y0"] + w_ * math.sin(math.radians(60)), LINE, 1.3)
        svg.arc(cg["x"], cg["y0"], w_, math.radians(60), math.radians(90), LINE, 0.5)
    svg.layer = "S-COLS"
    for (x, y) in D.POSTS:
        svg.rect(x - 0.17, y - 0.17, x + 0.17, y + 0.17, fill=LINE, stroke=LINE, sw=0.3)
    sk = getattr(D, "SKYLIGHTS", [])
    if sk:
        svg.layer = "A-ROOF-SKYL"
        for k in sk:
            x0, y0, x1, y1 = k["rect"]
            svg.rect(x0, y0, x1, y1, fill="none", stroke=LINE, sw=0.7, extra='stroke-dasharray="6 3"')
            svg.line(x0, y0, x1, y1, MID, 0.4, extra='stroke-dasharray="6 3"')
            svg.line(x0, y1, x1, y0, MID, 0.4, extra='stroke-dasharray="6 3"')
    hv = getattr(D, "HVAC", None)
    if hv:
        svg.layer = "M-HVAC"
        for z in hv["dropped"]:
            x0, y0, x1, y1 = z["rect"]
            svg.rect(x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25, fill="none", stroke="#7b8085", sw=0.6,
                     extra='stroke-dasharray="10 3 2 3"')
        for a in hv["ahu"]:
            ax_, ay_ = a["at"]
            svg.rect(ax_ - 1.25, ay_ - 0.42, ax_ + 1.25, ay_ + 0.42, fill="#ffffff", stroke=LINE, sw=0.7,
                     extra='stroke-dasharray="4 2"')
            svg.text(ax_, ay_, a["name"], 6, weight=700, ls=0.3, extra='dy="2.2"')
        x0, y0, x1, y1 = hv["pad"]
        svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=LINE, sw=0.9)
        svg.circle((x0 + x1) / 2, (y0 + y1) / 2, 1.2, fill="none", stroke=LINE, sw=0.6)
        svg.text((x0 + x1) / 2, (y0 + y1) / 2, "AC", 6, weight=700, extra='dy="2.2"')
    # grid
    svg.layer = "A-GRID"
    part_x = D.PARTITIONS[[i for i, p in enumerate(D.PARTITIONS) if p.get("openings") and
                           any(o.get("name") == "Primary" for o in p["openings"])][0]]["a"][0]
    grid(svg, [D.BAR["x0"], D.WING["x1"], part_x, D.BAR["x1"]], [30, 60, 80], (-10.5, 72.5), (14.6, 104.2))
    # room tags
    svg.layer = "A-ANNO-ROOM"
    for r in D.ROOMS:
        if r["name"] == "Cl.":
            continue
        lx, ly = r["label"]
        no = ROOM_NO.get(r["name"], "")
        if r.get("vertical"):
            X, Y = svg.X(lx), svg.Y(ly)
            svg.add(f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{FONT}" font-size="8.5" text-anchor="middle" '
                    f'fill="{LINE}" font-weight="700" letter-spacing="1.5" transform="rotate(-90 {X:.1f} {Y:.1f})">'
                    f'GALLERY {no}</text>')
            continue
        name = r["name"].upper()
        wbox = max(len(name) * 0.62, 4.2) * (0.85 if r.get("small") else 1.0)
        svg.rect(lx - wbox / 2, ly - 1.05, lx + wbox / 2, ly + 1.05, fill="#ffffff", stroke=LINE, sw=0.8)
        svg.line(lx - wbox / 2, ly - 0.1, lx + wbox / 2, ly - 0.1, LINE, 0.5)
        svg.text(lx, ly, name, 7.5 if r.get("small") else 8.5, weight=700, ls=0.6, extra='dy="-3"')
        svg.text(lx, ly, f"{no}  ·  {D.poly_area(r['poly']):.0f} SF", 6.8, fill=MID, extra='dy="8.5"')
    for o in D.OUTDOOR:
        lx, ly = o["label"]
        svg.text(lx, ly, o["name"].upper(), 8 if len(o["name"]) < 15 else 7, weight=700, fill=LINE, ls=1.2)
    # door + window tags
    doors, wins = openings_schedule()
    for d in doors:
        svg.layer = "A-GATE-ALT" if d["name"] == "Carport sliding gate" else "A-DOOR-IDEN"
        off = (0, 1.6)
        if d.get("wall") in ("N-bar",):
            off = (0, -1.5)
        if d.get("wall") in ("S-bar",):
            off = (0, 1.6)
        if d.get("wall") == "E-gallery":
            off = (-1.8, 0)
        if d["name"] == "Entry gate":
            off = (0, -1.6)
        tag_circle(svg, d["x"] + off[0], d["y"] + off[1], d["tag"], 0.95, 7.5)
    svg.layer = "A-GLAZ-IDEN"
    for wn in wins:
        dx, dy = {"S-wing": (0, -1.7), "E-gallery": (1.9, 0), "N-bar": (0, 1.7), "W": (-2.3, 0),
                  "E-bar": (2.3, 0), "S-bar": (0, -1.7)}.get(wn["wall"], (0, 1.5))
        tag_hex(svg, wn["x"] + dx, wn["y"] + dy, wn["tag"], 7.5)
    # keynotes
    svg.layer = "A-ANNO-KEYN"
    cbx = (D.COBOGO["x0"] + D.COBOGO["x1"]) / 2
    keynote(svg, cbx, 30.15, 1, cbx + 2.0, 25.2)
    gx = (D.ENTRY_GATE["x0"] + D.ENTRY_GATE["x1"]) / 2
    keynote(svg, gx, 30.2, 2, gx, 25.2)
    keynote(svg, 15.0, 29.8, 3, 15.0, 25.2)
    keynote(svg, D.CEDAR_SCREEN["x"], 42.0, 4, D.CEDAR_SCREEN["x"] - 3.0, 42.0)
    em_ = D.ENTRY_MOSAIC
    keynote(svg, em_["x0"] + 5.0, 33.0, 5, em_["x0"] + 7.5, 38.0)
    keynote(svg, 35.0, 56.0, 6)
    keynote(svg, 36.4, 76.0, 7)
    keynote(svg, 43.0, 92.5, 8, 46.0, 94.5)
    keynote(svg, 18.4, 91.6, 9, 14.0, 94.5)
    keynote(svg, 19.75, 85.2, 10)
    keynote(svg, 44.0, 46.5, 11)
    keynote(svg, D.PRIMARY_BATH["shower"][2] - 0.9, 78.3, 12)
    if hb:
        keynote(svg, hb["tub"][0] + 0.7, hb["tub"][1] + 0.7, 19)
    if cp:
        keynote(svg, cp["x0"] + 1.4, (cp["y0"] + cp["y1"]) / 2, 13)
    if sl:
        svg.layer = "A-GATE-ALT"
        keynote(svg, sl["x1"] - 1.5, sl["y"], 17, sl["x1"] + 1.8, sl["y"] - 3.2)
        svg.layer = "A-ANNO-KEYN"
    if ri:
        mx0, my0, mx1, my1 = ri["motor_pad"]
        keynote(svg, (mx0 + mx1) / 2 - 0.4, my0, 18, mx0 - 0.2, 27.0)
    if hv:
        x0, y0, x1, y1 = hv["pad"]
        keynote(svg, (x0 + x1) / 2, y1, 14, (x0 + x1) / 2, y1 + 2.4)
    for k in sk:   # tag inside the skylight outline
        x0, y0, x1, y1 = k["rect"]
        keynote(svg, (x0 + x1) / 2, (y0 + y1) / 2, 15)
    if hv:
        x0, y0, x1, y1 = hv["dropped"][3]["rect"]
        keynote(svg, x0 + 0.3, y1 - 0.3, 16, x0 - 3.7, y1 + 1.2)
    # dimension chains (exterior faces)
    svg.layer = "A-ANNO-DIMS"
    def wall_edges(wid):
        w = [w for w in D.EXT_WALLS if w["id"] == wid][0]
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        pts = [ax if abs(ux) > 0.5 else ay, bx if abs(ux) > 0.5 else by]
        for o in w["openings"]:
            for t in (o["off"], o["off"] + o["w"]):
                pts.append(ax + ux * t if abs(ux) > 0.5 else ay + uy * t)
        return pts
    X0, X1 = D.BAR["x0"], D.BAR["x1"]
    cpx = [cp["x1"]] if cp else []
    s_ops = wall_edges("S-wing") + [D.LIMESTONE_WALL["x0"], D.ENTRY_GATE["x0"], D.ENTRY_GATE["x1"],
                                    D.CEDAR_SCREEN["x"]] + cpx
    chain(svg, s_ops, 30, True, -6.2)
    chain(svg, [X0, D.WING["x1"], D.CEDAR_SCREEN["x"]] + cpx, 30, True, -9.0)
    chain(svg, [X0, X1], 30, True, -11.8, size=9)
    chain(svg, wall_edges("N-bar"), 92.5, True, 3.4)
    chain(svg, [X0, 16, 18.4, 40.6, 43, X1], 92.5, True, 6.2)
    chain(svg, [X0, X1], 92.5, True, 9.4, size=9)
    chain(svg, wall_edges("W") + [60], 6, False, -6.0)
    chain(svg, [30, 60, 80, 92.5], 6, False, -8.8)
    chain(svg, [30, 92.5], 6, False, -11.6, size=9)
    chain(svg, wall_edges("E-bar") + [30, (cp["y1"] if cp else 60)], X1, False, 6.0)
    chain(svg, [27, 30, 60, 80, 83], X1, False, 8.8)
    # interior: wing rooms + courtyard clear
    chain(svg, [30.5, 41.5, 48.5, 60], D.PARTITIONS[0]["a"][0], False, -1.4, size=7)
    chain(svg, [D.COURTYARD["x0"], D.COURTYARD["x1"]], 48, True, 0.0, size=8)
    # section + elevation markers
    svg.layer = "A-ANNO-SYMB"
    for (yy, up) in ((16.4, True), (100.4, False)):
        svg.line(34, yy, 34, yy + (2.6 if up else -2.6), LINE, 2)
        svg.circle(34, yy + (-1.0 if up else 1.0), 1.1, fill="#ffffff", stroke=LINE, sw=1.1)
        svg.text(34, yy + (-1.0 if up else 1.0), "A", 8, weight=700, extra='dy="3"')
    elev_marker(svg, 22, 16.2, 1, "A-202", "n")
    elev_marker(svg, 22, 100.0, 2, "A-202", "s")
    elev_marker(svg, max(74.5, D.BAR["x1"] + 13.5), 72, 3, "A-203", "w")
    elev_marker(svg, -11.8, 70, 4, "A-203", "e")
    north_arrow(svg, svg.w - 44, 42, 20)
    scale_bar(svg, 30, svg.h - 18)
    svg.layer = None
    name = svg.save("30_floor_plan_cd.svg")
    json.dump(dict(doors=doors, windows=wins, keynotes=KEYNOTES), open(os.path.join(OUT, "schedules.json"), "w"),
              indent=1)
    return name


# ------------------------------------------------------------------ roof plan
def roof_plan_cd():
    svg = SVG(-6, 22, 66, 98, scale=8.4, pad=18)
    cd_defs(svg)
    svg.poly(D.FOOTPRINT, fill="none", stroke=MID, sw=0.7, extra='stroke-dasharray="5 3"')
    svg.poly(D.ROOF, fill="#f6f6f4", stroke=LINE, sw=1.8)
    inset = [(3.6, 27.6), (56.4, 27.6), (56.4, 35.4), (30.4, 35.4), (30.4, 56.6), (56.4, 56.6), (56.4, 82.4),
             (42.4, 82.4), (42.4, 91.9), (16.6, 91.9), (16.6, 82.4), (3.6, 82.4)]
    svg.poly(inset, fill="none", stroke=LINE, sw=0.6)
    svg.text(30.0, 70.0, "LOW-SLOPE TPO ROOF", 9, weight=700, ls=1.2)
    svg.text(30.0, 70.0, "1/4\" PER FT TO SCUPPERS", 7.5, fill=MID, extra='dy="11"')
    for (x0, y0, x1, y1) in ((14, 66, 14, 76), (44, 66, 44, 76), (16, 40, 16, 50), (44, 30.5, 44, 33.5)):
        svg.line(x0, y0, x1, y1, LINE, 1.0)
        svg.add(f'<path d="M {svg.X(x1) - 4:.1f} {svg.Y(y1) + 6:.1f} L {svg.X(x1):.1f} {svg.Y(y1):.1f} '
                f'L {svg.X(x1) + 4:.1f} {svg.Y(y1) + 6:.1f}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    for (x, y) in ((10, 83.0), (50, 83.0), (29, 92.5)):
        svg.rect(x - 0.6, y - 0.25, x + 0.6, y + 0.25, fill=LINE, stroke="none")
        svg.leader(x, y, x + 3, y + 3.2, "SCUPPER + DOWNSPOUT", size=7)
    svg.text(43.5, 46.5, "OPEN TO SKY", 8, weight=700, ls=1.2, fill=MID)
    svg.text(43.5, 46.5, "(PÁTIO)", 7.5, fill=MID, extra='dy="10"')
    svg.dim(3, 83, 57, 83, 9.5 + 2.5, size=8)
    svg.dim(3, 27, 3, 83, -4.0, horizontal=False, size=8)
    svg.dim(6, 30, 3, 30, -2.6, "3'-0\" OH", size=7)
    svg.dim(31, 56, 57, 56, -2.0, size=7)
    svg.dim(57, 36, 57, 56, 2.5, horizontal=False, size=7)
    north_arrow(svg, svg.w - 34, 34, 16)
    return svg.save("31_roof_plan_cd.svg")


# ------------------------------------------------------------------ CD elevations (no trees)
def datum(svg, x_left, x_right, marks):
    for z, lab in marks:
        svg.line(x_left, z, x_right, z, "#7b8085", 0.5, extra='stroke-dasharray="10 4"')
        for xx in (x_left,):
            X, Y = svg.X(xx), svg.Y(z)
            svg.add(f'<g transform="translate({X:.1f},{Y:.1f})"><circle r="6" fill="#ffffff" stroke="{LINE}" '
                    f'stroke-width="1"/><path d="M -6 0 A 6 6 0 0 1 0 -6 L 0 0 Z M 6 0 A 6 6 0 0 1 0 6 L 0 0 Z" '
                    f'fill="{LINE}"/></g>')
            svg.text(xx, z, lab, 7.5, anchor="end", extra='dx="-9" dy="-3"')


def elev_cd(name, view):
    import drawings as DR
    # reuse the vector elevations but with trees off, plus datums + keynote tags
    orig = DR.elev_tree
    DR.elev_tree = lambda *a, **k: None
    try:
        fn = {"s": DR.south_elevation, "n": DR.north_elevation, "e": DR.east_elevation, "w": DR.west_elevation}[view]
        path = fn(ztop=23)
    finally:
        DR.elev_tree = orig
    s = open(path).read()
    os.replace(path, os.path.join(OUT, name))
    # restore the presentation version too
    fn()
    return name


def main():
    print(floor_plan_cd())
    print(roof_plan_cd())
    for v, n in (("s", "32_elev_s_cd.svg"), ("n", "33_elev_n_cd.svg"), ("e", "34_elev_e_cd.svg"),
                 ("w", "35_elev_w_cd.svg")):
        print(elev_cd(n, v))


if __name__ == "__main__":
    main()
