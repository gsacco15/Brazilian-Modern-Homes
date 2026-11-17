"""Presentation sheets (SketchUp LayOut style): rendered orthographic plan / elevations /
landscape plan from Cycles, with crisp vector linework on top.

    python3 casa01/drawings2.py   ->  casa01/drawings/2*_*.svg  (+ plant schedule json)

Each SVG embeds its render by relative path (__IMG__/<file>), swapped at build time.
"""
import json
import math
import os

import design as D
from drawings import fmt_ft, wall_rects

HERE = os.path.dirname(os.path.abspath(__file__))
ORTHO = os.path.join(HERE, "renders", "ortho")
OUT = os.path.join(HERE, "drawings")
FONT = "Lato, 'Helvetica Neue', Arial, sans-serif"
INK = "#1b1d1f"
GOLD = "#b8955a"


class Sheet:
    def __init__(self, view, img):
        meta = json.load(open(os.path.join(ORTHO, "ortho_views.json")))[view]
        self.W, self.H = meta["res"]
        self.s = self.W / meta["width"]
        self.c = meta["center"]
        self.rot = meta["rot"]
        self.view = view
        self.items = [f'<image href="__IMG__/{img}" x="0" y="0" width="{self.W}" height="{self.H}"/>']
        self.pad = dict(l=0, t=0, r=0, b=0)

    # plan: x right, y up. elevations: horizontal axis per camera, z up.
    def P(self, x, y):
        cx, cy = self.c[0], self.c[1]
        return ((x - cx) * self.s + self.W / 2, (cy - y) * self.s + self.H / 2)

    def E(self, h, z):
        rz = self.rot[2]
        if rz == 0:
            u = h - self.c[0]
        elif rz == 180:
            u = self.c[0] - h
        elif rz == 90:
            u = h - self.c[1]
        else:
            u = self.c[1] - h
        return (u * self.s + self.W / 2, (self.c[2] - z) * self.s + self.H / 2)

    def add(self, s):
        self.items.append(s)

    def poly(self, pts, fill=INK, stroke="none", sw=1, extra=""):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, a, b, stroke=INK, sw=2, extra=""):
        self.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}" {extra}/>')

    def text(self, p, s, size=26, anchor="middle", fill=INK, weight=700, ls=1.5, extra=""):
        self.add(f'<text x="{p[0]:.1f}" y="{p[1]:.1f}" font-family="{FONT}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" letter-spacing="{ls}" fill="{fill}" {extra}>{s}</text>')

    def tag(self, p, title, sub=None, size=24):
        w = max(len(title) * size * 0.66, len(sub or "") * size * 0.5) + 26
        h = size * (2.35 if sub else 1.5)
        x, y = p
        self.add(f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" '
                 f'fill="rgba(255,255,255,0.86)" stroke="rgba(27,29,31,0.25)" stroke-width="1"/>')
        if sub:
            self.text((x, y - size * 0.12), title, size, ls=size * 0.06)
            self.text((x, y + size * 0.88), sub, size * 0.72, weight=400, fill="#4a4f53", ls=0.5)
        else:
            self.text((x, y + size * 0.36), title, size, ls=size * 0.06)

    def callout(self, a, b, label, size=24, anchor="start"):
        self.line(a, b, "rgba(255,255,255,0.85)", 6)   # halo keeps the leader readable over foliage
        self.line(a, b, "#2b2e31", 2)
        self.add(f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="5" fill="#2b2e31"/>')
        w = len(label) * size * 0.72 + 22  # bold caps + letter-spacing; text must never spill onto dark foliage
        x = b[0] if anchor == "start" else b[0] - w
        self.add(f'<rect x="{x:.1f}" y="{b[1] - size * 0.9:.1f}" width="{w:.1f}" height="{size * 1.35:.1f}" '
                 f'fill="rgba(255,255,255,0.9)"/>')
        self.text((x + 9, b[1] + size * 0.2), label, size, anchor="start", ls=size * 0.05)

    def save(self, name, extra_w=0, extra_h=0):
        os.makedirs(OUT, exist_ok=True)
        W, H = self.W + extra_w, self.H + extra_h
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
               f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.items) + "</svg>")
        open(os.path.join(OUT, name), "w").write(svg)
        return name


def north_arrow(sh, x, y, r=46):
    sh.add(f'<g transform="translate({x},{y})"><circle r="{r}" fill="rgba(255,255,255,0.88)" stroke="{INK}" '
           f'stroke-width="2"/><path d="M0 {-r * 0.8} L{r * 0.32} {r * 0.55} L0 {r * 0.28} L{-r * 0.32} {r * 0.55} Z" '
           f'fill="{INK}"/><text y="{-r - 10}" font-family="{FONT}" font-size="26" font-weight="900" '
           f'text-anchor="middle" fill="{INK}">N</text></g>')


def scale_bar(sh, x, y, marks=(0, 4, 8, 16), unit_px=None):
    s = unit_px or sh.s
    out = [f'<g transform="translate({x},{y})"><rect x="-10" y="-14" width="{marks[-1] * s + 40}" height="56" '
           f'fill="rgba(255,255,255,0.88)"/>']
    for i in range(len(marks) - 1):
        a, b = marks[i], marks[i + 1]
        out.append(f'<rect x="{a * s:.1f}" y="0" width="{(b - a) * s:.1f}" height="10" fill="{INK if i % 2 == 0 else "#fff"}" '
                   f'stroke="{INK}" stroke-width="1.5"/>')
    for m in marks:
        out.append(f'<text x="{m * s:.1f}" y="34" font-family="{FONT}" font-size="20" text-anchor="middle" '
                   f'fill="{INK}">{m}\'</text>')
    out.append("</g>")
    sh.add("".join(out))


# ------------------------------------------------------------------ rendered floor plan
def plan_rendered():
    sh = Sheet("plan_render", "plan_render.jpg")
    P = sh.P
    # poché for cut walls (exterior + partitions + limestone veneer)
    for w in D.EXT_WALLS:
        rects, spans, rect, _ = wall_rects(w, D.EXT_T)
        for (x0, y0, x1, y1) in rects:
            sh.poly([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)])
        for o in spans:
            if o["sill"] > 0 and o["sill"] < 4.5:
                x0, y0, x1, y1 = rect(o["off"], o["off"] + o["w"], 0, D.EXT_T)
                sh.poly([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)], fill="rgba(170,200,210,0.55)",
                        stroke=INK, sw=2)
    lw = D.LIMESTONE_WALL
    sh.poly([P(lw["x0"], lw["y_face"]), P(lw["x1"], lw["y_face"]), P(lw["x1"], lw["y_back"]), P(lw["x0"], lw["y_back"])],
            fill="#5a4c38")
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
                pts = [(ax + ux * s + nx * t, ay + uy * s + ny * t), (ax + ux * e + nx * t, ay + uy * e + ny * t),
                       (ax + ux * e - nx * t, ay + uy * e - ny * t), (ax + ux * s - nx * t, ay + uy * s - ny * t)]
                sh.poly([P(*q) for q in pts])
            if o:
                if o["kind"] != "closet":
                    sw_ = -1 if p["a"] == (39.0, 60.5) else 1
                    hx, hy = ax + ux * o["off"], ay + uy * o["off"]
                    lx, ly = hx + nx * o["w"] * sw_, hy + ny * o["w"] * sw_
                    sh.line(P(hx, hy), P(lx, ly), INK, 3)
                    r = o["w"] * sh.s
                    a0 = P(lx, ly)
                    a1 = P(hx + ux * o["w"], hy + uy * o["w"])
                    sweep = 1 if sw_ * 1 > 0 else 0
                    sh.add(f'<path d="M {a0[0]:.1f} {a0[1]:.1f} A {r:.1f} {r:.1f} 0 0 {sweep} {a1[0]:.1f} {a1[1]:.1f}" '
                           f'fill="none" stroke="{INK}" stroke-width="1.5" stroke-dasharray="6 5"/>')
                s = o["off"] + o["w"]
    # cobogó, gate, cedar screen, posts (cut at 5'-6")
    c = D.COBOGO
    for i in range(int(c["x1"] - c["x0"])):
        x = c["x0"] + i
        sh.poly([P(x + 0.04, c["y"]), P(x + 0.96, c["y"]), P(x + 0.96, c["y"] + c["t"]), P(x + 0.04, c["y"] + c["t"])],
                fill="#f2efe8", stroke=INK, sw=2)
    for (x, y) in D.POSTS:
        sh.poly([P(x - 0.17, y - 0.17), P(x + 0.17, y - 0.17), P(x + 0.17, y + 0.17), P(x - 0.17, y + 0.17)])
    # roof edge above (dashed)
    sh.add('<polygon points="' + " ".join(f"{P(x, y)[0]:.1f},{P(x, y)[1]:.1f}" for x, y in D.ROOF) +
           '" fill="none" stroke="#1b1d1f" stroke-width="2.5" stroke-dasharray="18 10" opacity="0.7"/>')
    # room tags
    for r in D.ROOMS:
        if r["name"] in ("Cl.",):
            continue
        xs = [q[0] for q in r["poly"]]
        ys = [q[1] for q in r["poly"]]
        area = D.poly_area(r["poly"])
        if r.get("vertical"):
            x, y = P(*r["label"])
            sh.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="34" font-weight="700" '
                   f'letter-spacing="2" text-anchor="middle" fill="{INK}" transform="rotate(-90 {x:.1f} {y:.1f})">'
                   f'GALLERY</text>')
            continue
        sub = None if r.get("small") else f"{fmt_ft(max(xs) - min(xs))} x {fmt_ft(max(ys) - min(ys))} · {area:.0f} sf"
        sh.tag(P(*r["label"]), r["name"].upper(), sub, size=30 if r.get("small") else 40)
    for o in D.OUTDOOR:
        sh.tag(P(*o["label"]), o["name"].upper(), None, size=36)
    sh.callout(P(16.0, 29.9), P(9.0, 25.0), "LUEDERS LIMESTONE WALL", 32, anchor="end")
    sh.callout(P(44.0, 30.15), P(44.0, 25.2), "COBOGÓ SCREEN", 32)
    sh.callout(P(54.0, 45.0), P(58.0, 45.0), "CEDAR SCREEN", 32)
    sh.callout(P(30.5, 30.0), P(30.5, 24.2), "CEDAR GATE", 32, anchor="end")
    sh.callout(P(36.5, 33.2), P(38.5, 22.6), "BLACK CALÇADA PORTUGUESA", 32)
    north_arrow(sh, sh.W - 110, 130, 62)
    scale_bar(sh, 60, sh.H - 80)
    return sh.save("20_plan_rendered.svg")


# ------------------------------------------------------------------ landscape plan
SPECIES = [
    # code, log names, common, botanical, size, water, notes
    ("LO", ["__trees__"], "Live oak / Monterrey oak", "Quercus virginiana / Q. polymorpha", "existing / 30 gal",
     "Low", "Heritage oak protected; root zone kept clear of new paving"),
    ("AG", ["Front agave", "Courtyard agave"], "Whale's tongue agave", "Agave ovatifolia", "15 gal", "Very low",
     "Sculptural accent, full sun"),
    ("SO", ["Front sotol"], "Texas sotol", "Dasylirion texanum", "5 gal", "Very low", "Fountain form"),
    ("MF", ["Front feather grass"], "Fine-textured grass", "Little bluestem (native)", "1 gal", "Low",
     "Feather-grass look; prefer natives over Nassella"),
    ("MU", ["Front muhly", "Courtyard muhly", "Rear muhly"], "Lindheimer muhly", "Muhlenbergia lindheimeri", "5 gal",
     "Low", "Silver-blue clumps, fall plumes"),
    ("PA", ["Courtyard palmetto", "Shower garden palmetto"], "Dwarf palmetto", "Sabal minor", "5 gal", "Low-med",
     "Native, cold-hardy tropical look"),
    ("FE", ["Courtyard ferns", "Shower garden ferns"], "River fern", "Thelypteris kunthii", "1 gal", "Medium",
     "Shade under the courtyard tree"),
    ("YA", ["Front shrubs", "Side shrubs"], "Dwarf yaupon holly", "Ilex vomitoria 'Nana'", "5 gal", "Low",
     "Evergreen screening along lot lines"),
    ("BG", ["Rear lawn", "Parkway lawn"], "Buffalo grass / Habiturf", "Bouteloua dactyloides blend", "plugs / seed",
     "Low", "Low-mow native lawn"),
    ("BO", ["Front boulders"], "Limestone boulders", "Local Hill Country stone", "2-4 ft", "–", "Set 1/3 buried"),
]


def landscape_plan():
    sh = Sheet("site_render", "site_render.jpg")
    P = sh.P
    log = json.load(open(os.path.join(ORTHO, "planting.json")))
    plants = log["plants"]
    # lot + setbacks
    lot = [(0, 0), (D.LOT_W, 0), (D.LOT_W, D.LOT_D), (0, D.LOT_D)]
    sh.add('<polygon points="' + " ".join(f"{P(*q)[0]:.1f},{P(*q)[1]:.1f}" for q in lot) +
           '" fill="none" stroke="#ffffff" stroke-width="4" stroke-dasharray="26 8 4 8"/>')
    sb = [(5, 25), (60, 25), (60, 115), (5, 115)]
    sh.add('<polygon points="' + " ".join(f"{P(*q)[0]:.1f},{P(*q)[1]:.1f}" for q in sb) +
           f'" fill="none" stroke="{GOLD}" stroke-width="2.5" stroke-dasharray="10 8"/>')
    rows = []
    for code, names, common, bot, size, water, note in SPECIES:
        if names == ["__trees__"]:
            pts = [(t["x"], t["y"]) for t in log["trees"]]
        else:
            pts = [p for n in names for p in plants.get(n, [])]
        if not pts:
            continue
        qty = len(pts) if code != "BG" else None
        rows.append((code, common, bot, size, water, note, qty))
        # tag a few representative plants with the species code
        step = max(1, len(pts) // (3 if code in ("MF", "BG") else 4))
        for (x, y) in pts[::step][:4]:
            if not (-12 < x < 77 and -14 < y < 129):
                continue
            X, Y = P(x, y)
            sh.add(f'<g><circle cx="{X:.1f}" cy="{Y:.1f}" r="26" fill="rgba(255,255,255,0.94)" stroke="{INK}" '
                   f'stroke-width="2"/><text x="{X:.1f}" y="{Y + 8:.1f}" font-family="{FONT}" font-size="22" '
                   f'font-weight="900" text-anchor="middle" fill="{INK}">{code}</text></g>')
    for (x, y, s_) in ((30.5, 13.0, "LIMESTONE STEPPING SLABS"), (59.3, 10.0, "RIBBON DRIVE"),
                       (44.0, 46.0, "PÁTIO"), (29.5, 88.0, "VERANDA"), (24.0, 60.0, "CASA 01")):
        sh.tag(P(x, y), s_, None, size=28)
    sh.callout(P(65.0, 100.0), P(64.0, 109.0), "6' CEDAR FENCE", 26, anchor="end")
    sh.callout(P(10.0, 14.0), P(-9.0, 19.0), "DG + NATIVE MEADOW", 26)
    north_arrow(sh, sh.W - 70, 90, 38)
    scale_bar(sh, 40, sh.H - 60, (0, 10, 20, 40))
    name = sh.save("21_landscape_plan.svg")
    json.dump(rows, open(os.path.join(OUT, "plant_schedule.json"), "w"), indent=1)
    return name


# ------------------------------------------------------------------ rendered elevations
def elevation(view, title, callouts):
    sh = Sheet(view, f"{view}.jpg")
    E = sh.E
    rz = sh.rot[2]
    margin = 560
    gy = E(0, 0)[1]
    below = max(0.0, gy + 84 - sh.H)   # room under the grade line for its label
    # cut the ground: white below grade, heavy grade line across the full sheet
    sh.add(f'<rect x="0" y="{gy:.1f}" width="{sh.W + margin}" height="{sh.H - gy + below + 2:.1f}" fill="#ffffff"/>')
    sh.add(f'<rect x="0" y="{gy:.1f}" width="{sh.W + margin}" height="26" fill="url(#earth)"/>')
    sh.line((0, gy), (sh.W + margin - 20, gy), INK, 7)
    x0 = sh.W + 40
    for z, lab in ((D.FASCIA_TOP, "T.O. ROOF +12'-3\""), (D.CEIL, "SOFFIT / CLG +11'-0\""), (D.FF, "F.F. +1'-0\""),
                   (0, "GRADE 0'-0\"")):
        y = E(0, z)[1]
        sh.add(f'<line x1="{sh.W - 260}" y1="{y:.1f}" x2="{x0 + 40}" y2="{y:.1f}" stroke="#2b2e31" stroke-width="2" '
               f'stroke-dasharray="14 8"/>')
        sh.add(f'<path d="M {x0 + 20:.1f} {y:.1f} l -15 -20 l 30 0 z" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>')
        sh.text((x0 + 56, y + (58 if z == 0 else -8)), lab, 32, anchor="start", ls=1)
    for (h, z, h2, z2, lab, anchor) in callouts:
        sh.callout(E(h, z), E(h2, z2), lab, 34, anchor)
    sh.add('<defs><pattern id="earth" width="16" height="16" patternUnits="userSpaceOnUse" '
           'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="16" stroke="#8a8a8a" stroke-width="2"/>'
           '</pattern></defs>')
    return sh.save(f"22_{view}.svg", extra_w=margin, extra_h=below)


def _opening(wall_id, name):
    """(center along the elevation's h axis, opening) for a named opening in an exterior wall."""
    w = next(w for w in D.EXT_WALLS if w["id"] == wall_id)
    o = next(o for o in w["openings"] if o["name"] == name)
    (ax, ay), (bx, by) = w["a"], w["b"]
    L = math.hypot(bx - ax, by - ay)
    t = (o["off"] + o["w"] / 2) / L
    return (ax + (bx - ax) * t, ay + (by - ay) * t), o


def elevations():
    # south: labels step down left to right so no leader crosses another label
    lw, eg, cb, cs = D.LIMESTONE_WALL, D.ENTRY_GATE, D.COBOGO, D.CARPORT_SLIDER
    south = [
        (lw["x0"] + 2.0, D.FASCIA_TOP - 0.6, lw["x0"] + 2.0, 26.0, "15\" DARK BRONZE FASCIA", "start"),
        (14.0, 6.0, 14.0, 23.5, "LUEDERS LIMESTONE ASHLAR", "start"),
        ((eg["x0"] + eg["x1"]) / 2, 6.0, (eg["x0"] + eg["x1"]) / 2, 21.0, "CEDAR SLAT PIVOT GATE", "start"),
        (cb["x0"] + 9.0, 6.5, cb["x0"] + 9.0, 18.5, "12x12 CONCRETE COBOGÓ", "start")]
    if cs.get("installed", True):
        south.append((cs["x0"] + 5.5, 6.0, cs["x0"] + 5.5, 16.0, "SLIDING CARPORT GATE (OPTION)", "start"))
    (cx, _), _o = _opening("N-bar", "Primary bath clerestory")
    (sx, _), so = _opening("N-bar", "Great room to veranda")
    (_, b3), _o = _opening("W", "Bed 3 window")
    (_, b2), _o = _opening("W", "Bed 2 window")
    out = [elevation("elev_s", "SOUTH ELEVATION (STREET)", south),
        elevation("elev_n", "NORTH ELEVATION (VERANDA)", [
            (sx, 5, sx, 19.0, f"{so['w']:.0f}' SLIDING GLASS WALL", "end"),
            (19.8, 3, 14, 18.5, "LIMESTONE GRILL COUNTER", "start"),
            (cx, 7.8, cx, 16.5, "BATH CLERESTORY", "start")]),
        elevation("elev_e", "EAST ELEVATION", [
            (45, 6, 45, 16.5, "CEDAR SLAT SCREEN", "start"),
            (78, 6.5, 80, 16.5, "SHOWER GARDEN WINDOW", "start")]),
        elevation("elev_w", "WEST ELEVATION", [
            (b3, 6, b3, 16.5, "BEDROOM 3", "end"), (b2, 6, b2, 16.5, "BEDROOM 2", "end"),
            (29.8, 9, 29.8, 19, "LIMESTONE FIN", "end")])]
    return out


def main():
    print(plan_rendered())
    print(landscape_plan())
    for e in elevations():
        print(e)


if __name__ == "__main__":
    main()
