"""Elevations and sections for Casa 02 and the Casita, drawn from the same model as the plans.

    python3 phase2/plans/elevations.py           (writes out/elev_*.svg; the sheets are added by plans.py)

Each drawing is a list of primitives in feet (x across the drawing, z up from grade), so the same geometry goes
to the PDF sheets (SVG) and to the AutoCAD file (export_dxf.py). Heights are the model's: finished floor 1'-0",
upper floor 11'-6", top of wall 21'-0", roof edge 22'-3" (Casita: wall 11'-0", roof edge 12'-3").
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
sys.path.insert(0, P2)
from model import homes as H  # noqa: E402

FF, GF_TOP, UP_FF, UP_TOP = 1.0, 10.5, 11.5, 21.0
ROOF, ONE = (21.0, 22.25), (11.0, 12.25)
BAND = UP_FF - 1.25
DOOR_HEAD, WIN_HEAD = 8.0, 8.5
SILL = {"high": 5.5, "egress": 2.25, "fluted below 5'": 2.25, "egress, fluted below 5'": 2.25, "sill 3'-6\"": 3.5,
        "to the pátio, cedar-screened": 1.0, "behind the cobogó": 1.0}
C = dict(ink="#23262a", mid="#6b6f73", light="#a7aaad", stucco="#f5f2ec", stone="#e2d8c6", joint="#a99c84",
         bronze="#2b2926", glass="#dfe6e8", oak="#c9a77c", cedar="#c4885a", cobogo="#fbfaf7", ground="#8a8478",
         cut="#23262a", sky="#e9eef0")


class Drawing:
    """Primitives in feet. kinds: poly, line, circle, text. Each carries a CAD layer."""

    def __init__(self, name, title):
        self.name, self.title = name, title
        self.items = []
        self.x0 = self.z0 = 1e9
        self.x1 = self.z1 = -1e9

    def _ext(self, xs, zs):
        self.x0, self.x1 = min(self.x0, *xs), max(self.x1, *xs)
        self.z0, self.z1 = min(self.z0, *zs), max(self.z1, *zs)

    def poly(self, pts, fill="none", stroke=None, sw=0.6, layer="A-ELEV", dash=None):
        self.items.append(dict(k="poly", pts=pts, fill=fill, stroke=stroke or C["ink"], sw=sw, layer=layer, dash=dash))
        self._ext([p[0] for p in pts], [p[1] for p in pts])

    def rect(self, x0, z0, x1, z1, **kw):
        self.poly([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], **kw)

    def line(self, x0, z0, x1, z1, stroke=None, sw=0.5, layer="A-ELEV", dash=None):
        self.items.append(dict(k="line", a=(x0, z0), b=(x1, z1), stroke=stroke or C["ink"], sw=sw, layer=layer,
                               dash=dash))
        self._ext([x0, x1], [z0, z1])

    def circle(self, x, z, r, fill="none", stroke=None, sw=0.4, layer="A-ELEV-PATT"):
        self.items.append(dict(k="circle", c=(x, z), r=r, fill=fill, stroke=stroke or C["mid"], sw=sw, layer=layer))

    def text(self, x, z, s, size=7.0, anchor="middle", fill=None, weight=400, layer="A-ANNO-TEXT"):
        self.items.append(dict(k="text", p=(x, z), s=s, size=size, anchor=anchor, fill=fill or C["ink"], weight=weight,
                               layer=layer))
        w = len(s) * size * 0.047                      # rough text width in feet at the sheet scale
        a = {"start": (x, x + w), "end": (x - w, x), "middle": (x - w / 2, x + w / 2)}[anchor]
        self._ext(list(a), [z])


# ---------------------------------------------------------------- materials as patterns
def ashlar(d, x0, z0, x1, z1, seed=1, holes=()):
    """Lueders sawn-face ashlar, 3 course heights, with random head joints; holes (x0, z0, x1, z1) left open."""
    d.rect(x0, z0, x1, z1, fill=C["stone"], stroke=C["ink"], sw=0.6, layer="A-ELEV")
    rng = random.Random(seed)
    pattern = [0.667, 0.333, 1.0, 0.333, 0.667, 0.667, 1.0, 0.333]
    z, i = z0, 0

    def inside(x, zz):
        return any(h[0] - 0.02 < x < h[2] + 0.02 and h[1] - 0.02 < zz < h[3] + 0.02 for h in holes)
    while z < z1 - 0.05:
        h = min(pattern[i % len(pattern)] if i else 0.667, z1 - z)
        zt = z + h
        if zt < z1 - 0.02:
            segs, xs = [], x0
            for hx0, hz0, hx1, hz1 in sorted(holes):
                if hz0 < zt < hz1:
                    segs.append((xs, hx0))
                    xs = hx1
            segs.append((xs, x1))
            for a, b in segs:
                if b - a > 0.05:
                    d.line(a, zt, b, zt, stroke=C["joint"], sw=0.35, layer="A-ELEV-PATT")
        x = x0 + rng.uniform(0.5, 2.5)
        while x < x1 - 0.3:
            if not inside(x, (z + zt) / 2):
                d.line(x, z, x, zt, stroke=C["joint"], sw=0.35, layer="A-ELEV-PATT")
            x += rng.uniform(1.4, 3.6) if h < 0.9 else rng.uniform(1.8, 4.2)
        z, i = zt, i + 1
    for hx0, hz0, hx1, hz1 in holes:                       # openings drawn on top by the caller
        pass


def cobogo(d, x0, x1, z0, z1, gaps=()):
    """Cobogó in elevation: one 12 in block per foot, a large circle and a small one at each block corner."""
    d.rect(x0, z0, x1, z1, fill=C["cobogo"], stroke=C["ink"], sw=0.6)
    nx, nz = int(round(x1 - x0)), int(round(z1 - z0))
    for i in range(nx):
        for k in range(nz):
            cx, cz = x0 + i + 0.5, z0 + k + 0.5
            if any(g[0] < cx < g[2] and g[1] < cz < g[3] for g in gaps):
                continue
            d.circle(cx, cz, 0.36, fill="#e8e6e0")
            d.circle(x0 + i, z0 + k, 0.12, fill="#e8e6e0")
    for g in gaps:                                         # open bay in front of the door
        d.rect(g[0], g[1], g[2], g[3], fill="#ffffff", stroke=C["ink"], sw=0.5)


def slats(d, x0, x1, z0, z1, pitch=0.29):
    d.rect(x0, z0, x1, z1, fill=C["cedar"], stroke=C["ink"], sw=0.5)
    x = x0 + pitch
    while x < x1 - 0.05:
        d.line(x, z0 + 0.05, x, z1 - 0.05, stroke="#8d5c38", sw=0.35, layer="A-ELEV-PATT")
        x += pitch


def window(d, x0, x1, z0, z1, kind="window"):
    d.rect(x0, z0, x1, z1, fill=C["glass"], stroke=C["bronze"], sw=0.9, layer="A-ELEV-GLAZ")
    n = max(1, round((x1 - x0) / (4.0 if kind == "slider" else 3.2)))
    for k in range(1, n):
        x = x0 + (x1 - x0) * k / n
        d.line(x, z0, x, z1, stroke=C["bronze"], sw=0.7, layer="A-ELEV-GLAZ")


def door(d, x0, x1, z0, z1):
    d.rect(x0, z0, x1, z1, fill=C["oak"], stroke=C["bronze"], sw=0.8, layer="A-ELEV")


def opening_box(o, wall_a, wall_u, z0, reverse=None):
    """x range and z range of an opening along a wall. reverse(x) maps plan x/y to drawing x."""
    s0, s1 = o["off"], o["off"] + o["w"]
    p0 = (wall_a[0] + wall_u[0] * s0, wall_a[1] + wall_u[1] * s0)
    p1 = (wall_a[0] + wall_u[0] * s1, wall_a[1] + wall_u[1] * s1)
    if o["kind"] in ("door", "slider", "bypass"):
        sill, head = 0.0, DOOR_HEAD
    else:
        sill, head = SILL.get(o.get("note", ""), 2.5), WIN_HEAD
    a, b = reverse(p0), reverse(p1)
    return min(a, b), max(a, b), z0 + sill, z0 + head


def wall_openings(plan, test, reverse, z0):
    """Openings of the exterior walls that lie on one face (test(a, b) is True), mapped to the drawing."""
    out = []
    for w in plan["walls"]:
        if not w["ext"] or not test(w["a"], w["b"]):
            continue
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        u = ((bx - ax) / L, (by - ay) / L)
        for o in w["openings"]:
            out.append((o, opening_box(o, (ax, ay), u, z0, reverse)))
    return out


def grade(d, x0, x1):
    d.line(x0 - 3, 0, x1 + 3, 0, stroke=C["ink"], sw=1.4, layer="A-ELEV-OTLN")
    x = x0 - 3
    while x < x1 + 3:
        d.line(x, 0, x - 0.6, -0.6, stroke=C["ground"], sw=0.3, layer="A-ELEV-OTLN")
        x += 0.8


def levels(d, x, marks):
    for z, label in marks:
        d.line(x, z, x + 2.2, z, stroke=C["mid"], sw=0.4, layer="A-ANNO-DIMS", dash="3 2")
        d.poly([(x + 2.2, z), (x + 2.6, z + 0.4), (x + 1.8, z + 0.4)], fill=C["ink"], stroke=C["ink"], sw=0.3,
               layer="A-ANNO-DIMS")
        d.text(x + 2.9, z, label, 6.2, anchor="start", layer="A-ANNO-DIMS")


def leader(d, x, z, tx, tz, label, anchor="start"):
    d.line(x, z, tx, tz, stroke=C["mid"], sw=0.45, layer="A-ANNO-TEXT")
    d.circle(x, z, 0.12, fill=C["ink"], stroke=C["ink"], layer="A-ANNO-TEXT")
    d.text(tx + (0.3 if anchor == "start" else -0.3), tz, label, 6.0, anchor=anchor)


def fx(d):
    """Common level marks of Casa 02."""
    return [(0.0, "GRADE 0'-0\""), (FF, "GROUND FLOOR 1'-0\""), (UP_FF, "UPPER FLOOR 11'-6\""),
            (ROOF[1], "ROOF EDGE 22'-3\"")]


# ---------------------------------------------------------------- Casa 02
def casa02_front(gf, name, title):
    """Front elevation (the y = 0 face, seen from the street): drawing x = plan x."""
    d = Drawing(name, title)
    W = 20.0
    grade(d, 0, W)
    rev = lambda p: p[0]
    face = lambda a, b: abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6
    side = gf is H.CASA02_GF_SIDE
    # upper floor: band, wall, openings
    d.rect(0, BAND, W, UP_FF, fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.rect(0, UP_FF, W, ROOF[0], fill=C["stucco"], stroke=C["ink"], sw=0.7)
    for o, (x0, x1, z0, z1) in wall_openings(H.CASA02_UPPER, face, rev, UP_FF):
        window(d, x0, x1, z0, z1, o["kind"])
    # ground floor
    ext_front = [w for w in gf["walls"] if w["ext"] and face(w["a"], w["b"])]
    if side:                                                    # the side-drive street wall in stone
        ashlar(d, 0, 0, W, BAND, seed=3)
    else:
        for w in ext_front:
            xa, xb = sorted((w["a"][0], w["b"][0]))
            d.rect(xa, FF, xb, BAND, fill=C["stucco"], stroke=C["ink"], sw=0.7)
        for run in H.stone_runs(gf):
            if abs(run["u"][1]) < 1e-6 and abs(run["a"][1]) < 1e-6:
                xa, xb = sorted((run["a"][0], run["a"][0] + run["u"][0] * run["L"]))
                holes = [opening_box(o, run["a"], run["u"], FF, rev) for _h0, _h1, o in run["holes"]]
                ashlar(d, xa, 0, xb, BAND, seed=5, holes=[(h[0], h[2], h[1], h[3]) for h in holes])
        for o, (x0, x1, z0, z1) in wall_openings(gf, face, rev, FF):
            (door if o["kind"] == "door" else window)(d, x0, x1, z0, z1) if o["kind"] == "door" else \
                window(d, x0, x1, z0, z1, o["kind"])
        bay = [r for r in gf["rooms"] if r.get("outdoor")]
        if bay:                                                 # carport: recess, cedar ceiling, gate, stone pier
            x0, _y0, x1, _y1 = bay[0]["rect"]
            d.rect(x0, 0.15, x1, BAND, fill="#5d5750", stroke=C["ink"], sw=0.6)
            d.rect(x0, BAND - 0.35, x1, BAND, fill=C["cedar"], stroke=C["ink"], sw=0.4)
            (g0x, _), (g1x, _) = gf["gate"]
            slats(d, min(g0x, g1x), max(g0x, g1x), 0.2, 8.4)
            for p in gf.get("stone", {}).get("piers", []):
                if p[1] < 0.01:
                    ashlar(d, p[0], 0, p[2], BAND, seed=7)
        d.rect(0, 0, W, FF, fill="#d9d4ca", stroke=C["ink"], sw=0.4) if not bay else None
    # cobogó lantern
    lan = gf.get("lantern")
    if lan:
        z0 = BAND if lan.get("upper_only") else FF
        gaps = []
        if lan.get("opening"):
            gaps = [(lan["opening"][0], FF, lan["opening"][1], FF + 8.0)]
            for o, (x0, x1, za, zb) in wall_openings(gf, face, rev, FF):
                if o["kind"] == "door":
                    door(d, x0, x1, za, zb)
        cobogo(d, lan["x"][0], lan["x"][1], z0, ROOF[0], gaps)
        if gaps:
            for o, (x0, x1, za, zb) in wall_openings(gf, face, rev, FF):
                if o["kind"] == "door":
                    door(d, x0, x1, za, zb)
    # roof edge and rooftop
    xr = W if gf is H.CASA02_GF_CARPORT else W + 1
    d.rect(-1, ROOF[0], xr, ROOF[1], fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.line(-1, ROOF[0] - 0.06, 0, ROOF[0] - 0.06, stroke=C["cedar"], sw=1.2)
    for sk in H.CASA02_UPPER.get("skylights", []):
        x0, _y0, x1, _y1 = sk["rect"]
        d.rect(x0 - 0.3, ROOF[1], x1 + 0.3, ROOF[1] + 0.56, fill="#e6e3dc", stroke=C["mid"], sw=0.4)
    levels(d, xr + 1.5, fx(d))
    # notes
    if side:
        leader(d, 3.0, 4.5, -6.0, 6.0, "LUEDERS LIMESTONE ASHLAR", "end")
    elif gf.get("gate"):
        leader(d, 0.75, 4.0, -6.0, 3.0, "LUEDERS LIMESTONE PIER", "end")
        leader(d, 6.0, 5.0, -6.0, 6.5, "CEDAR SLAT GATE", "end")
    else:
        leader(d, 1.0, 1.8, -6.0, 3.0, "LUEDERS LIMESTONE ASHLAR", "end")
    leader(d, 2.0, 18.5, -6.0, 18.5, "WARM-WHITE STUCCO", "end")
    leader(d, 5.0, BAND + 0.6, -6.0, 12.6, "DARK BRONZE FLOOR BAND", "end")
    leader(d, 17.5, 16.0, -6.0, 15.4, "COBOGÓ SCREEN", "end")
    leader(d, 4.0, ROOF[0] + 0.6, -6.0, 21.6, "15\" BRONZE FASCIA", "end")
    return d


def casa02_back(gf, name, title):
    """Back elevation (the y = 39 face, seen from the pátio): drawing x = 20 - plan x."""
    d = Drawing(name, title)
    W, D = 20.0, 39.0
    grade(d, 0, W)
    rev = lambda p: W - p[0]
    face = lambda a, b: abs(a[1] - D) < 1e-6 and abs(b[1] - D) < 1e-6
    d.rect(0, FF, W, BAND, fill=C["stucco"], stroke=C["ink"], sw=0.7)
    d.rect(0, 0, W, FF, fill="#d9d4ca", stroke=C["ink"], sw=0.4)
    d.rect(0, BAND, W, UP_FF, fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.rect(0, UP_FF, W, ROOF[0], fill=C["stucco"], stroke=C["ink"], sw=0.7)
    for o, (x0, x1, z0, z1) in wall_openings(gf, face, rev, FF):
        window(d, x0, x1, z0, z1, o["kind"])
    for o, (x0, x1, z0, z1) in wall_openings(H.CASA02_UPPER, face, rev, UP_FF):
        window(d, x0, x1, z0, z1, o["kind"])
    sh = gf.get("sunshade")
    if sh:
        x0, _y0, x1, _y1 = sh["rect"]
        a, b = sorted((W - x0, W - x1))
        d.rect(a, sh["z"], b, sh["z"] + 0.45, fill=C["cedar"], stroke=C["ink"], sw=0.5)
        leader(d, b - 1.0, sh["z"] + 0.2, W + 2.0, 8.0, "CEDAR SLAT SUNSHADE")
    xl = 0.0 if gf is H.CASA02_GF_CARPORT else -1.0
    d.rect(xl, ROOF[0], W + 1, ROOF[1], fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    for sk in H.CASA02_UPPER.get("skylights", []):
        x0, _y0, x1, _y1 = sk["rect"]
        d.rect(W - x1 - 0.3, ROOF[1], W - x0 + 0.3, ROOF[1] + 0.56, fill="#e6e3dc", stroke=C["mid"], sw=0.4)
    levels(d, W + 2.5, fx(d))
    leader(d, 5.0, 5.0, W + 2.0, 4.0, "16 FT SLIDER TO THE PÁTIO")
    leader(d, 5.0, UP_FF + 5.0, W + 2.0, 15.0, "PRIMARY BEDROOM WINDOW")
    return d


def casa02_side(gf, name, title):
    """Outer side (the x = 0 face, seen from the side yard or the drive): drawing x = 39 - plan y."""
    d = Drawing(name, title)
    D = 39.0
    grade(d, 0, D)
    rev = lambda p: D - p[1]
    face = lambda a, b: abs(a[0]) < 1e-6 and abs(b[0]) < 1e-6
    ext_side = [w for w in gf["walls"] if w["ext"] and face(w["a"], w["b"])]
    for w in ext_side:
        za, zb = sorted((D - w["a"][1], D - w["b"][1]))
        d.rect(za, FF, zb, BAND, fill=C["stucco"], stroke=C["ink"], sw=0.7)
        d.rect(za, 0, zb, FF, fill="#d9d4ca", stroke=C["ink"], sw=0.4)
    for o, (x0, x1, z0, z1) in wall_openings(gf, face, rev, FF):
        (door(d, x0, x1, z0, z1) if o["kind"] == "door" else window(d, x0, x1, z0, z1, o["kind"]))
    bay = [r for r in gf["rooms"] if r.get("outdoor")]
    if bay:
        _x0, y0, _x1, y1 = bay[0]["rect"]
        d.rect(D - y1, 0.15, D - y0, BAND, fill="#5d5750", stroke=C["ink"], sw=0.6)
        d.rect(D - y1, BAND - 0.35, D - y0, BAND, fill=C["cedar"], stroke=C["ink"], sw=0.4)
        g = gf.get("gate")
        if g and abs(g[0][0] - g[1][0]) < 1e-6:                 # side gate on this face
            slats(d, D - g[1][1], D - g[0][1], 0.2, 8.4)
    for p in gf.get("stone", {}).get("piers", []):
        if p[0] < 0.01:
            ashlar(d, D - p[3], 0, D - p[1], BAND, seed=9)
    for run in H.stone_runs(gf):
        if abs(run["u"][0]) < 1e-6 and abs(run["a"][0]) < 1e-6:
            ya, yb = run["a"][1], run["a"][1] + run["u"][1] * run["L"]
            holes = [opening_box(o, run["a"], run["u"], FF, rev) for _h0, _h1, o in run["holes"]]
            ashlar(d, D - max(ya, yb), 0, D - min(ya, yb), BAND, seed=11, holes=[(h[0], h[2], h[1], h[3]) for h in holes])
            for o, (x0, x1, z0, z1) in wall_openings(gf, face, rev, FF):
                window(d, x0, x1, z0, z1, o["kind"])
    for cx, cy in gf.get("columns", []):
        d.rect(D - cy - 0.17, 0.15, D - cy + 0.17, BAND, fill=C["bronze"], stroke=C["bronze"], sw=0.4)
    d.rect(0, BAND, D, UP_FF, fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.rect(0, UP_FF, D, ROOF[0], fill=C["stucco"], stroke=C["ink"], sw=0.7)
    for o, (x0, x1, z0, z1) in wall_openings(H.CASA02_UPPER, face, rev, UP_FF):
        window(d, x0, x1, z0, z1, o["kind"])
    lan = gf.get("lantern")
    if lan:                                                     # the cobogó in profile at the front
        z0 = BAND if lan.get("upper_only") else FF
        d.rect(D - lan["y"][1], z0, D - lan["y"][0], ROOF[0], fill=C["cobogo"], stroke=C["ink"], sw=0.6)
    sh = gf.get("sunshade")
    if sh:                                                      # sunshade in profile at the back
        d.rect(D - sh["rect"][3], sh["z"], D - sh["rect"][1], sh["z"] + 0.45, fill=C["cedar"], stroke=C["ink"], sw=0.5)
    d.rect(-1, ROOF[0], D + 1, ROOF[1], fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    levels(d, D + 2.5, fx(d))
    d.text(D, -2.2, "FRONT", 6.5, fill=C["mid"])
    d.text(0, -2.2, "BACK", 6.5, fill=C["mid"])
    return d


def casa02_section_long(gf, name, title, cut_x=18.0):
    """Section A: along the house through the stair (cut at x = 18, looking west). Drawing x = plan y."""
    d = Drawing(name, title)
    D = 39.0
    grade(d, 0, D)
    cut = dict(fill=C["cut"], stroke=C["cut"], sw=0.4, layer="A-SECT")
    d.rect(0, 0, D, FF, **cut)                                   # ground floor slab
    for y0, y1 in ((0.0, 0.5), (D - 0.5, D)):                    # front and back walls, both floors
        d.rect(y0, FF, y1, BAND, **cut)
        d.rect(y0, UP_FF, y1, ROOF[0], **cut)
    # openings cut in those walls at x = 18
    for w in gf["walls"] + H.CASA02_UPPER["walls"]:
        pass
    for zz0, zz1, y0, y1 in ((FF + 5.5, FF + 8.5, 0.0, 0.5), (UP_FF + 1.0, UP_FF + 8.5, 0.0, 0.5),
                             (FF, FF + 8.0, D - 0.5, D), (UP_FF + 5.5, UP_FF + 8.5, D - 0.5, D)):
        d.rect(y0, zz0, y1, zz1, fill=C["glass"], stroke=C["bronze"], sw=0.6, layer="A-ELEV-GLAZ")
    void = H.CASA02_UPPER["void"]
    for y0, y1 in ((0.0, void[1]), (void[3], D)):                # upper floor slab with the stair opening
        d.rect(y0, BAND, y1, UP_FF, **cut)
    # roof with the skylights on this line
    holes = sorted((sk["rect"][1], sk["rect"][3]) for sk in H.CASA02_UPPER.get("skylights", [])
                   if sk["rect"][0] < cut_x < sk["rect"][2])
    y = -1.0
    for h0, h1 in holes + [(D + 1, D + 1)]:
        if h0 > y:
            d.rect(y, ROOF[0], h0, ROOF[1], **cut)
        if h1 <= D:
            d.rect(h0 - 0.3, ROOF[1], h0, ROOF[1] + 0.5, **cut)
            d.rect(h1, ROOF[1], h1 + 0.3, ROOF[1] + 0.5, **cut)
            d.rect(h0 - 0.3, ROOF[1] + 0.5, h1 + 0.3, ROOF[1] + 0.56, fill=C["glass"], stroke=C["bronze"], sw=0.6)
            # daylight down the opening
            for k in range(3):
                yy = h0 + (h1 - h0) * (k + 1) / 4
                d.line(yy, ROOF[0], yy - 2.5, ROOF[0] - 9.0 if (void[1] < yy < void[3]) else UP_FF + 0.5,
                       stroke="#e0b25a", sw=0.6, layer="A-ANNO-TEXT", dash="4 3")
        y = h1
    # partitions cut at x = 18
    for pl, z0, z1 in ((gf, FF, BAND), (H.CASA02_UPPER, UP_FF, ROOF[0])):
        for w in pl["walls"]:
            if w["ext"]:
                continue
            (ax, ay), (bx, by) = w["a"], w["b"]
            if abs(ay - by) < 1e-6 and min(ax, bx) - 0.01 <= cut_x <= max(ax, bx) + 0.01:
                d.rect(ay - w["t"] / 2, z0, ay + w["t"] / 2, z1, **cut)
    # the stair: open oak treads from the kitchen (y 19.5) up to the landing (y 6)
    st = gf["stair"]
    x0, y0, x1, y1 = st["rect"]
    n = st.get("risers", 17) - 1
    rise, run = (UP_FF - FF) / st.get("risers", 17), (y1 - y0) / n
    pts = []
    for k in range(n + 1):
        yy = y1 - k * run
        pts += [(yy, FF + k * rise), (yy, FF + (k + 1) * rise)]
    for k in range(n):
        yy = y1 - (k + 1) * run
        z = FF + (k + 1) * rise
        d.rect(yy - 0.05, z - 0.15, yy + run, z, fill=C["oak"], stroke=C["ink"], sw=0.4)
    d.line(y1, FF, y0, UP_FF, stroke=C["ink"], sw=0.8)            # stringer
    # the cedar slats beyond, on the hall side
    yy = 9.5
    while yy < 19.5:
        d.line(yy, FF, yy, BAND, stroke=C["cedar"], sw=0.5, layer="A-ELEV-PATT")
        yy += 0.29
    # cobogó at the front, sunshade at the back
    lan = gf.get("lantern")
    if lan:
        d.rect(lan["y"][0], BAND if lan.get("upper_only") else FF, lan["y"][1], ROOF[0], fill=C["cobogo"],
               stroke=C["ink"], sw=0.6)
    sh = gf.get("sunshade")
    if sh:
        d.rect(sh["rect"][1], sh["z"], sh["rect"][3], sh["z"] + 0.45, fill=C["cedar"], stroke=C["ink"], sw=0.5)
    for (y, z, label) in ((2.8, FF + 2.5, "WC"), (7.5, FF + 2.5, "MECH"), (24.0, FF + 4.5, "KITCHEN"),
                          (32.5, FF + 4.5, "LIVING"), (2.8, UP_FF + 2.5, "LANDING"), (21.5, UP_FF + 2.5, "LAUNDRY"),
                          (27.0, UP_FF + 2.5, "CLOSET"), (34.5, UP_FF + 2.5, "PRIMARY BATH"),
                          (13.0, UP_FF + 6.5, "STAIR")):
        d.text(y, z, label, 6.2, fill=C["mid"])
    leader(d, 12.0, ROOF[1] + 0.3, 12.0, ROOF[1] + 3.0, "SKYLIGHT OVER THE STAIR")
    levels(d, D + 2.5, fx(d) + [(BAND, "CARPORT CEILING 10'-3\"")])
    d.text(0, -2.2, "FRONT", 6.5, fill=C["mid"])
    d.text(D, -2.2, "BACK", 6.5, fill=C["mid"])
    return d


# ---------------------------------------------------------------- Casita
def casita_front(name, title):
    d = Drawing(name, title)
    cs = H.CASITA
    W = cs["W"]
    grade(d, 0, W + 8)
    rev = lambda p: p[0]
    face = lambda a, b: abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6
    d.rect(0, FF, W, ONE[0], fill=C["stucco"], stroke=C["ink"], sw=0.7)
    d.rect(0, 0, W, FF, fill="#d9d4ca", stroke=C["ink"], sw=0.4)
    for o, (x0, x1, z0, z1) in wall_openings(cs, face, rev, FF):
        (door(d, x0, x1, z0, z1) if o["kind"] == "door" else window(d, x0, x1, z0, z1, o["kind"]))
    pr = cs["porch"]
    d.rect(W, 0, pr["roof"][2], ONE[0], fill="#f0ece4", stroke="none")
    for px, _py in pr["posts"][:1]:
        d.rect(px - 0.17, 0, px + 0.17, ONE[0], fill=C["bronze"], stroke=C["bronze"], sw=0.4)
    d.rect(-1, ONE[0], pr["roof"][2], ONE[1], fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.line(W + 0.2, ONE[0] - 0.06, pr["roof"][2], ONE[0] - 0.06, stroke=C["cedar"], sw=1.4)
    for sk in cs.get("skylights", []):
        x0, _y0, x1, _y1 = sk["rect"]
        d.rect(x0 - 0.3, ONE[1], x1 + 0.3, ONE[1] + 0.56, fill="#e6e3dc", stroke=C["mid"], sw=0.4)
    d.rect(13.0, 0, 17.0, FF - 0.02, fill="#3a3936", stroke=C["ink"], sw=0.4)       # calçada stoop
    levels(d, pr["roof"][2] + 1.5, [(0.0, "GRADE 0'-0\""), (FF, "FLOOR 1'-0\""), (ONE[1], "ROOF EDGE 12'-3\"")])
    leader(d, 24.0, 6.0, 31.5, 4.0, "COVERED PORCH, CEDAR CEILING")
    leader(d, 15.0, 0.4, 15.0, -2.6, "CALÇADA STOOP")
    leader(d, 2.0, 7.0, -4.0, 8.5, "WARM-WHITE STUCCO", "end")
    return d


def casita_side(name, title):
    """The porch side (x = W face), seen from the pátio: drawing x = plan y."""
    d = Drawing(name, title)
    cs = H.CASITA
    W, D = cs["W"], cs["D"]
    grade(d, 0, D)
    rev = lambda p: p[1]
    face = lambda a, b: abs(a[0] - W) < 1e-6 and abs(b[0] - W) < 1e-6
    d.rect(0, FF, D, ONE[0], fill=C["stucco"], stroke=C["ink"], sw=0.7)
    d.rect(0, 0, D, FF, fill="#d9d4ca", stroke=C["ink"], sw=0.4)
    for o, (x0, x1, z0, z1) in wall_openings(cs, face, rev, FF):
        window(d, x0, x1, z0, z1, o["kind"])
    pr = cs["porch"]
    for _px, py in pr["posts"]:
        d.rect(py - 0.17, 0, py + 0.17, ONE[0], fill=C["bronze"], stroke=C["bronze"], sw=0.4)
    d.rect(-1, ONE[0], D + 1, ONE[1], fill=C["bronze"], stroke=C["bronze"], sw=0.5)
    d.rect(pr["roof"][1], ONE[0] - 0.3, pr["roof"][3], ONE[0], fill=C["cedar"], stroke=C["ink"], sw=0.4)
    levels(d, D + 2.5, [(0.0, "GRADE 0'-0\""), (FF, "FLOOR 1'-0\""), (ONE[1], "ROOF EDGE 12'-3\"")])
    leader(d, 8.0, 5.0, 8.0, -2.6, "10 FT SLIDER UNDER THE PORCH")
    d.text(0, -2.2, "FRONT", 6.5, fill=C["mid"])
    return d


def casita_section(name, title, cut_y=8.0):
    """Section C: across the living room and porch (cut at y = 8, looking toward the back). Drawing x = plan x."""
    d = Drawing(name, title)
    cs = H.CASITA
    W = cs["W"]
    pr = cs["porch"]
    grade(d, -1, pr["roof"][2])
    cut = dict(fill=C["cut"], stroke=C["cut"], sw=0.4, layer="A-SECT")
    d.rect(0, 0, W, FF, **cut)
    d.rect(0, FF, 0.5, ONE[0], **cut)
    d.rect(W - 0.5, FF, W, FF + 0.0 + 0.01, **cut)
    d.rect(W - 0.5, FF, W, FF + 8.0, fill=C["glass"], stroke=C["bronze"], sw=0.6)     # the slider, cut
    d.rect(W - 0.5, FF + 8.0, W, ONE[0], **cut)
    d.rect(-1, ONE[0], pr["roof"][2], ONE[1], **cut)
    d.rect(W, ONE[0] - 0.3, pr["roof"][2], ONE[0], fill=C["cedar"], stroke=C["ink"], sw=0.4)
    d.rect(pr["posts"][0][0] - 0.17, 0, pr["posts"][0][0] + 0.17, ONE[0], fill=C["bronze"], stroke=C["bronze"],
           sw=0.4)
    d.rect(W, -0.1, pr["rect"][2], 0.08, fill=C["stone"], stroke=C["ink"], sw=0.3)    # terrace pavers
    d.text(10.0, FF + 4.0, "LIVING + KITCHEN", 6.4, fill=C["mid"])
    d.text(24.0, 4.0, "PORCH", 6.4, fill=C["mid"])
    levels(d, pr["roof"][2] + 1.5, [(0.0, "GRADE 0'-0\""), (FF, "FLOOR 1'-0\""), (ONE[0], "CEILING 11'-0\""),
                                    (ONE[1], "ROOF EDGE 12'-3\"")])
    return d


def all_drawings():
    return dict(
        front_gc=casa02_front(H.CASA02_GF_CARPORT, "front_gc", "Front, carport version"),
        back_gc=casa02_back(H.CASA02_GF_CARPORT, "back_gc", "Back, toward the pátio"),
        side_gc=casa02_side(H.CASA02_GF_CARPORT, "side_gc", "Outer side, carport version"),
        front_gs=casa02_front(H.CASA02_GF_SUITE, "front_gs", "Front, suite version"),
        front_gd=casa02_front(H.CASA02_GF_SIDE, "front_gd", "Front, side-drive version"),
        side_gd=casa02_side(H.CASA02_GF_SIDE, "side_gd", "Drive side, side-drive version"),
        sect_a=casa02_section_long(H.CASA02_GF_CARPORT, "sect_a", "Section A, through the stair"),
        cs_front=casita_front("cs_front", "Casita front"),
        cs_side=casita_side("cs_side", "Casita porch side"),
        cs_sect=casita_section("cs_sect", "Section C, Casita living + porch"),
    )


# ---------------------------------------------------------------- SVG
def to_svg(d, scale=13.0, pad=12):
    sys.path.insert(0, os.path.join(os.path.dirname(P2), "casa01"))
    import drawings as DR
    svg = DR.SVG(d.x0 - 0.5, d.z0 - 1.0, d.x1 + 0.5, d.z1 + 1.0, scale=scale, pad=pad)
    for it in d.items:
        dash = f'stroke-dasharray="{it["dash"]}"' if it.get("dash") else ""
        if it["k"] == "poly":
            svg.poly(it["pts"], fill=it["fill"], stroke=it["stroke"], sw=it["sw"], extra=dash)
        elif it["k"] == "line":
            svg.line(it["a"][0], it["a"][1], it["b"][0], it["b"][1], it["stroke"], it["sw"], extra=dash)
        elif it["k"] == "circle":
            svg.circle(it["c"][0], it["c"][1], it["r"], fill=it["fill"], stroke=it["stroke"], sw=it["sw"])
        elif it["k"] == "text":
            svg.text(it["p"][0], it["p"][1], it["s"], it["size"], anchor=it["anchor"], fill=it["fill"],
                     weight=it["weight"], ls=0.6, extra='dy="2.2"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg.w:.0f} {svg.h:.0f}" '
            f'preserveAspectRatio="xMidYMid meet"><rect width="100%" height="100%" fill="#ffffff"/>'
            f'{"".join(svg.items)}</svg>')


def main():
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    for k, d in all_drawings().items():
        open(os.path.join(out, f"elev_{k}.svg"), "w").write(to_svg(d))
        print(k, len(d.items), "items", f"{d.x1 - d.x0:.0f} x {d.z1 - d.z0:.0f} ft")


if __name__ == "__main__":
    main()
