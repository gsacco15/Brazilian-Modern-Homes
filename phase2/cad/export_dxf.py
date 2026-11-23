"""Phase 2 AutoCAD file: every home plan as a block, every site built from those blocks, one sheet per layout.

    PYTHONPATH=<ezdxf> python3 phase2/cad/export_dxf.py      ->  phase2/cad/Phase2_Concepts.dxf

Units are inches (architectural). Model space holds:
  - the four plans side by side (blocks C02-GC, C02-GS, C02-UP, CS) with room names and dimensions;
  - the five sites to the right, each built by inserting those blocks (mirrored or rotated as the site needs).
Edit a block once and every site that uses it updates.
Paper space has one layout per sheet: C-1 Casa 02, C-2 Casita, C-3..C-7 one per site, each with a title block
and a viewport at a standard architectural scale; then A-101..A-103, the developed Casa 02 plans (below the concept
plans in model space) with dimension strings, door and window tags, and their schedules in paper space.
"""
import math
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from model import homes as H  # noqa: E402
from model.sites import SITES, HOME_RULES, footprint, garden_wall, tp  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "plans"))
import plans as PL  # noqa: E402  (developed plans: sheets, tags, schedules, the same as the PDF)

OUT = os.path.join(HERE, "Phase2_Concepts.dxf")
IN = 12.0  # inches per foot

LAYERS = [  # name, colour, lineweight (1/100 mm), linetype
    ("A-WALL", 7, 50, "Continuous"), ("A-WALL-INTR", 7, 35, "Continuous"), ("A-WALL-PATT", 8, 0, "Continuous"),
    ("A-DOOR", 3, 18, "Continuous"), ("A-GLAZ", 4, 18, "Continuous"), ("A-FLOR-FIXT", 8, 13, "Continuous"),
    ("A-FURN", 9, 13, "Continuous"), ("A-FLOR-STRS", 7, 18, "Continuous"), ("A-COLS", 7, 35, "Continuous"),
    ("A-GATE", 30, 25, "DASHED"), ("A-OVHD", 8, 18, "DASHED"), ("A-AREA-IDEN", 7, 18, "Continuous"),
    ("A-WALL-SCRN", 7, 25, "Continuous"), ("A-ROOF-OTLN", 8, 18, "DASHED"),
    ("A-ANNO-SYMB", 7, 18, "Continuous"), ("A-ANNO-SCHD", 7, 18, "Continuous"),
    ("A-WALL-STON", 41, 35, "Continuous"), ("L-PAVE-CALC", 250, 18, "Continuous"),
    ("A-ANNO-DIMS", 7, 13, "Continuous"), ("A-ANNO-TEXT", 7, 18, "Continuous"),
    ("C-PROP", 1, 35, "PHANTOM"), ("C-SETB", 8, 13, "DASHED"), ("C-ROAD", 8, 13, "Continuous"),
    ("C-PAVE", 8, 13, "Continuous"), ("L-PLNT", 3, 13, "Continuous"), ("L-TREE", 3, 18, "Continuous"),
    ("L-FENC", 30, 25, "Continuous"), ("L-WALL", 7, 35, "Continuous"), ("L-PATH", 8, 13, "Continuous"),
    ("G-TTLB", 7, 35, "Continuous"), ("G-TTLB-TEXT", 7, 18, "Continuous"), ("G-VPRT", 8, 13, "Continuous"),
]

PLANS = [("C02-GC", H.CASA02_GF_CARPORT, "CASA 02 - GROUND FLOOR, CARPORT"),
         ("C02-GS", H.CASA02_GF_SUITE, "CASA 02 - GROUND FLOOR, SUITE"),
         ("C02-UP", H.CASA02_UPPER, "CASA 02 - UPPER FLOOR (BOTH VERSIONS)"),
         ("CS", H.CASITA, "CASITA")]
BLOCK_OF = {id(p): name for name, p, _ in PLANS}


def ft_in(v):
    f = int(v + 1e-6)
    i = round((v - f) * 12)
    if i == 12:
        f, i = f + 1, 0
    return f"{f}'-{i}\""


# ---------------------------------------------------------------- plan geometry into a block
def pts_in(pts):
    return [(x * IN, y * IN) for x, y in pts]


def ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def build_block(doc, name, plan):
    blk = doc.blocks.new(name=name)

    def poly(pts, layer, closed=True, hatch=False):
        p = pts_in(pts)
        blk.add_lwpolyline(p, close=closed, dxfattribs={"layer": layer})
        if hatch:
            h = blk.add_hatch(color=7, dxfattribs={"layer": "A-WALL-PATT"})
            h.paths.add_polyline_path(p, is_closed=True)

    def line(a, b, layer):
        blk.add_line((a[0] * IN, a[1] * IN), (b[0] * IN, b[1] * IN), dxfattribs={"layer": layer})

    for w in plan["walls"]:
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        th = w["t"]
        d0, d1 = (0.0, th) if w["ext"] else (-th / 2, th / 2)
        layer = "A-WALL" if w["ext"] else "A-WALL-INTR"

        def P(s, d):
            return (ax + ux * s + nx * d, ay + uy * s + ny * d)
        cuts = sorted(w["openings"], key=lambda o: o["off"])
        s = 0.0
        for o in cuts + [dict(off=L, w=0, kind="end")]:
            if o["off"] - s > 1e-6:
                poly([P(s, d0), P(o["off"], d0), P(o["off"], d1), P(s, d1)], layer, hatch=True)
            s = o["off"] + o["w"]
        for o in cuts:
            s0, s1 = o["off"], o["off"] + o["w"]
            if o["kind"] in ("window", "slider"):
                line(P(s0, d0), P(s0, d1), "A-GLAZ")
                line(P(s1, d0), P(s1, d1), "A-GLAZ")
                if o["kind"] == "window":
                    for f in (0.38, 0.62):
                        line(P(s0, d0 + (d1 - d0) * f), P(s1, d0 + (d1 - d0) * f), "A-GLAZ")
                else:
                    mid = (s0 + s1) / 2
                    line(P(s0, d0 + (d1 - d0) * 0.3), P(mid + 0.25, d0 + (d1 - d0) * 0.3), "A-GLAZ")
                    line(P(mid - 0.25, d0 + (d1 - d0) * 0.7), P(s1, d0 + (d1 - d0) * 0.7), "A-GLAZ")
            elif o["kind"] == "door":
                sg = 1.0 if o["side"] == "L" else -1.0
                face = d1 if sg > 0 else d0
                hs, cs = (s0, s1) if o["hinge"] == "s" else (s1, s0)
                hx, hy = P(hs, face)
                cx_, cy_ = P(cs, face)
                ex, ey = hx + nx * sg * o["w"], hy + ny * sg * o["w"]
                line((hx, hy), (ex, ey), "A-DOOR")
                a0 = math.degrees(math.atan2(cy_ - hy, cx_ - hx))
                a1 = math.degrees(math.atan2(ey - hy, ex - hx))
                d = (a1 - a0 + 180) % 360 - 180
                start, end = (a0, a1) if d > 0 else (a1, a0)
                blk.add_arc((hx * IN, hy * IN), o["w"] * IN, start, end, dxfattribs={"layer": "A-DOOR"})
    for f in plan.get("fixtures", []):
        k = f["kind"]
        lay = "A-FURN" if k in ("bed", "sofa", "table", "car", "desk") else "A-FLOR-FIXT"
        if k == "wc":
            x, y = f["at"]
            dirn = 1 if f.get("rot", 0) == 0 else -1
            poly([(x - 0.85, y - 0.3), (x + 0.85, y - 0.3), (x + 0.85, y + 0.3), (x - 0.85, y + 0.3)], lay)
            poly(ellipse(x, y + dirn * 1.25, 0.62, 0.92), lay)
            continue
        x0, y0, x1, y1 = f["rect"]
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if k == "range":
            for ox in (-0.5, 0.5):
                for oy in (-0.45, 0.45):
                    blk.add_circle(((cx + ox) * IN, (cy + oy) * IN), 0.32 * IN, dxfattribs={"layer": lay})
        elif k in ("sink", "lav"):
            poly(ellipse(cx, cy, (x1 - x0) * 0.32, (y1 - y0) * 0.32), lay)
        elif k == "shower":
            blk.add_circle((cx * IN, cy * IN), 0.18 * IN, dxfattribs={"layer": lay})
            line((x0, y0), (x1, y1), lay)
        elif k == "bed":
            south = f.get("head") == "s"
            pa, pb = (y0 + 0.3, y0 + 1.3) if south else (y1 - 1.3, y1 - 0.3)
            for px0 in (x0 + 0.3, cx + 0.15):
                poly([(px0, pa), (px0 + (x1 - x0) / 2 - 0.45, pa), (px0 + (x1 - x0) / 2 - 0.45, pb), (px0, pb)], lay)
            yl = y0 + 2.0 if south else y1 - 2.0
            line((x0, yl), (x1, yl), lay)
        elif k == "tub":
            poly([(x0 + 0.3, y0 + 0.3), (x1 - 0.3, y0 + 0.3), (x1 - 0.3, y1 - 0.3), (x0 + 0.3, y1 - 0.3)], lay)
        elif k == "mech":
            line((x0, y0), (x1, y1), lay)
            line((x0, y1), (x1, y0), lay)
        elif k == "wd":
            if (x1 - x0) >= (y1 - y0):
                line(((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), lay)
            else:
                line((x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2), lay)
        elif k == "car":
            pass
    st = plan.get("stair")
    if st:                                        # treads to the cut line, the rest overhead (dashed); arrow
        x0, y0, x1, y1 = st["rect"]
        top_front = st.get("top", "back") == "front"
        foot, top = (y1, y0) if top_front else (y0, y1)
        sgn = -1.0 if top_front else 1.0
        n = st.get("risers", 17) - 1
        run = abs(top - foot) / n
        upper = st.get("floor") == "upper"
        cut = None if upper else st.get("cut")
        end = top if cut is None else cut
        ya, yb = sorted((foot, end))
        poly([(x0, ya), (x1, ya), (x1, yb), (x0, yb)], "A-FLOR-STRS")
        for i in range(1, n):
            y = foot + sgn * i * run
            if (y - end) * sgn > 1e-6:
                break
            line((x0, y), (x1, y), "A-FLOR-STRS")
        if cut is not None:
            blk.add_lwpolyline(pts_in([(x0, cut - sgn * 0.35), ((x0 + x1) / 2 - 0.3, cut - sgn * 0.35),
                                       ((x0 + x1) / 2, cut + sgn * 0.35), (x1, cut + sgn * 0.35)]),
                               dxfattribs={"layer": "A-FLOR-STRS"})
            za, zb = sorted((cut, top))
            poly([(x0, za), (x1, za), (x1, zb), (x0, zb)], "A-OVHD")
        cx = (x0 + x1) / 2
        a, tip = ((cx, top - sgn * 0.5), (cx, foot + sgn * 1.0)) if upper else ((cx, foot - sgn * 0.5), (cx, end - sgn * 1.0))
        line(a, tip, "A-FLOR-STRS")
        d = 1.0 if tip[1] > a[1] else -1.0
        poly([tip, (cx - 0.3, tip[1] - d * 0.6), (cx + 0.3, tip[1] - d * 0.6)], "A-FLOR-STRS")
    for (ax, ay), (bx, by) in plan.get("slats", []):        # cedar slats beside the stair
        line((ax, ay), (bx, by), "A-GATE")
    if any(r.get("outdoor") for r in plan["rooms"]):
        poly([(0, 0), (plan["W"], 0), (plan["W"], plan["D"]), (0, plan["D"])], "A-OVHD")
    for cx, cy in plan.get("columns", []):
        poly([(cx - 0.3, cy - 0.3), (cx + 0.3, cy - 0.3), (cx + 0.3, cy + 0.3), (cx - 0.3, cy + 0.3)], "A-COLS", hatch=True)
    if plan.get("gate"):
        (gx0, gy0), (gx1, gy1) = plan["gate"]
        line((gx0, gy0 + 0.25), (gx1, gy1 + 0.25), "A-GATE")
    for run in H.stone_runs(plan):                # Lueders limestone ashlar on the outer face
        (ax, ay), (ux, uy), (nx, ny), L_ = run["a"], run["u"], run["n"], run["L"]
        s0 = 0.0
        spans = []
        for h0, h1, _o in run["holes"]:
            if h0 > s0:
                spans.append((s0, h0))
            s0 = max(s0, h1)
        if s0 < L_:
            spans.append((s0, L_))
        for q0, q1 in spans:
            P = [(ax + ux * q + nx * d, ay + uy * q + ny * d) for q, d in ((q0, 0), (q1, 0), (q1, 0.34), (q0, 0.34))]
            p_ = pts_in(P)
            blk.add_lwpolyline(p_, close=True, dxfattribs={"layer": "A-WALL-STON"})
            hh = blk.add_hatch(color=41, dxfattribs={"layer": "A-WALL-STON"})
            hh.set_pattern_fill("ANSI31", scale=2.0)
            hh.paths.add_polyline_path(p_, is_closed=True)
    for r in plan.get("stone", {}).get("piers", []):
        x0, y0, x1, y1 = r
        p_ = pts_in([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        blk.add_lwpolyline(p_, close=True, dxfattribs={"layer": "A-WALL-STON"})
        hh = blk.add_hatch(color=41, dxfattribs={"layer": "A-WALL-STON"})
        hh.set_pattern_fill("ANSI31", scale=2.0)
        hh.paths.add_polyline_path(p_, is_closed=True)
    for r in plan.get("calcada", []):             # black calçada with its light band
        x0, y0, x1, y1 = r
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "L-PAVE-CALC")
        b = 0.3 if min(x1 - x0, y1 - y0) > 1.5 else 0.12
        p_ = pts_in([(x0 + b, y0 + b), (x1 - b, y0 + b), (x1 - b, y1 - b), (x0 + b, y1 - b)])
        blk.add_lwpolyline(p_, close=True, dxfattribs={"layer": "L-PAVE-CALC"})
        hh = blk.add_hatch(color=250, dxfattribs={"layer": "L-PAVE-CALC"})
        hh.set_pattern_fill("AR-SAND", scale=1.0)
        hh.paths.add_polyline_path(p_, is_closed=True)
    lan = plan.get("lantern")                     # cobogó screen, two stories (facade direction C)
    if lan:
        (x0, x1), (y0, y1) = lan["x"], lan["y"]
        op = lan.get("opening")
        for a, b in ([(x0, op[0]), (op[1], x1)] if op else [(x0, x1)]):
            if b - a > 0.01:
                cobogo(blk, a, b, y0, y1)
        if op:
            poly([(op[0], y0), (op[1], y0), (op[1], y1), (op[0], y1)], "A-OVHD")
    pr = plan.get("porch")                        # the Casita's covered porch: roof outline and two posts
    if pr:
        x0, y0, x1, y1 = pr["roof"]
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "A-ROOF-OTLN")
        for cx, cy in pr["posts"]:
            poly([(cx - 0.25, cy - 0.25), (cx + 0.25, cy - 0.25), (cx + 0.25, cy + 0.25), (cx - 0.25, cy + 0.25)],
                 "A-COLS", hatch=True)
    return blk


def cobogo(space, x0, x1, y0, y1, ox=0.0, oy=0.0):
    """A cobogó screen in plan on layer A-WALL-SCRN: the band, and one ring per 12 in block."""
    space.add_lwpolyline([((ox + x0) * IN, (oy + y0) * IN), ((ox + x1) * IN, (oy + y0) * IN),
                          ((ox + x1) * IN, (oy + y1) * IN), ((ox + x0) * IN, (oy + y1) * IN)], close=True,
                         dxfattribs={"layer": "A-WALL-SCRN"})
    n = max(1, int(round(x1 - x0)))
    for i in range(n):
        cx = ox + x0 + (x1 - x0) * (i + 0.5) / n
        space.add_circle((cx * IN, (oy + (y0 + y1) / 2) * IN), 1.2, dxfattribs={"layer": "A-WALL-SCRN"})


# ---------------------------------------------------------------- model space helpers
def text(msp, x, y, s, h, layer="A-ANNO-TEXT", align=TextEntityAlignment.MIDDLE_CENTER):
    t = msp.add_text(s, height=h, dxfattribs={"layer": layer, "style": "LATO"})
    t.set_placement((x, y), align=align)
    return t


def rect(msp, x0, y0, x1, y1, layer, hatch=None, color=None):
    p = [(x0 * IN, y0 * IN), (x1 * IN, y0 * IN), (x1 * IN, y1 * IN), (x0 * IN, y1 * IN)]
    msp.add_lwpolyline(p, close=True, dxfattribs={"layer": layer})
    if hatch:
        h = msp.add_hatch(color=color or 8, dxfattribs={"layer": layer})
        if hatch == "SOLID":
            h.set_solid_fill(color=color or 254)
        else:
            h.set_pattern_fill(hatch, scale=hatch_scale(hatch))
        h.paths.add_polyline_path(p, is_closed=True)


def hatch_scale(name):
    return {"GRASS": 14.0, "AR-SAND": 3.0, "AR-CONC": 1.5, "ANSI31": 12.0, "DOTS": 8.0}.get(name, 6.0)


def dim(msp, a, b, base, angle=0):
    length = abs(b[1] - a[1]) if angle == 90 else abs(b[0] - a[0])
    d = msp.add_linear_dim(base=(base[0] * IN, base[1] * IN), p1=(a[0] * IN, a[1] * IN), p2=(b[0] * IN, b[1] * IN),
                           angle=angle, text=ft_in(length), dimstyle="ARCH", dxfattribs={"layer": "A-ANNO-DIMS"})
    d.render()


def insert(msp, block, t, origin):
    """Insert a home block where transform t puts it, shifted by the site's origin (ft)."""
    x, y = tp(t, 0.0, 0.0)
    return msp.add_blockref(block, ((x + origin[0]) * IN, (y + origin[1]) * IN),
                            dxfattribs={"rotation": t["rot"], "xscale": -1 if t["mirror"] else 1, "layer": "0"})


def feature_labels(msp, plan, t, origin, h, full=True):
    """Labels for the facade features drawn in the blocks: the cobogó screen and the Casita's porch."""
    def at(x, y):
        X, Y = tp(t, x, y) if t else (x, y)
        return (X + origin[0]) * IN, (Y + origin[1]) * IN
    lan = plan.get("lantern")
    if lan and full:
        text(msp, *at(sum(lan["x"]) / 2, lan["y"][0] - 1.4), "COBOGÓ SCREEN, TWO STORIES", h * 0.6)
    pr = plan.get("porch")
    if pr:
        x0, y0, x1, y1 = pr["rect"]
        X, Y = at((x0 + x1) / 2, (y0 + y1) / 2)
        if full:
            text(msp, X, Y + h * 0.6, "COVERED PORCH", h, "A-AREA-IDEN")
            text(msp, X, Y - h * 0.8, f"{ft_in(x1 - x0)} x {ft_in(y1 - y0)}", h * 0.75, "A-AREA-IDEN")
        else:
            text(msp, X, Y, "PORCH", h, "A-AREA-IDEN")


def draw_garden_wall(msp, s, origin):
    """The Casita's street wall: limestone piers, a cedar gate into the garden, cobogó between."""
    gw = garden_wall(s)
    if not gw:
        return
    ox, oy = origin
    y = gw["y"]
    for p0, p1 in gw["piers"]:
        rect(msp, ox + p0, oy + y - 0.4, ox + p1, oy + y + 0.4, "L-WALL", hatch="AR-SAND", color=8)
    c0, c1 = gw["cobogo"]
    cobogo(msp, c0, c1, y - 0.17, y + 0.17, ox, oy)
    text(msp, (ox + (c0 + c1) / 2) * IN, (oy + y - 2.1) * IN, "COBOGÓ", 8)
    if gw["gate"]:
        g0, g1 = gw["gate"]
        msp.add_line(((ox + g0) * IN, (oy + y) * IN), ((ox + g0) * IN, (oy + y + g1 - g0) * IN),
                     dxfattribs={"layer": "A-GATE"})
        msp.add_arc(((ox + g0) * IN, (oy + y) * IN), (g1 - g0) * IN, 0, 90, dxfattribs={"layer": "A-GATE"})
        text(msp, (ox + (g0 + g1) / 2) * IN, (oy + y - 2.1) * IN, "CEDAR GATE", 8)


def room_labels(msp, plan, t, origin, h, dims=True):
    for room in plan["rooms"]:
        if room.get("label") is False:
            continue
        x0, y0, x1, y1 = room["rect"]
        lx, ly = room.get("lab", ((x0 + x1) / 2, (y0 + y1) / 2)) if dims else ((x0 + x1) / 2, (y0 + y1) / 2)
        X, Y = tp(t, lx, ly) if t else (lx, ly)
        X, Y = (X + origin[0]) * IN, (Y + origin[1]) * IN
        narrow = (x1 - x0) < 7.5
        name = room.get("short", room["name"]) if (narrow or not dims) else room["name"]
        text(msp, X, Y + (h * 0.6 if dims and not narrow else 0), name.upper(), h, "A-AREA-IDEN")
        if dims and not narrow:
            text(msp, X, Y - h * 0.8, f"{ft_in(x1 - x0)} x {ft_in(y1 - y0)}", h * 0.75, "A-AREA-IDEN")


# ---------------------------------------------------------------- sites in model space
def draw_site(msp, s, origin):
    ox, oy = origin
    W, L = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    # street, alley, side street
    rect(msp, ox - 6, oy - 14, ox + W + (13 if lot.get("corner") else 6), oy - 6, "C-ROAD")
    text(msp, (ox + W / 2) * IN, (oy - 10) * IN, "STREET", 18, "C-ROAD")
    if lot.get("alley"):
        rect(msp, ox - 6, oy + L + 1, ox + W + 6, oy + L + 13, "C-ROAD")
        text(msp, (ox + W / 2) * IN, (oy + L + 7) * IN, "ALLEY", 18, "C-ROAD")
    if lot.get("corner"):
        rect(msp, ox + W + 1, oy - 14, ox + W + 13, oy + L + 6, "C-ROAD")
        t = text(msp, (ox + W + 7) * IN, (oy + L / 2) * IN, "SIDE STREET", 18, "C-ROAD")
        t.dxf.rotation = 90
    # lot line and setbacks
    rect(msp, ox, oy, ox + W, oy + L, "C-PROP")
    rect(msp, ox + HOME_RULES["side"], oy + HOME_RULES["front"], ox + W - HOME_RULES["side"],
         oy + L - HOME_RULES["rear"], "C-SETB")
    for p in s["patios"]:
        rect(msp, ox + p[0], oy + p[1], ox + p[2], oy + p[3], "L-PLNT", hatch="GRASS", color=3)
    for k, r in s["pave"]:
        rect(msp, ox + r[0], oy + r[1], ox + r[2], oy + r[3], "C-PAVE", hatch="AR-CONC" if k != "Terrace" else "AR-SAND",
             color=8)
        if k in ("Drive", "Parking") and (r[3] - r[1]) > 12:
            t = text(msp, (ox + (r[0] + r[2]) / 2) * IN, (oy + (r[1] + r[3]) / 2) * IN, k.upper(), 14, "C-PAVE")
            if (r[2] - r[0]) < (r[3] - r[1]):
                t.dxf.rotation = 90
    for pts in s.get("paths", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 2.2))
            for i in range(n):
                f = (i + 0.5) / n
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                rect(msp, ox + x - 0.8, oy + y - 0.55, ox + x + 0.8, oy + y + 0.55, "L-PATH")
    for x, y, r in s["trees"]:
        msp.add_circle(((ox + x) * IN, (oy + y) * IN), r * IN, dxfattribs={"layer": "L-TREE"})
        msp.add_circle(((ox + x) * IN, (oy + y) * IN), 0.4 * IN, dxfattribs={"layer": "L-TREE"})
    for pts in s.get("fence", []):
        msp.add_lwpolyline([((ox + x) * IN, (oy + y) * IN) for x, y in pts], dxfattribs={"layer": "L-FENC"})
    for pts in s.get("walls", []):
        msp.add_lwpolyline([((ox + x) * IN, (oy + y) * IN) for x, y in pts], dxfattribs={"layer": "L-WALL",
                                                                                         "const_width": 6})
    for r in s.get("calcada", []):                 # site calçada (the Casita's garden landing)
        rect(msp, ox + r[0], oy + r[1], ox + r[2], oy + r[3], "L-PAVE-CALC", hatch="AR-SAND", color=250)
    draw_garden_wall(msp, s, origin)
    for h in s["homes"]:
        insert(msp, BLOCK_OF[id(h["plan"])], h["t"], origin)
        room_labels(msp, h["plan"], h["t"], origin, 9, dims=False)
        feature_labels(msp, h["plan"], h["t"], origin, 9, full=False)
        x0, y0, x1, y1 = footprint(h["t"])
        tx, ty = h.get("tag") or ((x0 + x1) / 2, (y0 - 2.4 if y0 > 18 else y1 + 3.2))
        fa = h["plan"]["enclosed"] + (H.CASA02_UPPER["enclosed"] if h["plan"] is not H.CASITA else 0)
        text(msp, (ox + tx) * IN, (oy + ty) * IN, f"{h['id']} - {h['kind'].upper()}", 15)
        text(msp, (ox + tx) * IN, (oy + ty - 1.6) * IN, f"{h['beds']} - {fa:,.0f} SF", 11)
    dim(msp, (ox, oy + L), (ox + W, oy + L), (ox, oy + L + (16 if lot.get("alley") else 4)))
    dim(msp, (ox, oy), (ox, oy + L), (ox - 4, oy), angle=90)
    text(msp, (ox + W / 2) * IN, (oy - 20) * IN, f"{s['id']}  {s['name'].upper()}", 24)


# ---------------------------------------------------------------- developed plans (A-101..A-103)
def developed(msp, origin, sh):
    """One developed plan in model space: the block, room names with sizes and areas, tags and dimension strings."""
    ox, oy = origin
    plan = sh["plan"]
    W, D = plan["W"], plan["D"]
    msp.add_blockref(BLOCK_OF[id(plan)], (ox * IN, oy * IN), dxfattribs={"layer": "0"})
    for r in plan["rooms"]:
        if r.get("label") is False:
            continue
        x0, y0, x1, y1 = r["rect"]
        lx, ly = r.get("lab", ((x0 + x1) / 2, (y0 + y1) / 2))
        narrow = (x1 - x0) < 7.5
        name = r.get("short", r["name"]) if narrow else r["name"]
        area = (x1 - x0) * (y1 - y0)
        size = f"{area:,.0f} SF" if narrow else f"{ft_in(x1 - x0)} x {ft_in(y1 - y0)} - {area:,.0f} SF"
        text(msp, (ox + lx) * IN, (oy + ly + 0.35) * IN, name.upper(), 6.5, "A-AREA-IDEN")
        text(msp, (ox + lx) * IN, (oy + ly - 0.6) * IN, size, 4.5, "A-AREA-IDEN")
    doors, wins = PL.openings(plan, sh["floor"])
    for kind, label, x, y in PL.tag_positions(plan, doors, wins):
        X, Y = (ox + x) * IN, (oy + y) * IN
        if kind == "door":
            msp.add_circle((X, Y), 0.95 * IN, dxfattribs={"layer": "A-ANNO-SYMB"})
        else:
            r_ = 1.15 * IN
            msp.add_lwpolyline([(X - r_, Y), (X, Y + r_ * 0.8), (X + r_, Y), (X, Y - r_ * 0.8)], close=True,
                               dxfattribs={"layer": "A-ANNO-SYMB"})
        text(msp, X, Y, label, 4.2, "A-ANNO-SYMB")
    ch = sh["chains"]

    def chain(pts, axis, at, off):
        for a, b in zip(pts, pts[1:]):
            if axis == "x":
                dim(msp, (ox + a, oy + at), (ox + b, oy + at), (ox + a, oy + at + off))
            else:
                dim(msp, (ox + at, oy + a), (ox + at, oy + b), (ox + at + off, oy + a), angle=90)
        k = 1 if off > 0 else -1
        if axis == "x":
            dim(msp, (ox + pts[0], oy + at), (ox + pts[-1], oy + at), (ox, oy + at + off + k * 2.3))
        else:
            dim(msp, (ox + at, oy + pts[0]), (ox + at, oy + pts[-1]), (ox + at + off + k * 2.3, oy), angle=90)
    chain(ch["front"], "x", 0.0, -4.3)
    chain(ch["west"], "y", 0.0, -3.4)
    chain(ch["east"], "y", W, 3.4)
    if ch.get("back"):
        for a, b in zip(ch["back"], ch["back"][1:]):
            dim(msp, (ox + a, oy + D), (ox + b, oy + D), (ox + a, oy + D + 3.0))
    if plan.get("lantern"):
        text(msp, (ox + W + 1.2) * IN, (oy - 2.0) * IN, "COBOGÓ SCREEN", 5, align=TextEntityAlignment.MIDDLE_LEFT)
    text(msp, (ox + W / 2) * IN, (oy - 8.2) * IN, "FRONT", 6)
    st = plan.get("stair")
    if st:                                       # UP at the foot downstairs, DN at the top upstairs
        x0, y0, x1, y1 = st["rect"]
        foot, top = (y1, y0) if st.get("top") == "front" else (y0, y1)
        sgn = -1.0 if st.get("top") == "front" else 1.0
        up = st.get("floor") == "upper"
        ly = (top - sgn * 1.3) if up else (foot - sgn * 1.4)
        text(msp, (ox + (x0 + x1) / 2) * IN, (oy + ly) * IN, "DN" if up else "UP", 5)
    return doors, wins


def schedules(lay, sh, doors, wins):
    """Door and window schedules and the notes, as text in paper space to the right of the viewport."""
    def t(x, y, s, h=0.085):
        e = lay.add_text(s, height=h, dxfattribs={"layer": "A-ANNO-SCHD", "style": "LATO"})
        e.set_placement((x, y), align=TextEntityAlignment.LEFT)
    plan = sh["plan"]
    x0, y = 9.75, 10.25
    t(x0, y, f"CASA 02 - {sh['title'].upper()}", 0.15)
    y -= 0.42
    t(x0, y, "DOORS", 0.1)
    cols = (0.0, 0.45, 2.15, 3.15)
    y -= 0.22
    for c, h in zip(cols, ("TAG", "FROM - TO", "SIZE", "TYPE")):
        t(x0 + c, y, h, 0.07)
    lay.add_line((x0, y - 0.06), (14.05, y - 0.06), dxfattribs={"layer": "A-ANNO-SCHD"})
    for d in doors:
        row = PL.door_row(d, plan)
        y -= 0.18
        for c, v in zip(cols, (row[0], row[1].replace("→", "-"), row[2].replace("×", "x"), row[3])):
            t(x0 + c, y, v)
        if row[4]:
            y -= 0.14
            t(x0 + 0.45, y, row[4], 0.07)
    y -= 0.38
    t(x0, y, "WINDOWS", 0.1)
    cols = (0.0, 0.5, 1.6, 2.6, 3.1, 3.6)
    y -= 0.22
    for c, h in zip(cols, ("TAG", "ROOM", "SIZE", "SILL", "HEAD", "")):
        t(x0 + c, y, h, 0.07)
    lay.add_line((x0, y - 0.06), (14.05, y - 0.06), dxfattribs={"layer": "A-ANNO-SCHD"})
    for w_ in wins:
        row = PL.win_row(w_, plan)
        y -= 0.18
        for c, v in zip(cols[:5], (row[0], row[1], row[2].replace("×", "x"), row[3], row[4])):
            t(x0 + c, y, v)
        if row[5]:
            y -= 0.14
            t(x0 + 0.5, y, row[5], 0.07)
    y -= 0.38
    t(x0, y, "NOTES", 0.1)
    notes = PL.SHEET_NOTES[sh["no"]] + PL.GENERAL
    m = lay.add_mtext(r"\P".join(f"- {n}" for n in notes), dxfattribs={"layer": "A-ANNO-SCHD", "style": "LATO",
                                                                         "char_height": 0.07, "width": 4.3})
    m.set_location((x0, y - 0.12))


# ---------------------------------------------------------------- paper space
def title_block(lay, sheet, title, scale, phase="CONCEPT"):
    """17 x 11 in sheet: border, a 2.3 in title strip on the right."""
    def r(x0, y0, x1, y1):
        lay.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "G-TTLB"})

    def t(x, y, s, h, align=TextEntityAlignment.LEFT):
        e = lay.add_text(s, height=h, dxfattribs={"layer": "G-TTLB-TEXT", "style": "LATO"})
        e.set_placement((x, y), align=align)
    r(0.35, 0.35, 14.15, 10.65)
    r(14.35, 0.35, 16.65, 10.65)
    t(14.5, 10.3, "BRAZILIAN MODERN HOMES", 0.11)
    t(14.5, 10.08, "RESIDENTIAL DESIGN - AUSTIN", 0.08)
    t(14.5, 9.6, "PHASE 2", 0.16)
    t(14.5, 9.35, "CASA 02 + CASITA" if phase == "CONCEPT" else "CASA 02", 0.16)
    t(14.5, 9.05, "CONCEPT DESIGN" if phase == "CONCEPT" else "DEVELOPED FLOOR PLANS", 0.08)
    t(14.5, 2.75, "SHEET TITLE", 0.07)
    t(14.5, 2.55, title, 0.12 if len(title) <= 20 else 0.095)
    t(14.5, 2.25, "SCALE", 0.07)
    t(14.5, 2.05, scale, 0.12)
    t(14.5, 1.75, "DATE / PHASE", 0.07)
    t(14.5, 1.55, "NOV 2026 - " + ("CONCEPT" if phase == "CONCEPT" else "DESIGN DEV."), 0.12)
    t(14.5, 0.85, sheet, 0.5)
    t(14.5, 0.5, "CONCEPT. NOT FOR CONSTRUCTION." if phase == "CONCEPT" else "NOT FOR CONSTRUCTION.", 0.07)


def sheet(doc, name, sheet_no, title, scale_txt, scale, center_ft, size_in=(13.4, 9.9), phase="CONCEPT"):
    lay = doc.layouts.new(name)
    lay.page_setup(size=(17, 11), margins=(0, 0, 0, 0), units="inch")
    title_block(lay, sheet_no, title, scale_txt, phase)
    cx, cy = 0.35 + 0.4 + size_in[0] / 2, 0.35 + 0.35 + size_in[1] / 2
    vp = lay.add_viewport(center=(cx, cy), size=size_in, view_center_point=(center_ft[0] * IN, center_ft[1] * IN),
                          view_height=size_in[1] * scale, dxfattribs={"layer": "G-VPRT"})
    vp.dxf.status = 1
    return lay


def main():
    doc = ezdxf.new("R2018", setup=True, units=ezdxf.units.IN)
    doc.header["$MEASUREMENT"] = 0
    doc.header["$LUNITS"] = 4          # architectural
    doc.header["$INSUNITS"] = 1        # inches
    doc.styles.new("LATO", dxfattribs={"font": "arial.ttf"})
    for name, color, lw, lt in LAYERS:
        doc.layers.add(name, color=color, lineweight=lw, linetype=lt)
    ds = doc.dimstyles.new("ARCH")
    ds.dxf.dimlunit = 4
    ds.dxf.dimtxt = 9
    ds.dxf.dimasz = 0
    ds.dxf.dimtsz = 4
    ds.dxf.dimexe = 4
    ds.dxf.dimexo = 4
    ds.dxf.dimgap = 3
    ds.dxf.dimdec = 0
    ds.dxf.dimtad = 1
    ds.dxf.dimtxsty = "LATO"
    for name, plan, _ in PLANS:
        build_block(doc, name, plan)
    msp = doc.modelspace()

    # plans side by side: the three Casa 02 floors 32 ft apart (one sheet), the Casita 48 ft further (its own sheet)
    plan_x = {}
    for i, (name, plan, title) in enumerate(PLANS):
        ox = i * 32.0 + (16.0 if name == "CS" else 0.0)
        plan_x[name] = ox
        msp.add_blockref(name, (ox * IN, 0), dxfattribs={"layer": "0"})
        room_labels(msp, plan, None, (ox, 0), 9)
        feature_labels(msp, plan, None, (ox, 0), 9)
        dim(msp, (ox, 0), (ox + plan["W"], 0), (ox, -5))
        if plan.get("porch"):      # the porch is on the right, so dimension the depth on the left
            dim(msp, (ox, 0), (ox, plan["D"]), (ox - 4, 0), angle=90)
        else:
            dim(msp, (ox + plan["W"], 0), (ox + plan["W"], plan["D"]), (ox + plan["W"] + 4, 0), angle=90)
        text(msp, (ox + plan["W"] / 2) * IN, -9 * IN, title, 12)

    # sites, to the right of the plans
    site_origin = {}
    x = 300.0           # far enough right that no site sheet's viewport reaches the plans
    for fn in SITES:
        s = fn()
        site_origin[s["id"]] = (x, 0.0)
        draw_site(msp, s, (x, 0.0))
        x += 250.0          # wider than a sheet's viewport, so each sheet shows one site

    # sheets
    sheet(doc, "C-1 Casa 02", "C-1", "CASA 02 PLANS", '1/8" = 1\'-0"', 96, (plan_x["C02-UP"] / 2 + 10, 18))
    sheet(doc, "C-2 Casita", "C-2", "CASITA PLAN", '1/4" = 1\'-0"', 48, (plan_x["CS"] + 12, 14))
    for i, fn in enumerate(SITES):
        s = fn()
        ox, oy = site_origin[s["id"]]
        sheet(doc, f"C-{i + 3} {s['id']}", f"C-{i + 3}", f"SITE {s['id']}", '1/16" = 1\'-0"', 192,
              (ox + s["lot"]["W"] / 2, oy + s["lot"]["L"] / 2 - 8))
    # developed plans: model space below the concept plans, one sheet each at 3/16" = 1'-0"
    for i, sh in enumerate(PL.SHEETS):
        origin = (i * 60.0, -130.0)
        doors, wins = developed(msp, origin, sh)
        cy = 17.4 if sh["chains"].get("back") else 16.2
        lay = sheet(doc, f"{sh['no']} {BLOCK_OF[id(sh['plan'])]}", sh["no"], sh["title"].upper(), '3/16" = 1\'-0"',
                    64, (origin[0] + 10.6, origin[1] + cy), size_in=(8.6, 9.9), phase="DESIGN DEVELOPMENT")
        schedules(lay, sh, doors, wins)
    if "Layout1" in doc.layouts:
        doc.layouts.delete("Layout1")
    doc.saveas(OUT)
    print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB", "blocks:", [p[0] for p in PLANS],
          "layouts:", [l.name for l in doc.layouts if l.name != "Model"])


if __name__ == "__main__":
    main()
