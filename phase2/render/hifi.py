"""Phase 2 high-detail renders for the lookbook, at Casa 01 quality, from the same model as the drawings.

    <bpy venv>/bin/python phase2/render/hifi.py [--views duo_street,duo_dusk] [--res 1600] [--samples 96]
        -> phase2/render/hifi/<view>.png

The massing renders (build.py) show layouts; this scene shows the homes as built, in the chosen direction:
stucco walls with bronze window frames and glass, the white upper floor floating on a bronze band over a
Lueders limestone ashlar base, the cobogó lantern, cedar slat gates, cedar soffits and carport ceiling, black
calçada at the entries, São Tomé limestone pavers, an open oak stair behind cedar slats, furnished rooms seen
through the glass, and a Central Austin garden of live oaks, agave, sotol, feather grass and buffalo grass.
It reuses the Casa 01 kit: materials (scanned textures), plants, furniture models, HDRI skies, camera and
render settings.
"""
import argparse
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import build as B  # noqa: E402  (phase2 massing: model, constants, wall pieces, cobogó panel, Casa 01 kit on the path)
import plants as PL  # noqa: E402  (Casa 01)
import landscape as LS  # noqa: E402  (Casa 01)
import furniture as FU  # noqa: E402  (Casa 01)
from geo import MB, M, new_coll, subtract_rect  # noqa: E402

R, MAT, H, tp = B.R, B.MAT, B.H, B.tp
from model.sites import SITES, footprint, garden_wall  # noqa: E402

OUT = os.path.join(HERE, "hifi")
FF, GF_TOP, UP_FF, UP_TOP, ROOF, ONE = B.FF, B.GF_TOP, B.UP_FF, B.UP_TOP, B.ROOF, B.ONE_STORY_ROOF
BAND = UP_FF - 1.25                      # bottom of the upper floor's bronze band
SITE_OF = {fn().get("id"): fn for fn in SITES}

# camera and light per view (feet; sun = compass azimuth). site: which layout to build.
VIEWS = {
    "duo_street": dict(site="L1-D1", cam=(43.0, -27.0, 5.4), tgt=(23.0, 24.0, 10.8), lens=24, hdri="afternoon",
                       sun=232, strength=1.0, exposure=-0.15, night=False),
    "duo_dusk": dict(site="L1-D1", cam=(43.0, -27.0, 5.4), tgt=(23.0, 24.0, 10.8), lens=24, hdri="dusk", sun=290,
                     strength=0.07, exposure=0.9, night=True),
    "duo_entry": dict(site="L1-D1", cam=(29.8, 1.8, 5.2), tgt=(16.0, 15.0, 8.4), lens=20, hdri="afternoon", sun=210,
                      strength=1.0, exposure=0.15, night=False),
    "duo_garden": dict(site="L1-D1", cam=(43.6, 75.0, 5.3), tgt=(29.0, 54.0, 9.8), lens=18, hdri="golden",
                       sun=300, strength=1.0, exposure=0.35, night=True, night_level=0.3),
    "kitchen": dict(site="L1-D1", cam=(22.6, 52.6, 5.8), tgt=(11.0, 37.5, 5.1), lens=18, hdri="day", sun=200,
                    strength=1.0, exposure=1.9, night=True, night_level=0.12),
    "primary_bath": dict(site="L1-D1", cam=(23.0, 53.0, 16.3), tgt=(23.2, 45.2, 15.0), lens=18, hdri="day", sun=200,
                         strength=1.0, exposure=1.6, night=True, night_level=0.15),
    "side_drive": dict(site="L4-T1", cam=(-5.0, -23.0, 5.4), tgt=(19.0, 23.0, 9.8), lens=24, hdri="afternoon", sun=232,
                       strength=1.0, exposure=-0.1, night=False),
    "upper_hall": dict(site="L1-D1", cam=(16.3, 37.2, 16.7), tgt=(22.4, 24.0, 17.6), lens=16, hdri="day", sun=200,
                       strength=1.0, exposure=1.6, night=True, night_level=0.12),
    "trio_street": dict(site="L2-T2", cam=(45.0, -22.0, 5.4), tgt=(22.0, 24.0, 8.5), lens=24, hdri="day", sun=200,
                        strength=1.0, exposure=-0.05, night=False),
    "trio_aerial": dict(site="L1-T1", cam=(98.0, -42.0, 74.0), tgt=(25.0, 62.0, 4.0), lens=31, hdri="day", sun=215,
                        strength=1.0, exposure=0.0, night=False, two_point=False),
}
FURN = {"counter": (3.0, "oak", "granite"), "island": (3.0, "oak", "granite"), "range": (3.0, "black", "black"),
        "sink": (3.0, "oak", "granite"), "fridge": (6.8, "black", "black"), "table": (2.5, "oak", "oak"),
        "desk": (2.5, "oak", "oak"), "sofa": (2.4, "linen", "linen"), "bed": (1.9, "linen", "linen"),
        "tub": (1.7, "ceramic", "ceramic"), "lav": (2.8, "oak", "ceramic"), "wd": (5.8, "ceramic", "ceramic")}


# ---------------------------------------------------------------- helpers
def wbox(mb, t, a, u, n, q0, q1, d0, d1, z0, z1, mat=0, r=None):
    """A box along a wall of a home: q along the wall (u), d across it (n), in the home's frame; placed by t."""
    pts = [tp(t, a[0] + u[0] * q + n[0] * d, a[1] + u[1] * q + n[1] * d) for q in (q0, q1) for d in (d0, d1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mb.box(min(xs), min(ys), z0, max(xs), max(ys), z1, mat=mat, r=r)


def lb(mb, t, x0, y0, x1, y1, z0, z1, mat=0, mats6=None, r=None):
    pts = [tp(t, x, y) for x in (x0, x1) for y in (y0, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mb.box(min(xs), min(ys), z0, max(xs), max(ys), z1, mat=mat, mats6=mats6, r=r)


def boards(mb, t, rect, z, rng, along="y", bw=5.5 / 12, gap=0.25 / 12, th=0.06, mat=0):
    """Cedar ceiling boards (T&G look) filling rect, in the home's frame, hanging under z."""
    x0, y0, x1, y1 = rect
    if along == "y":
        x = x0
        while x < x1 - 0.05:
            xe = min(x + bw, x1)
            y = y0
            while y < y1 - 0.05:
                ye = min(y + rng.uniform(8, 16), y1)
                lb(mb, t, x, y, xe, ye - 0.01, z - th, z - 0.002, mat=mat, r=rng.random())
                y = ye
            x = xe + gap
    else:
        y = y0
        while y < y1 - 0.05:
            ye = min(y + bw, y1)
            x = x0
            while x < x1 - 0.05:
                xe = min(x + rng.uniform(8, 16), x1)
                lb(mb, t, x, y, xe - 0.01, ye, z - th, z - 0.002, mat=mat, r=rng.random())
                x = xe
            y = ye + gap


def wall_frame(w):
    (ax, ay), (bx, by) = w["a"], w["b"]
    L = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / L, (by - ay) / L)
    return (ax, ay), u, (-u[1], u[0]), L


# ---------------------------------------------------------------- architecture
def openings(plan, t, z0, M_):
    """Bronze frames, mullions and glass for windows and sliders; oak and half-glass exterior doors."""
    for w in plan["walls"]:
        a, u, n, L = wall_frame(w)
        th = w["t"]
        d0 = 0.0 if w["ext"] else -th / 2
        for o in w["openings"]:
            q0, q1 = o["off"], o["off"] + o["w"]
            if o["kind"] == "door":
                if not w["ext"]:
                    continue
                fw, za, zb = 0.12, z0, z0 + B.DOOR_HEAD
                for p0, p1, z_a, z_b in ((q0, q0 + fw, za, zb), (q1 - fw, q1, za, zb), (q0, q1, zb - fw, zb)):
                    wbox(M_["frames"], t, a, u, n, p0, p1, d0 + 0.05, d0 + 0.42, z_a, z_b)
                front = abs(n[1] - 1.0) < 1e-6                       # the front door: solid oak
                if front:
                    wbox(M_["oak"], t, a, u, n, q0 + fw, q1 - fw, d0 + 0.16, d0 + 0.3, za, zb - fw)
                else:                                                 # carport door: oak with a glass upper half
                    wbox(M_["oak"], t, a, u, n, q0 + fw, q1 - fw, d0 + 0.16, d0 + 0.3, za, za + 3.6)
                    wbox(M_["oak"], t, a, u, n, q0 + fw, q1 - fw, d0 + 0.16, d0 + 0.3, zb - fw - 0.35, zb - fw)
                    for p0, p1 in ((q0 + fw, q0 + fw + 0.3), (q1 - fw - 0.3, q1 - fw)):
                        wbox(M_["oak"], t, a, u, n, p0, p1, d0 + 0.16, d0 + 0.3, za + 3.6, zb - fw - 0.35)
                    wbox(M_["glass"], t, a, u, n, q0 + fw + 0.3, q1 - fw - 0.3, d0 + 0.22, d0 + 0.24,
                         za + 3.6, zb - fw - 0.35)
                continue
            slider = o["kind"] == "slider"
            sill = 0.0 if slider else B.SILLS.get(o.get("note", ""), 2.5)
            head = B.DOOR_HEAD if slider else B.WIN_HEAD
            za, zb = z0 + sill, z0 + head
            fw = 0.15
            dd0, dd1 = (d0 + 0.04, d0 + 0.36) if w["ext"] else (d0, d0 + th)
            for p0, p1, z_a, z_b in ((q0, q0 + fw, za, zb), (q1 - fw, q1, za, zb), (q0, q1, za, za + fw),
                                     (q0, q1, zb - fw, zb)):
                wbox(M_["frames"], t, a, u, n, p0, p1, dd0, dd1, z_a, z_b)
            panels = max(1, round(o["w"] / (4.0 if slider else 3.2)))
            pw = (q1 - q0) / panels
            for k in range(panels):
                p0 = q0 + k * pw
                off = (0.06 if k % 2 else -0.05) if slider else 0.0
                if k:
                    wbox(M_["frames"], t, a, u, n, p0 - 0.07, p0 + 0.07, dd0 + 0.04, dd1 - 0.04, za, zb)
                wbox(M_["glass"], t, a, u, n, p0 + 0.04, p0 + pw - 0.04, d0 + 0.18 + off, d0 + 0.2 + off,
                     za + 0.1, zb - 0.1)
                if slider:
                    for z_a, z_b in ((za + fw, za + fw + 0.1), (zb - fw - 0.08, zb - fw)):
                        wbox(M_["frames"], t, a, u, n, p0 + 0.04, p0 + pw - 0.04, d0 + 0.14 + off, d0 + 0.24 + off,
                             z_a, z_b)


def ashlar(L, coll, t, runs, top, piers, pier_top, name, seed, cap=False):
    """Lueders limestone, sawn-face ashlar in three course heights (8, 4 and 12 in), with a mortar bed; cut at the
    openings. Runs from homes.stone_runs; piers (x0, y0, x1, y1) in the home's frame."""
    rng = random.Random(seed)
    st = MB(f"{name} limestone ashlar", [L["limestone"]])
    mo = MB(f"{name} limestone mortar", [L["mortar"]])
    pattern = [0.667, 0.333, 1.0, 0.333, 0.667, 0.667, 1.0, 0.333]
    joint = 0.03

    def courses(z0, z1):
        out, z, i = [], z0, 0
        while z < z1 - 0.05:
            h = min(pattern[i % len(pattern)] if i else 0.667, z1 - z)
            out.append((z, z + h))
            z += h
            i += 1
        return out
    for run in runs:
        a, u, n, Lr = run["a"], run["u"], run["n"], run["L"]
        holes = []
        for h0, h1, o in run["holes"]:
            sill = 0.0 if o["kind"] in ("door", "slider") else B.SILLS.get(o.get("note", ""), 2.5)
            head = B.DOOR_HEAD if o["kind"] in ("door", "slider") else B.WIN_HEAD
            holes.append((h0, h1, FF + sill, FF + head))
        rect = (0.0, Lr, 0.0, top)
        pieces = [rect]
        for hx0, hx1, hz0, hz1 in holes:
            pieces = [r for p in pieces for r in subtract_rect(p, (hx0, hx1, hz0, hz1))]
        for (q0, q1, z0, z1) in pieces:
            wbox(mo, t, a, u, n, q0, q1, -0.26, -0.02, z0, z1)
        for cz0, cz1 in courses(0.0, top):
            q = -rng.uniform(0, 1.5)
            while q < Lr:
                ln = rng.uniform(1.4, 3.6) if cz1 - cz0 < 0.9 else rng.uniform(1.8, 4.2)
                s0, s1 = max(q, 0.0), min(q + ln, Lr)
                q += ln
                if s1 - s0 < 0.25:
                    continue
                r = rng.random()
                parts = [(s0, s1, cz0, cz1)]
                for hx0, hx1, hz0, hz1 in holes:
                    parts = [p_ for p in parts for p_ in subtract_rect(p, (hx0 - 0.02, hx1 + 0.02, hz0, hz1))]
                for (p0, p1, z0, z1) in parts:
                    if p1 - p0 < 0.05 or z1 - z0 < 0.05:
                        continue
                    proud = rng.uniform(-0.012, 0.012)
                    wbox(st, t, a, u, n, p0 + joint / 2, p1 - joint / 2, -0.3 - proud, -0.03, z0 + joint / 2,
                         z1 - joint / 2, r=r)
    for (x0, y0, x1, y1) in piers:
        lb(mo, t, x0 + 0.04, y0 + 0.04, x1 - 0.04, y1 - 0.04, 0.0, pier_top)
        along_x = (x1 - x0) >= (y1 - y0)
        Lp = max(x1 - x0, y1 - y0)
        if cap:                                              # thin limestone cap, slightly proud
            lb(st, t, x0 - 0.06, y0 - 0.06, x1 + 0.06, y1 + 0.06, pier_top, pier_top + 0.15, r=rng.random())
        for i, (cz0, cz1) in enumerate(courses(0.0, pier_top)):
            r = rng.random()
            if Lp > 2.2:                                     # a short wall: stones laid along its length
                q = -rng.uniform(0.0, 1.2)
                while q < Lp:
                    ln = rng.uniform(1.3, 3.2) if cz1 - cz0 < 0.9 else rng.uniform(1.8, 3.8)
                    s0, s1 = max(q, 0.0), min(q + ln, Lp)
                    q += ln
                    if s1 - s0 < 0.25:
                        continue
                    if along_x:
                        lb(st, t, x0 + s0 + joint / 2, y0, x0 + s1 - joint / 2, y1, cz0 + joint / 2, cz1 - joint / 2,
                           r=rng.random())
                    else:
                        lb(st, t, x0, y0 + s0 + joint / 2, x1, y0 + s1 - joint / 2, cz0 + joint / 2, cz1 - joint / 2,
                           r=rng.random())
                continue
            if i % 2:
                lb(st, t, x0, y0, x1, y1 - (y1 - y0) / 2 - joint / 2, cz0 + joint / 2, cz1 - joint / 2, r=r)
                lb(st, t, x0, y0 + (y1 - y0) / 2 + joint / 2, x1, y1, cz0 + joint / 2, cz1 - joint / 2, r=r * 0.7)
            else:
                lb(st, t, x0, y0, x1 - (x1 - x0) / 2 - joint / 2, y1, cz0 + joint / 2, cz1 - joint / 2, r=r)
                lb(st, t, x0 + (x1 - x0) / 2 + joint / 2, y0, x1, y1, cz0 + joint / 2, cz1 - joint / 2, r=r * 0.7)
    st.build(coll, bevel=0.003)
    mo.build(coll)


def calcada(L, coll, rects, z_of, name):
    """Black calçada portuguesa framed by a light concrete band (Casa 01's entry mosaic). rects in lot ft."""
    mo = MB(f"{name} calcada", [L["calcada"], L["concrete"]])
    for r in rects:
        x0, y0, x1, y1 = r
        z = z_of(r)
        b = 0.3 if min(x1 - x0, y1 - y0) > 1.5 else 0.1
        mo.box(x0, y0, z - 0.14, x1, y1, z - 0.002, mats6=[1, 1, 1, 1, 1, 1])
        mo.box(x0 + b, y0 + b, z - 0.12, x1 - b, y1 - b, z + 0.004, mats6=[1, 0, 1, 1, 1, 1])
    mo.build(coll)


def cedar_gate_y(L, coll, t, y0, y1, x, z0, z1, name):
    """Cedar slat gate along y (a side gate, face toward -x)."""
    g = MB(f"{name} cedar gate", [L["cedar_z"], L["bronze"]])
    lb(g, t, x + 0.1, y0, x + 0.22, y1, z0, z0 + 0.12, mat=1)
    lb(g, t, x + 0.1, y0, x + 0.22, y1, z1 - 0.12, z1, mat=1)
    for yy in (y0, y1 - 0.12):
        lb(g, t, x + 0.05, yy, x + 0.27, yy + 0.12, z0, z1, mat=1)
    y = y0 + 0.16
    while y + 0.125 < y1 - 0.14:
        lb(g, t, x, y, x + 0.12, y + 0.125, z0 + 0.05, z1 - 0.05, mat=0, r=random.random())
        y += 0.29
    g.build(coll, bevel=0.002)


def cedar_gate(L, coll, t, x0, x1, y, z0, z1, name):
    """Cedar slat gate on a dark bronze frame, along x in the home's frame (face toward -y)."""
    g = MB(f"{name} cedar gate", [L["cedar_z"], L["bronze"]])
    lb(g, t, x0, y + 0.1, x1, y + 0.22, z0, z0 + 0.12, mat=1)
    lb(g, t, x0, y + 0.1, x1, y + 0.22, z1 - 0.12, z1, mat=1)
    for xx in (x0, x1 - 0.12):
        lb(g, t, xx, y + 0.05, xx + 0.12, y + 0.27, z0, z1, mat=1)
    x = x0 + 0.16
    while x + 0.125 < x1 - 0.14:
        lb(g, t, x, y, x + 0.125, y + 0.12, z0 + 0.05, z1 - 0.05, mat=0, r=random.random())
        x += 0.29
    g.build(coll, bevel=0.002)


def stair(L, coll, plan, t, name):
    """Open oak treads rising toward the front, cedar slats on the hall side and a slat guard upstairs."""
    st = plan.get("stair")
    if not st:
        return
    x0, y0, x1, y1 = st["rect"]
    n = st.get("risers", 17) - 1
    rise = (UP_FF - FF) / st.get("risers", 17)
    run = (y1 - y0) / n
    mb = MB(f"{name} stair", [L["oak"], L["cedar_z"], L["bronze"]])
    for k in range(n):
        ya, yb = y1 - (k + 1) * run - 0.06, y1 - k * run
        z = FF + (k + 1) * rise
        lb(mb, t, x0 + 0.2, ya, x1 - 0.5, yb, z - 0.15, z, mat=0, r=random.random())
    lb(mb, t, x1 - 0.5, y0, x1 - 0.45, y1, FF, UP_FF, mat=2)           # wall stringer
    for (sx, sy0), (_sx, sy1) in plan.get("slats", []):
        y = min(sy0, sy1)
        while y + 0.125 < max(sy0, sy1):
            lb(mb, t, sx - 0.06, y, sx + 0.06, y + 0.125, FF, BAND, mat=1, r=random.random())
            y += 0.29
    for (sx, sy0), (_sx, sy1) in H.CASA02_UPPER.get("slats", []):        # guard upstairs
        y = min(sy0, sy1)
        while y + 0.125 < max(sy0, sy1):
            lb(mb, t, sx - 0.06, y, sx + 0.06, y + 0.125, UP_FF, UP_FF + 3.5, mat=1, r=random.random())
            y += 0.29
    mb.build(coll, bevel=0.002)


KITCHEN_KINDS = ("counter", "island", "range", "sink", "fridge")
DETAIL_KITCHEN = True


def kitchen(L, coll, plan, t, name):
    """The Casa 02 kitchen as specified: rift oak slab cabinets with reveals and a toe kick, honed black granite,
    green zellige backsplash to an oak shelf, plaster hood over the induction range, undermount sink with a brass
    bridge faucet, panel-ready oak fridge, and the granite island with its oak table."""
    fx = {f["kind"]: f for f in plan.get("fixtures", []) if "rect" in f and f["rect"][1] >= 20.0}   # kitchen zone
    if "counter" not in fx:
        return
    mb = MB(f"{name} kitchen", [L["oak"], L["black"], L["granite"], L["tile"], L["paint"], L["brass"], L["oak_y"]])
    z = FF
    cx0, cy0, cx1, cy1 = fx["counter"]["rect"]
    fr = fx.get("fridge", {}).get("rect")
    x_left = fr[2] if fr else cx0
    # base run: toe kick, boxes, reveals, top
    lb(mb, t, x_left, cy0, cx1, cy1 - 0.25, z, z + 0.33, mat=1)
    lb(mb, t, x_left, cy0, cx1, cy1, z + 0.33, z + 2.9, mat=0, r=0.3)
    x = x_left + 1.5
    while x < cx1 - 0.3:
        lb(mb, t, x - 0.01, cy1, x + 0.01, cy1 + 0.005, z + 0.38, z + 2.86, mat=1)
        x += 1.5
    lb(mb, t, x_left, cy1, cx1, cy1 + 0.005, z + 2.33, z + 2.35, mat=1)
    lb(mb, t, x_left, cy0, cx1 + 0.02, cy1 + 0.06, z + 2.9, z + 3.0, mat=2)
    if "range" in fx:                                           # induction top, black front, plaster hood
        rx0, ry0, rx1, ry1 = fx["range"]["rect"]
        lb(mb, t, rx0 + 0.1, ry0 + 0.25, rx1 - 0.1, ry1 - 0.2, z + 3.0, z + 3.012, mat=1)
        lb(mb, t, rx0, cy1, rx1, cy1 + 0.01, z + 0.4, z + 2.85, mat=1)
        lb(mb, t, rx0 - 0.1, cy0, rx1 + 0.1, cy0 + 1.7, z + 6.3, BAND, mat=4)
    if "sink" in fx:
        sx0, sy0, sx1, sy1 = fx["sink"]["rect"]
        lb(mb, t, sx0, sy0, sx1, sy1, z + 2.97, z + 3.004, mat=1)
        mx = (sx0 + sx1) / 2
        lb(mb, t, mx - 0.05, cy0 + 0.15, mx + 0.05, cy0 + 0.25, z + 3.0, z + 4.15, mat=5)
        lb(mb, t, mx - 0.04, cy0 + 0.15, mx + 0.04, cy0 + 0.95, z + 4.05, z + 4.13, mat=5)
    # green zellige backsplash to the oak shelf, the shelf
    lb(mb, t, x_left, cy0 - 0.05, cx1, cy0, z + 3.0, z + 5.3, mat=3)
    lb(mb, t, x_left, cy0, cx1, cy0 + 0.9, z + 5.3, z + 5.45, mat=6)
    if fr:                                                      # panel-ready fridge in oak
        fx0, fy0, fx1, fy1 = fr
        lb(mb, t, fx0, fy0, fx1, fy1, z, z + 7.6, mat=0, r=0.6)
        lb(mb, t, (fx0 + fx1) / 2 - 0.01, fy1, (fx0 + fx1) / 2 + 0.01, fy1 + 0.005, z + 0.2, z + 7.4, mat=1)
        for xx in ((fx0 + fx1) / 2 - 0.25, (fx0 + fx1) / 2 + 0.2):
            lb(mb, t, xx, fy1 + 0.005, xx + 0.05, fy1 + 0.1, z + 3.2, z + 5.2, mat=5)
    if "island" in fx:                                          # granite island at counter height
        ix0, iy0, ix1, iy1 = fx["island"]["rect"]
        lb(mb, t, ix0 + 0.3, iy0 + 0.25, ix1 - 0.3, iy1, z, z + 0.33, mat=1)
        lb(mb, t, ix0 + 0.3, iy0, ix1 - 0.3, iy1, z + 0.33, z + 2.9, mat=0, r=0.45)
        x = ix0 + 1.8
        while x < ix1 - 0.6:
            lb(mb, t, x - 0.01, iy0 - 0.005, x + 0.01, iy0, z + 0.38, z + 2.86, mat=1)
            x += 1.5
        lb(mb, t, ix0, iy0 - 0.06, ix1, iy1, z + 2.9, z + 3.0, mat=2)
    if "island_table" in fx:                                    # the oak table built onto it
        tx0, ty0, tx1, ty1 = fx["island_table"]["rect"]
        lb(mb, t, tx0, ty0, tx1, ty1, z + 2.36, z + 2.5, mat=6)
        for xx in (tx0 + 0.2, tx1 - 0.35):
            lb(mb, t, xx, ty1 - 0.35, xx + 0.15, ty1 - 0.2, z, z + 2.36, mat=0)
    mb.build(coll, bevel=0.003)


def primary_bath(L, coll, t, name):
    """The primary bath upstairs: a walk-in shower under the skylight in green zellige to the ceiling, glass panel,
    brass rain head; floating oak vanity with a limestone top and a vessel sink; round mirror and sconces; wall wc."""
    import bath as BA                                           # Casa 01 bath helpers (cylinders, globes)
    z0, zc = UP_FF, UP_TOP
    mb = MB(f"{name} primary bath", [L["zellige"], L["shower_mosaic"], L["floor"], L["glass"], L["brass"], L["oak"],
                                     L["limestone"], L["ceramic"]])
    lb(mb, t, 14.2, 30.2, 19.5, 38.5, z0, z0 + 0.02, mat=2)                   # honed concrete floor
    lb(mb, t, 16.3, 35.4, 19.5, 38.5, z0, z0 + 0.03, mat=1)                   # shower mosaic
    win = (15.5, 18.5, z0 + 5.5, z0 + 8.5)                                    # back wall window in the shower
    for (a0, a1, b0, b1) in subtract_rect((16.3, 19.5, z0, zc), win):
        lb(mb, t, a0, 38.45, a1, 38.5, b0, b1, mat=0)
    lb(mb, t, 19.45, 35.4, 19.5, 38.5, z0, zc, mat=0)                         # east wall of the shower
    lb(mb, t, 16.28, 35.6, 16.32, 38.45, z0 + 0.03, z0 + 7.6, mat=3)          # glass panel
    lb(mb, t, 16.26, 35.6, 16.34, 38.45, z0 + 7.6, z0 + 7.66, mat=4)
    lb(mb, t, 18.7, 36.95, 19.45, 37.05, z0 + 7.0, z0 + 7.08, mat=4)          # rain head arm
    lb(mb, t, 19.4, 36.7, 19.45, 37.3, z0 + 3.9, z0 + 4.3, mat=4)             # valve trim
    lb(mb, t, 17.05, 30.45, 19.4, 32.1, z0 + 1.15, z0 + 2.55, mat=5)          # floating oak vanity
    lb(mb, t, 17.0, 30.2, 19.45, 32.2, z0 + 2.55, z0 + 2.7, mat=6)            # limestone top
    lb(mb, t, 18.2, 30.2, 18.28, 30.85, z0 + 3.4, z0 + 3.47, mat=4)           # wall faucet
    lb(mb, t, 14.75, 30.2, 16.05, 31.95, z0 + 1.05, z0 + 1.42, mat=7)         # wall-hung wc
    lb(mb, t, 15.0, 30.2, 15.8, 31.65, z0 + 0.95, z0 + 1.05, mat=7)
    mb.build(coll, bevel=0.003)
    hx, hy = tp(t, 18.7, 37.0)
    BA.cyl(f"{name} rain head", coll, L["brass"], hx, hy, z0 + 6.95, z0 + 7.0, 0.42)
    sx, sy = tp(t, 18.2, 31.3)
    BA.cyl(f"{name} vessel sink", coll, L["ceramic"], sx, sy, z0 + 2.7, z0 + 3.15, 0.62, bowl=0.38)
    mx, my = tp(t, 18.2, 30.2)
    for nmx, mat, rr, off in (("rim", L["brass"], 1.12, 0.0), ("mirror", L["mirror"], 1.05, 0.02)):
        ob = BA.cyl(f"{name} mirror {nmx}", coll, mat, mx, my, 0, 0.05, rr, axis="Y", segs=64)
        ob.location = (mx * M, (my + ((0.05 + off) if t["rot"] == 0 else -(0.05 + off))) * M,   # the glass sits proud of the rim
                       (z0 + 5.3) * M)
    for sxx in (16.75, 19.55 - 0.1):
        gx, gy = tp(t, sxx, 30.55)
        BA.globe(f"{name} sconce", coll, L["lamp"], gx, gy, z0 + 5.4)


def furnish(L, coll, plan, t, z, name, protos):
    mb = MB(f"{name} furniture", [L["oak"], L["granite"], L["linen"], L["ceramic"], L["black"]])
    idx = {"oak": 0, "granite": 1, "linen": 2, "ceramic": 3, "black": 4}
    for f in plan.get("fixtures", []):
        k = f["kind"]
        if k == "chair" and "chair" in protos:
            x0, y0, x1, y1 = f["rect"]
            X, Y = tp(t, (x0 + x1) / 2, (y0 + y1) / 2)
            FU.place(protos["chair"], X, Y, z, math.radians(f.get("rot", 0) + (t["rot"] if t else 0)), coll)
            continue
        if k not in FURN or "rect" not in f or (k in KITCHEN_KINDS and DETAIL_KITCHEN and f["rect"][1] >= 20.0):
            continue
        h, body, top = FURN[k]
        x0, y0, x1, y1 = f["rect"]
        if k == "table":
            lb(mb, t, x0, y0, x1, y1, z + h - 0.15, z + h, mat=0)
            for cx, cy in ((x0 + 0.3, y0 + 0.3), (x1 - 0.3, y0 + 0.3), (x0 + 0.3, y1 - 0.3), (x1 - 0.3, y1 - 0.3)):
                lb(mb, t, cx - 0.08, cy - 0.08, cx + 0.08, cy + 0.08, z, z + h - 0.15, mat=0)
            if "chair" in protos:
                for i, (cx, cy, rot) in enumerate(((x0 + 1.5, y0 - 0.7, 0), (x1 - 1.5, y0 - 0.7, 0),
                                                   (x0 + 1.5, y1 + 0.7, 180), (x1 - 1.5, y1 + 0.7, 180))):
                    X, Y = tp(t, cx, cy)
                    FU.place(protos["chair"], X, Y, z, math.radians(rot + (t["rot"] if t else 0)), coll)
            continue
        lb(mb, t, x0, y0, x1, y1, z, z + h - 0.1, mat=idx[body])
        lb(mb, t, x0 - 0.04, y0 - 0.04, x1 + 0.04, y1 + 0.04, z + h - 0.1, z + h, mat=idx[top])
    mb.build(coll, bevel=0.004)
    for f in plan.get("fixtures", []):                      # pendants over the island
        if f["kind"] == "island" and "pendant" in protos:
            x0, y0, x1, y1 = f["rect"]
            for cx in (x0 + 2.0, x1 - 2.0):
                X, Y = tp(t, cx, (y0 + y1) / 2)
                FU.place(protos["pendant"], X, Y, BAND - 3.2, 0, coll)


def home(L, coll, h, protos, lights):
    plan, t = h["plan"], h["t"]
    casa = not H.is_casita(plan)
    W, D = plan["W"], plan["D"]
    nm = f"{h['id']}"
    rng = random.Random(hash(nm) % 1000)
    walls = MB(f"{nm} walls", [L["stucco"], L["paint"]])
    floors = [(FF, GF_TOP if casa else ONE[0], plan)] + ([(UP_FF, UP_TOP, H.CASA02_UPPER)] if casa else [])
    fx0, fy0, fx1, fy1 = footprint(t)
    for z0, z1, pl in floors:
        for x0, y0, x1, y1, za, zb, kind in B.wall_pieces(pl, t, z0, z1, ext_only=False):
            if kind in ("glass", "door"):
                continue
            if kind == "inner":                     # stop partitions at the inner face of the outer walls
                x0, x1 = max(x0, fx0 + 0.5), min(x1, fx1 - 0.5)
                y0, y1 = max(y0, fy0 + 0.5), min(y1, fy1 - 0.5)
                if x1 - x0 < 0.05 or y1 - y0 < 0.05:
                    continue
            walls.box(x0, y0, za, x1, y1, zb, mat=0 if kind == "wall" else 1)
    walls.build(coll, bevel=0.004)
    M_ = dict(frames=MB(f"{nm} window frames", [L["bronze"]]), glass=MB(f"{nm} glass", [L["glass"]]),
              oak=MB(f"{nm} doors", [L["oak_door"]]))
    for z0, _z1, pl in floors:
        openings(pl, t, z0, M_)
    for mb in M_.values():
        mb.build(coll, bevel=0.002)
    # slabs, band, roof, soffits
    sl = MB(f"{nm} slabs", [L["floor"], L["concrete"], L["oak"], L["paint"], L["bronze"], L["roof"], L["cedar_y"]])
    ext = [tp(t, *w["a"]) for w in plan["walls"] if w["ext"]]
    sl.prism(ext, 0.0, FF, top=0, side=1, bottom=1)
    o = 1.0
    if casa:
        void = H.CASA02_UPPER["void"]
        for (a0, a1, b0, b1) in subtract_rect((0.0, W, 0.0, D), (void[0], void[2], void[1], void[3])):
            lb(sl, t, a0, b0, a1, b1, BAND, UP_FF, mats6=[3, 2, 4, 4, 4, 4])
        xr = W if plan is H.CASA02_GF_CARPORT else W + o        # a pair's roofs meet at the shared wall
        roof_with_skylights(sl, t, (-o, -o, xr, D + o), ROOF, H.CASA02_UPPER.get("skylights", []), nm, L, coll)
    else:
        roof_with_skylights(sl, t, (-o, -o, W + o, D + o), ONE, plan.get("skylights", []), nm, L, coll)
        pr = plan.get("porch")
        if pr:
            x0, y0, x1, y1 = pr["roof"]
            lb(sl, t, W + o, y0, x1, y1, ONE[0], ONE[1], mats6=[6, 5, 4, 4, 4, 4])
    sl.build(coll, bevel=0.003)
    if casa:                                                   # rooftop solar, 3 ft clear of edges and skylights
        pv = MB(f"{nm} solar", [SOLAR(), L["bronze"]])
        sks = [sk["rect"] for sk in H.CASA02_UPPER.get("skylights", [])]
        y0 = 3.0
        while y0 + 5.6 <= D - 3.0:
            x0 = 2.6
            while x0 + 4.5 <= W - 2.6:
                box = (x0 - 1.0, y0 - 1.0, x0 + 5.5, y0 + 6.6)
                if not any(box[0] < k[2] and k[0] < box[2] and box[1] < k[3] and k[1] < box[3] for k in sks):
                    lb(pv, t, x0, y0, x0 + 4.5, y0 + 5.6, ROOF[1] + 0.35, ROOF[1] + 0.45, mats6=[1, 0, 1, 1, 1, 1])
                    lb(pv, t, x0 + 0.4, y0 + 0.4, x0 + 0.6, y0 + 5.2, ROOF[1], ROOF[1] + 0.35, mat=1)
                    lb(pv, t, x0 + 3.9, y0 + 0.4, x0 + 4.1, y0 + 5.2, ROOF[1], ROOF[1] + 0.35, mat=1)
                x0 += 4.7
            y0 += 5.8
        pv.build(coll, bevel=0.002)
    sh = plan.get("sunshade")
    if sh:                                                     # cedar slat sunshade over the back slider
        x0, y0, x1, y1 = sh["rect"]
        z = sh["z"]
        ss = MB(f"{nm} sunshade", [L["cedar_x"], L["bronze"]])
        for xa in (x0, x1 - 0.2):
            lb(ss, t, xa, y0, xa + 0.2, y1, z, z + 0.45, mat=1)
        lb(ss, t, x0, y1 - 0.2, x1, y1, z, z + 0.45, mat=1)
        yy = y0 + 0.35
        while yy < y1 - 0.25:
            lb(ss, t, x0 + 0.2, yy, x1 - 0.2, yy + 0.1, z + 0.05, z + 0.42, mat=0, r=rng.random())
            yy += 0.32
        ss.build(coll, bevel=0.002)
    cb = MB(f"{nm} cedar ceilings", [L["cedar_y"]])
    for r in plan["rooms"]:
        if r.get("outdoor"):                                   # carport ceiling
            boards(cb, t, r["rect"], BAND, rng)
    if plan.get("porch"):
        x0, y0, x1, y1 = plan["porch"]["roof"]
        boards(cb, t, (W + 0.02, y0, x1, y1), ONE[0], rng)
    cb.build(coll, bevel=0.001)
    # columns, porch posts, gate
    det = MB(f"{nm} steel", [L["bronze"]])
    for cx, cy in plan.get("columns", []):
        lb(det, t, cx - 0.17, cy - 0.17, cx + 0.17, cy + 0.17, 0.15, BAND)
    if plan.get("porch"):
        for cx, cy in plan["porch"]["posts"]:
            lb(det, t, cx - 0.17, cy - 0.17, cx + 0.17, cy + 0.17, 0.0, ONE[0])
    det.build(coll, bevel=0.002)
    if plan.get("gate") and h.get("gate", True):
        (gx0, gy0), (gx1, gy1) = plan["gate"]
        if abs(gx1 - gx0) < 1e-6:
            cedar_gate_y(L, coll, t, gy0 + 0.05, gy1 - 0.05, gx0 - 0.05, 0.2, 8.4, nm)
        else:
            cedar_gate(L, coll, t, gx0 + 0.05, gx1 - 0.05, gy0 - 0.05, 0.2, 8.4, nm)
    # the staples: stone, cobogó, calçada; and the carport slab
    if plan.get("stone"):
        ashlar(L, coll, t, H.stone_runs(plan), GF_TOP, plan["stone"].get("piers", []), BAND, nm, len(nm) * 7)
    lan = plan.get("lantern")
    if lan and t["rot"] in (0, 180):
        (xa, ya), (xb, yb) = tp(t, lan["x"][0], lan["y"][0]), tp(t, lan["x"][1], lan["y"][1])
        holes = []
        if lan.get("opening"):
            pa, pb = tp(t, lan["opening"][0], 0.0)[0], tp(t, lan["opening"][1], 0.0)[0]
            holes.append((min(pa, pb), max(pa, pb), FF - 0.1, FF + 8.0))
        z0 = BAND if lan.get("upper_only") else FF
        B.cobogo_panel(L, f"{nm} cobogo", min(xa, xb), max(xa, xb), min(ya, yb), z0, ROOF[0], holes)
        cap = MB(f"{nm} cobogo frame", [L["bronze"]])
        lb(cap, t, lan["x"][0], lan["y"][0] - 0.03, lan["x"][1], lan["y"][1] + 0.03, z0 - 0.12, z0)
        cap.build(coll)
    slab = MB(f"{nm} carport slab", [L["concrete"]])
    for r in plan["rooms"]:
        if r.get("outdoor"):
            lb(slab, t, *r["rect"], -0.3, 0.15)
    slab.build(coll, bevel=0.004)
    rugs = []
    for r in plan.get("calcada", []):
        pts = [tp(t, x, y) for x in (r[0], r[2]) for y in (r[1], r[3])]
        g = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
        rugs.append((g, r[3] <= 0.01))
    if rugs:
        step = MB(f"{nm} stoop", [L["concrete"]])
        for g, at_door in rugs:
            if at_door:
                step.box(g[0], g[1], -0.2, g[2], g[3], FF - 0.15)
        step.build(coll, bevel=0.003)
        calcada(L, coll, [g for g, _ in rugs], lambda r: FF if any(r == g and d for g, d in rugs) else 0.17, nm)
    if casa:
        stair(L, coll, plan, t, nm)
        furnish(L, coll, plan, t, FF, f"{nm} GF", PROTOS)
        furnish(L, coll, H.CASA02_UPPER, t, UP_FF, f"{nm} UP", PROTOS)
        kitchen(L, coll, plan, t, nm)
        if t["rot"] == 0 and not t["mirror"]:                  # one detailed bath (A), where the camera goes
            primary_bath(L, coll, t, nm)
    else:
        furnish(L, coll, plan, t, FF, f"{nm} CS", PROTOS)
    # night lights: warm rooms, the lantern, soffits
    for r in plan["rooms"] + (H.CASA02_UPPER["rooms"] if casa else []):
        up = r in H.CASA02_UPPER["rooms"]
        x0, y0, x1, y1 = r["rect"]
        z = (UP_TOP - 1.2) if up else ((BAND - 1.0) if casa else ONE[0] - 1.0)
        X, Y = tp(t, (x0 + x1) / 2, (y0 + y1) / 2)
        a = (x1 - x0) * (y1 - y0)
        lights.append(("point", X, Y, z, min(140, 8 + a * 0.45) if not r.get("outdoor") else 30))
    if lan:
        for q in (12.0, 15.5, 19.0):                         # wash the cobogó from the gap behind it
            for z in (2.0, 9.0, 15.0):
                X, Y = tp(t, q, -0.45)
                lights.append(("point", X, Y, z, 14))
        for z in (FF + 7.0, UP_FF + 6.5):
            X, Y = tp(t, 16.0, 2.8)
            lights.append(("point", X, Y, z, 70))
    if plan.get("porch"):
        for cy in (6.0, 16.0):
            X, Y = tp(t, W + 4.0, cy)
            lights.append(("spot", X, Y, ONE[0] - 0.1, 30))


PROTOS = {}
_SOLAR = {}


def roof_with_skylights(sl, t, rect, zz, skylights, nm, L, coll):
    """The roof slab, cut for skylights: each gets a white light well through the slab, a 6 in curb and glass."""
    x0, y0, x1, y1 = rect
    pieces = [(x0, x1, y0, y1)]
    for sk in skylights:
        a0, b0, a1, b1 = sk["rect"]
        pieces = [p for q in pieces for p in subtract_rect(q, (a0, a1, b0, b1))]
    for (a0, a1, b0, b1) in pieces:
        lb(sl, t, a0, b0, a1, b1, zz[0], zz[1], mats6=[6, 5, 4, 4, 4, 4])
    if not skylights:
        return
    cu = MB(f"{nm} skylights", [L["paint"], L["roof"], L["glass"], L["bronze"]])
    for sk in skylights:
        a0, b0, a1, b1 = sk["rect"]
        w = 0.06
        for (p0, q0, p1, q1) in ((a0, b0, a1, b0 + w), (a0, b1 - w, a1, b1), (a0, b0, a0 + w, b1), (a1 - w, b0, a1, b1)):
            lb(cu, t, p0, q0, p1, q1, zz[0] - 0.01, zz[1], mat=0)                           # well lining
        c = 0.3
        for (p0, q0, p1, q1) in ((a0 - c, b0 - c, a1 + c, b0), (a0 - c, b1, a1 + c, b1 + c), (a0 - c, b0, a0, b1),
                                 (a1, b0, a1 + c, b1)):
            lb(cu, t, p0, q0, p1, q1, zz[1], zz[1] + 0.5, mat=1)                            # curb
        lb(cu, t, a0 - c, b0 - c, a1 + c, b1 + c, zz[1] + 0.5, zz[1] + 0.56, mat=2)         # glass
        lb(cu, t, a0 - c - 0.04, b0 - c - 0.04, a1 + c + 0.04, b0 - c + 0.08, zz[1] + 0.5, zz[1] + 0.6, mat=3)
        lb(cu, t, a0 - c - 0.04, b1 + c - 0.08, a1 + c + 0.04, b1 + c + 0.04, zz[1] + 0.5, zz[1] + 0.6, mat=3)
    cu.build(coll, bevel=0.002)


def SOLAR():
    """Solar panel glass: near-black blue, glossy, with a faint cell grid."""
    if "m" in _SOLAR:
        return _SOLAR["m"]
    m = bpy.data.materials.new("Solar panel")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 6.0
    br.inputs["Mortar Size"].default_value = 0.015
    br.inputs["Color1"].default_value = (0.012, 0.016, 0.03, 1)
    br.inputs["Color2"].default_value = (0.016, 0.02, 0.038, 1)
    br.inputs["Mortar"].default_value = (0.22, 0.24, 0.27, 1)
    br.offset = 0.0
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.12
    _SOLAR["m"] = m
    return m


# ---------------------------------------------------------------- site
def site(L, coll, s, rng):
    W, Lo = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    g = MB("ground", [L["lawn_soil"], L["asphalt"], L["sidewalk"], L["turf"], L["concrete"], L["pavers"], L["dg"],
                      L["mulch"]])
    g.box(-300, -300, -0.4, W + 300, Lo + 300, -0.02, mat=0)
    g.box(-300, -40, -0.75, W + 300, -12.5, -0.45, mat=1)                    # street
    g.box(-300, -12.5, -0.75, W + 300, -12.0, 0.0, mat=4)                    # curb
    g.box(-300, -6.0, -0.2, W + 300, -1.0, 0.04, mat=2)                      # sidewalk
    if lot.get("alley"):
        g.box(-300, Lo + 1, -0.5, W + 300, Lo + 16, -0.3, mat=1)
    if lot.get("corner"):
        g.box(W + 12.5, -300, -0.75, W + 40, Lo + 300, -0.45, mat=1)
        g.box(W + 6, -6, -0.2, W + 11, Lo + 300, 0.04, mat=2)
    g.box(0, 0, -0.1, W, 15, 0.0, mat=6)                                     # front yard: decomposed granite
    for p in s["patios"]:
        g.box(p[0], p[1], -0.1, p[2], p[3], 0.0, mat=3)
    for k, r in s["pave"]:
        if k in ("Terrace", "Walk"):
            x0, y0, x1, y1 = r
            # São Tomé limestone pavers, 24 x 36, with sand joints
            yy = y0
            while yy < y1 - 0.05:
                ye = min(yy + 2.0, y1)
                xx = x0 + (0.0 if int(yy) % 2 == 0 else -1.5)
                while xx < x1 - 0.05:
                    xe = min(xx + 3.0, x1)
                    xs = max(xx, x0)
                    if xe - xs > 0.2:
                        g.box(xs + 0.02, yy + 0.02, -0.05, xe - 0.02, ye - 0.02, 0.1, mat=5, r=rng.random())
                    xx = xe
                yy = ye
        else:
            g.box(*r[:2], -0.05, *r[2:], 0.08, mat=4)
            if k == "Apron" and r[1] <= 0.5:                                   # curb cut across the parkway
                g.box(r[0], -12.0, -0.3, r[2], -0.02, 0.06, mat=4)
    for pts in s.get("paths", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 2.2))
            for i in range(n):
                f = (i + 0.5) / n
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                g.box(x - 0.85, y - 0.55, -0.05, x + 0.85, y + 0.55, 0.1, mat=5, r=rng.random())
    g.build(coll, bevel=0.002)
    # fences: cedar boards; pátio walls: stucco with a bronze cap
    f = MB("Cedar fences", [L["fence"], L["black"]])
    bh, gap = 5.5 / 12, 0.6 / 12
    for pts in s.get("fence", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            horiz = abs(y0 - y1) < 1e-6
            z = 0.15
            while z + bh < 6.0:
                if horiz:
                    f.box(min(x0, x1), y0 - 0.06, z, max(x0, x1), y0 + 0.06, z + bh, r=rng.random())
                else:
                    f.box(x0 - 0.06, min(y0, y1), z, x0 + 0.06, max(y0, y1), z + bh, r=rng.random())
                z += bh + gap
            Ln = math.hypot(x1 - x0, y1 - y0)
            for k in range(int(Ln / 8) + 1):
                px, py = x0 + (x1 - x0) * k * 8 / Ln, y0 + (y1 - y0) * k * 8 / Ln
                f.box(px - 0.15, py - 0.15, 0, px + 0.15, py + 0.15, 6.1, mat=1)
    f.build(coll, bevel=0.002)
    pw = MB("Pátio walls", [L["stucco"], L["bronze"]])
    for pts in s.get("walls", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            pw.box(min(x0, x1) - 0.25, min(y0, y1) - 0.25, 0.0, max(x0, x1) + 0.25, max(y0, y1) + 0.25, 6.0)
            pw.box(min(x0, x1) - 0.3, min(y0, y1) - 0.3, 6.0, max(x0, x1) + 0.3, max(y0, y1) + 0.3, 6.12, mat=1)
    pw.build(coll, bevel=0.003)
    gw = garden_wall(s)
    if gw:                                                   # the Casita's garden wall
        y = gw["y"]
        runs = []
        piers = [(p0, y - 0.4, p1, y + 0.4) for p0, p1 in gw["piers"]]
        three = bool(gw.get("posts"))                       # open, filtered, solid, all 8 ft
        ashlar(L, coll, None, runs, 0.0, piers, 7.85 if three else 8.5, "garden wall", 5, cap=three)
        c0, c1 = gw["cobogo"]
        B.cobogo_panel(L, "Garden cobogo", c0, c1, y - 0.165, 0.0 if three else 0.4, 8.0 if three else 8.4)
        if gw.get("posts"):
            po = MB("Garden gate posts", [L["bronze"]])
            for p0, p1 in gw["posts"]:
                po.box(p0, y - 0.12, -0.3, p1, y + 0.12, 8.0)
            po.build(coll, bevel=0.002)
        if gw["gate"]:
            g0, g1 = gw["gate"]
            cedar_gate(L, coll, None, g0 + 0.03, g1 - 0.03, y - 0.06, 0.15 if three else 0.2, 8.0 if three else 7.6,
                       "Casita garden")
    for i, r in enumerate(s.get("address_walls", [])):         # low limestone walls at the walks
        ashlar(L, coll, None, [], 0.0, [r], 2.3, f"address wall {i}", 11 + i, cap=True)
        mbx = MB(f"mailbox {i}", [L["bronze"]])
        x0, y0, x1, y1 = r
        mbx.box(x0 + 0.04, y0 + 0.3, 2.45, x1 - 0.04, y0 + 1.5, 3.25)
        mbx.build(coll, bevel=0.01)
    if s.get("calcada"):
        calcada(L, coll, s["calcada"], lambda r: 0.12, "site")
    neighbourhood(L, coll, s, rng)


SIDING = {}


def siding(L, name, color):
    if name not in SIDING:
        SIDING[name] = MAT.fabric(f"Siding {name}", color, 0.85, 0.0)
    return SIDING[name]


def house(nb_parts, x0, y0, x1, y1, face, rng, garage=False):
    """A neighbouring house in plan rect (x0, y0, x1, y1), its street face at face ("s" = y0 side, "n" = y1 side):
    walls, a hipped roof, framed windows, a front door with a porch, and optionally a garage door and drive."""
    walls, roof, glass, trim, door, conc = nb_parts
    h = rng.uniform(9.5, 10.5)
    walls.box(x0, y0, 0, x1, y1, h)
    inset = min(6.0, (x1 - x0) / 3, (y1 - y0) / 3)
    ridge = h + rng.uniform(5.0, 7.0)
    pts = [(x0 - 1.5, y0 - 1.5, h), (x1 + 1.5, y0 - 1.5, h), (x1 + 1.5, y1 + 1.5, h), (x0 - 1.5, y1 + 1.5, h),
           (x0 + inset, y0 + inset, ridge), (x1 - inset, y0 + inset, ridge), (x1 - inset, y1 - inset, ridge),
           (x0 + inset, y1 - inset, ridge)]
    roof._add(pts, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)], [0] * 6, 0.5)
    fy = y0 if face == "s" else y1
    sg = -1 if face == "s" else 1
    span = x1 - x0
    xs = [x0 + span * f for f in (0.18, 0.42, 0.78)] if not garage else [x0 + span * 0.2, x0 + span * 0.45]
    for wx in xs:                                               # windows with white trim
        trim.box(wx - 2.2, fy + sg * 0.12 - 0.06, 2.6, wx + 2.2, fy + sg * 0.12 + 0.06, 7.9)
        glass.box(wx - 1.9, fy + sg * 0.18 - 0.03, 2.9, wx + 1.9, fy + sg * 0.18 + 0.03, 7.6)
    dx = x0 + span * 0.62 if not garage else x0 + span * 0.66
    door.box(dx - 1.6, fy + sg * 0.15 - 0.05, 0.6, dx + 1.6, fy + sg * 0.15 + 0.05, 7.4)
    conc.box(dx - 4.0, fy + sg * 0.0, 0, dx + 4.0, fy + sg * 5.0, 0.55)       # porch slab
    for px in (dx - 3.7, dx + 3.7):
        trim.box(px - 0.2, fy + sg * 4.6 - 0.2, 0.55, px + 0.2, fy + sg * 4.6 + 0.2, h)
    if garage:
        gx = x0 + span * 0.85
        trim.box(gx - 4.6, fy + sg * 0.14 - 0.05, 0, gx + 4.6, fy + sg * 0.14 + 0.05, 7.6)
    return fy, sg, (x0 + span * 0.85 if garage else dx)


def neighbourhood(L, coll, s, rng):
    """Neighbouring houses on both sides, across the street and behind; drives, porches; street lights."""
    W, Lo = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    walls = {k: MB(f"Neighbour walls {k}", [siding(L, k, c)]) for k, c in
             (("sand", "#D4C9B5"), ("sage", "#B9BFAE"), ("white", "#E4E1D8"), ("clay", "#C9B29A"))}
    roof = MB("Neighbour roofs", [L["house_roof"]])
    glass = MB("Neighbour glass", [L["glass"]])
    trim = MB("Neighbour trim", [L["paint"]])
    door = MB("Neighbour doors", [L["dark_wood"]])
    conc = MB("Neighbour paving", [L["concrete"]])
    keys = list(walls)
    right = W + (40 if lot.get("corner") else 12)
    plots = [(-52, 22, -12, 68, "s", True), (right, 24, right + 40, 70, "s", False),
             (-60, -96, -22, -60, "n", True), (-8, -98, 32, -60, "n", False), (46, -96, 86, -58, "n", True),
             (-50, Lo + 22, -10, Lo + 62, "s", False), (W + 8, Lo + 22, W + 48, Lo + 64, "s", True)]
    for i, (x0, y0, x1, y1, face, gar) in enumerate(plots):
        if lot.get("alley") and y0 > Lo:
            y0, y1 = y0 + 14, y1 + 14
        parts = (walls[keys[i % len(keys)]], roof, glass, trim, door, conc)
        fy, sg, dxx = house(parts, x0, y0, x1, y1, face, rng, garage=gar)
        if gar:                                                 # driveway to the street
            street_y = -12.0 if face == "s" else -40.0
            ya, yb = sorted((fy, street_y if y0 < Lo else fy + sg * 20))
            conc.box(dxx - 5.0, ya, -0.02, dxx + 5.0, yb, 0.06)
    for m in list(walls.values()) + [roof, glass, trim, door, conc]:
        m.build(coll, bevel=0.003)
    # street lights in the parkway
    sl = MB("Street lights", [L["black"], L["lamp"]])
    for x in (-30.0, W + 26.0):
        sl.box(x - 0.2, -9.2, 0, x + 0.2, -8.8, 16.0)
        sl.box(x - 0.15, -9.0, 15.6, x + 0.15, -4.5, 15.9)
        sl.box(x - 0.6, -5.2, 15.2, x + 0.6, -4.0, 15.6, mat=1)
    sl.build(coll, bevel=0.01)


def trees_and_planting(L, coll, s, rng, protos):
    W, Lo = s["lot"]["W"], s["lot"]["L"]
    leafc = bpy.data.collections.new("proto_leaf")
    bpy.context.scene.collection.children.link(leafc)
    PL.leaf_mesh("oak_leaf", leafc, L["leaf"], length=0.085, width=0.038)
    PL.leaf_mesh("oak_leaf_b", leafc, L["leaf"], length=0.06, width=0.03, bend=0.4)
    trees = [dict(x=x, y=y, h=max(20.0, r * 2.0), spread=r * 2.2, seed=int(x * 7 + y), crown=0.42)  # limbed up
             for x, y, r in s["trees"]]
    trees += [dict(x=-14, y=-9, h=30, spread=36, seed=11, leaf=0.8), dict(x=W + 16, y=-9, h=28, spread=34, seed=13, leaf=0.8),
              dict(x=-30, y=95, h=34, spread=44, seed=17, leaf=0.7), dict(x=W + 30, y=100, h=32, spread=42, seed=19, leaf=0.7),
              dict(x=W / 2, y=Lo + 30, h=38, spread=50, seed=23, leaf=0.7),
              dict(x=-40, y=-50, h=30, spread=38, seed=29, leaf=0.7), dict(x=60, y=-52, h=28, spread=34, seed=31, leaf=0.7),
              dict(x=-32, y=Lo + 10, h=32, spread=40, seed=37, leaf=0.7)]
    for tr in trees:
        PL.live_oak(f"oak_{tr['seed']}", (tr["x"] * M, tr["y"] * M, 0.0), tr["h"] * M, tr["spread"] * M, tr["seed"],
                    coll, L["bark"], leafc, leaf_density=tr.get("leaf", 1.0), crown_base=tr.get("crown", 0.22))
    bpy.context.view_layer.layer_collection.children[leafc.name].exclude = True

    pc = {}
    for key in ("feather", "muhly", "agave", "sotol", "palmetto"):
        c = bpy.data.collections.new("proto_" + key)
        bpy.context.scene.collection.children.link(c)
        pc[key] = c
    for i in range(4):
        PL.grass_clump(f"feather_{i}", pc["feather"], L["feather"], seed=i, blades=110, height=0.62, spread=0.42,
                       width=0.0035, droop=0.9)
        PL.grass_clump(f"muhly_{i}", pc["muhly"], L["grass"], seed=10 + i, blades=90, height=0.85, spread=0.35,
                       width=0.006, droop=0.5)
        PL.agave(f"agave_{i}", pc["agave"], L["agave"], seed=20 + i, n_leaves=24 + 3 * i, length=0.62 + 0.08 * i)
        PL.sotol(f"sotol_{i}", pc["sotol"], L["grass"], seed=30 + i)
        PL.palmetto(f"palmetto_{i}", pc["palmetto"], L["palm"], seed=40 + i)
    for c in pc.values():
        bpy.context.view_layer.layer_collection.children[c.name].exclude = True
    to_m = lambda pts, z=0.0: [(x * M, y * M, z) for x, y in pts]
    avoid = [(r[0] - 1.0, r[1] - 1.0, r[2] + 1.0, r[3] + 1.0) for _k, r in s["pave"]]
    for pts in s.get("paths", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            avoid.append((min(x0, x1) - 1.8, min(y0, y1) - 1.6, max(x0, x1) + 1.8, max(y0, y1) + 1.6))
    for h in s["homes"]:
        x0, y0, x1, y1 = footprint(h["t"])
        avoid.append((x0 - 1.2, y0 - 1.5, x1 + 1.2, y1 + 1.2))
    for r in [c for c in s.get("calcada", [])]:
        avoid.append((r[0] - 1, r[1] - 1, r[2] + 1, r[3] + 1))
    if s.get("street_wall"):
        (wx0, wy), (wx1, _wy) = s["street_wall"]
        avoid.append((wx0 - 0.6, wy - 1.0, wx1 + 0.6, wy + 1.0))
    front = [(0.6, 0.6), (W - 0.6, 0.6), (W - 0.6, 14.2), (0.6, 14.2)]
    ag = LS.sample_poly(front, 6, rng, avoid, 5.0)
    so = LS.sample_poly(front, 4, rng, avoid, 6.0, ag)
    fe = LS.sample_poly(front, 220, rng, avoid, 1.5, ag + so)
    LS._sc("Front agave", to_m(ag), pc["agave"], coll, scale=(0.9, 1.3))
    LS._sc("Front sotol", to_m(so), pc["sotol"], coll, scale=(0.9, 1.2))
    LS._sc("Front feather grass", to_m(fe), pc["feather"], coll, scale=(0.6, 1.05))
    if "boulder" in protos:
        bo = LS.sample_poly(front, 3, rng, avoid, 8.0, ag + so)
        LS._sc("Front boulders", to_m(bo, -0.12), protos["boulder"], coll, scale=(0.4, 0.7))
    # pátios: buffalo-grass lawn, muhly and palmetto along the fences and walls
    for p in s["patios"]:
        poly = [(p[0] + 0.4, p[1] + 0.4), (p[2] - 0.4, p[1] + 0.4), (p[2] - 0.4, p[3] - 0.4), (p[0] + 0.4, p[3] - 0.4)]
        if "lawn" in protos:
            area = (p[2] - p[0]) * (p[3] - p[1])
            lp = LS.sample_poly(poly, int(area * 3.2), rng, avoid, 0.0)
            LS._sc("Pátio lawn", to_m(lp, -0.02), protos["lawn"], coll, scale=(1.1, 1.9))
        edge = [(p[0] + 0.5, p[3] - 2.4), (p[2] - 0.5, p[3] - 2.4), (p[2] - 0.5, p[3] - 0.4), (p[0] + 0.5, p[3] - 0.4)]
        LS._sc("Pátio muhly", to_m(LS.sample_poly(edge, 14, rng, avoid, 1.4)), pc["muhly"], coll, scale=(0.9, 1.2))
        LS._sc("Pátio palmetto", to_m(LS.sample_poly(edge, 2, rng, avoid, 6.0)), pc["palmetto"], coll, scale=(1.0, 1.4))
    if "lawn" in protos:
        pk = LS.sample_poly([(-60, -11.8), (W + 60, -11.8), (W + 60, -6.2), (-60, -6.2)], 2600, rng,
                            [(r[0] - 0.5, -12.5, r[2] + 0.5, -5.5) for k, r in s["pave"] if k == "Apron" and r[1] <= 0.5],
                            0.0)
        LS._sc("Parkway lawn", to_m(pk, -0.02), protos["lawn"], coll, scale=(1.1, 1.9))
    if "shrub" in protos:
        sh = LS.sample_poly([(0.8, 16), (4.2, 16), (4.2, Lo - 6), (0.8, Lo - 6)], 8, rng, avoid, 6.0) + \
            LS.sample_poly([(W - 4.2, 16), (W - 0.8, 16), (W - 0.8, Lo - 6), (W - 4.2, Lo - 6)], 8, rng, avoid, 6.0)
        LS._sc("Side shrubs", to_m(sh), protos["shrub"], coll, scale=(1.2, 1.8))


def night_lights(coll, lights, s):
    warm = (1.0, 0.70, 0.42)
    for i, (kind, x, y, z, e) in enumerate(lights):
        ld = bpy.data.lights.new(f"night_{i}", "POINT" if kind == "point" else "SPOT")
        ld.energy = e
        ld.color = warm
        ld.shadow_soft_size = 0.12
        if kind == "spot":
            ld.spot_size = math.radians(100)
            ld.spot_blend = 0.7
        ob = bpy.data.objects.new(ld.name, ld)
        ob.location = (x * M, y * M, z * M)
        coll.objects.link(ob)
    for pts in s.get("paths", []):                           # low path lights beside the stepping stones
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 7))
            for k in range(n):
                f = (k + 0.5) / n
                ld = bpy.data.lights.new("path", "POINT")
                ld.energy, ld.color, ld.shadow_soft_size = 4, warm, 0.05
                ob = bpy.data.objects.new("path", ld)
                ob.location = ((x0 + (x1 - x0) * f + 1.3) * M, (y0 + (y1 - y0) * f) * M, 0.8 * M)
                coll.objects.link(ob)


# ---------------------------------------------------------------- scene
def oak_chair(L, root):
    """A plain Brazilian-modern dining chair: rift oak frame, cognac leather seat and back.
    Feet, seat centred on the origin, facing +y (as the Casa 01 chair prototype)."""
    c = bpy.data.collections.new("proto_oak_chair")
    root.children.link(c)
    leather = L.get("leather", L["black"])
    mb = MB("oak chair", [L["oak"], leather])
    w, d, sh, bh, lg = 0.72, 0.70, 1.50, 2.62, 0.11           # half width, half depth, seat and back height, leg
    for sx in (-1, 1):
        x0 = sx * w - (lg if sx > 0 else 0)
        mb.box(x0, d - lg, 0, x0 + lg, d, sh - 0.06, mat=0)          # front leg
        mb.box(x0, -d, 0, x0 + lg, -d + lg, bh, mat=0)              # back leg, up to the top rail
        mb.box(x0, -d + lg, 0.42, x0 + lg, d - lg, 0.50, mat=0)     # side stretcher
        mb.box(x0, -d + lg, sh - 0.22, x0 + lg, d - lg, sh - 0.08, mat=0)   # seat rail
    mb.box(-w + lg, d - lg, sh - 0.22, w - lg, d, sh - 0.08, mat=0)          # front rail
    mb.box(-w + lg, -d, sh - 0.22, w - lg, -d + lg, sh - 0.08, mat=0)        # back rail
    mb.box(-w + 0.04, -d + 0.04, sh - 0.08, w - 0.04, d - 0.02, sh + 0.02, mat=1)   # leather seat
    mb.box(-w + lg, -d + 0.01, bh - 0.62, w - lg, -d + 0.09, bh - 0.12, mat=1)     # leather back
    mb.box(-w, -d - 0.005, bh - 0.12, w, -d + lg, bh, mat=0)                         # oak top rail
    ob = mb.build(c, bevel=0.003)
    return ob


def build(site_id):
    R.reset()
    B._COBOGO.clear()
    _SOLAR.clear()
    SIDING.clear()
    root = bpy.context.scene.collection
    L = MAT.build_library()
    arch, land, night = new_coll("Architecture", root), new_coll("Landscape", root), new_coll("NightLights", root)
    PROTOS.clear()
    PROTOS.update(R.load_protos(root))
    PROTOS["chair"] = oak_chair(L, root)           # in place of the tufted Poly Haven chair
    s = SITE_OF[site_id]()
    rng = random.Random(7)
    t0 = time.time()
    lights = []
    for h in s["homes"]:
        home(L, arch, h, PROTOS, lights)
    print(f"[build] {site_id} homes {time.time() - t0:.1f}s", flush=True)
    site(L, land, s, rng)
    trees_and_planting(L, land, s, rng, PROTOS)
    print(f"[build] {site_id} site {time.time() - t0:.1f}s", flush=True)
    night_lights(night, lights, s)
    for c in list(root.children):
        if c.name.startswith(("proto", "inst_")) or c.name == "protos":
            R.exclude(c.name)
    return night


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--res", type=int, default=1600)
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args([x for x in sys.argv[1:] if x != "--"])
    os.makedirs(a.out, exist_ok=True)
    want = a.views.split(",")
    built = None
    night = None
    rx, ry = a.res, int(a.res * 9 / 16)
    for site_id in dict.fromkeys(VIEWS[v]["site"] for v in want):
        night = build(site_id)
        built = site_id
        R.setup_render(a.samples, rx, ry)
        for name in want:
            v = VIEWS[name]
            if v["site"] != built:
                continue
            R.set_world(v["hdri"], v["sun"], v["strength"])
            R.set_night(night, v["night"], v.get("night_level", 1.0))
            bpy.context.scene.view_settings.exposure = v["exposure"]
            R.set_camera(v, rx, ry)
            bpy.context.scene.render.filepath = os.path.join(a.out, f"{name}.png")
            t = time.time()
            bpy.ops.render.render(write_still=True)
            print(f"[render] {name} {rx}x{ry} {a.samples}spp in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
