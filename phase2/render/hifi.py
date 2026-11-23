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


def ashlar(L, coll, t, runs, top, piers, pier_top, name, seed):
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
        for i, (cz0, cz1) in enumerate(courses(0.0, pier_top)):
            r = rng.random()
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


def furnish(L, coll, plan, t, z, name, protos):
    mb = MB(f"{name} furniture", [L["oak"], L["granite"], L["linen"], L["ceramic"], L["black"]])
    idx = {"oak": 0, "granite": 1, "linen": 2, "ceramic": 3, "black": 4}
    for f in plan.get("fixtures", []):
        k = f["kind"]
        if k not in FURN or "rect" not in f:
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
    casa = plan is not H.CASITA
    W, D = plan["W"], plan["D"]
    nm = f"{h['id']}"
    rng = random.Random(hash(nm) % 1000)
    walls = MB(f"{nm} walls", [L["stucco"], L["paint"]])
    floors = [(FF, GF_TOP if casa else ONE[0], plan)] + ([(UP_FF, UP_TOP, H.CASA02_UPPER)] if casa else [])
    for z0, z1, pl in floors:
        for x0, y0, x1, y1, za, zb, kind in B.wall_pieces(pl, t, z0, z1, ext_only=False):
            if kind in ("glass", "door"):
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
        lb(sl, t, -o, -o, xr, D + o, ROOF[0], ROOF[1], mats6=[6, 5, 4, 4, 4, 4])
    else:
        lb(sl, t, -o, -o, W + o, D + o, ONE[0], ONE[1], mats6=[6, 5, 4, 4, 4, 4])
        pr = plan.get("porch")
        if pr:
            x0, y0, x1, y1 = pr["roof"]
            lb(sl, t, W + o, y0, x1, y1, ONE[0], ONE[1], mats6=[6, 5, 4, 4, 4, 4])
    sl.build(coll, bevel=0.003)
    if casa:                                                   # rooftop solar, 3 ft clear of the edges
        pv = MB(f"{nm} solar", [SOLAR(), L["bronze"]])
        for row in range(3):
            y0 = 9.0 + row * 6.4
            for col in range(3):
                x0 = 2.5 + col * 5.0
                lb(pv, t, x0, y0, x0 + 4.8, y0 + 5.6, ROOF[1] + 0.35, ROOF[1] + 0.45, mats6=[1, 0, 1, 1, 1, 1])
                lb(pv, t, x0 + 0.4, y0 + 0.4, x0 + 0.6, y0 + 5.2, ROOF[1], ROOF[1] + 0.35, mat=1)
                lb(pv, t, x0 + 4.2, y0 + 0.4, x0 + 4.4, y0 + 5.2, ROOF[1], ROOF[1] + 0.35, mat=1)
        pv.build(coll, bevel=0.002)
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
        (gx0, gy0), (gx1, _gy1) = plan["gate"]
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
        B.cobogo_panel(L, f"{nm} cobogo", min(xa, xb), max(xa, xb), min(ya, yb), FF, ROOF[0], holes)
        cap = MB(f"{nm} cobogo frame", [L["bronze"]])
        lb(cap, t, lan["x"][0], lan["y"][0] - 0.03, lan["x"][1], lan["y"][1] + 0.03, FF - 0.12, FF)
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
        ashlar(L, coll, None, runs, 0.0, piers, 8.5, "garden wall", 5)
        c0, c1 = gw["cobogo"]
        B.cobogo_panel(L, "Garden cobogo", c0, c1, y - 0.165, 0.4, 8.4)
        if gw["gate"]:
            g0, g1 = gw["gate"]
            cedar_gate(L, coll, None, g0 + 0.03, g1 - 0.03, y - 0.06, 0.2, 7.6, "Casita garden")
    if s.get("calcada"):
        calcada(L, coll, s["calcada"], lambda r: 0.12, "site")
    # neighbours, with trees behind
    nb = MB("Neighbours", [L["house_beige"], L["house_roof"], L["glass"], L["bronze"]])
    right = W + (40 if lot.get("corner") else 12)
    for (x0, x1) in ((-50, -12), (right, right + 38)):
        y0, y1 = 22, 70
        nb.box(x0, y0, 0, x1, y1, 10.0, mat=0)
        inset = 6.0
        pts = [(x0 - 1.5, y0 - 1.5, 10), (x1 + 1.5, y0 - 1.5, 10), (x1 + 1.5, y1 + 1.5, 10), (x0 - 1.5, y1 + 1.5, 10),
               (x0 + inset, y0 + inset, 16.5), (x1 - inset, y0 + inset, 16.5), (x1 - inset, y1 - inset, 16.5),
               (x0 + inset, y1 - inset, 16.5)]
        faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)]
        nb._add(pts, faces, [1] * 6, 0.5)
        for k in range(3):
            wx = x0 + 6 + k * (x1 - x0 - 12) / 2
            nb.box(wx - 2, y0 - 0.1, 3.0, wx + 2, y0 + 0.05, 7.5, mat=2)
    nb.build(coll)


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
              dict(x=W / 2, y=Lo + 30, h=38, spread=50, seed=23, leaf=0.7)]
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
def build(site_id):
    R.reset()
    B._COBOGO.clear()
    _SOLAR.clear()
    root = bpy.context.scene.collection
    L = MAT.build_library()
    arch, land, night = new_coll("Architecture", root), new_coll("Landscape", root), new_coll("NightLights", root)
    PROTOS.clear()
    PROTOS.update(R.load_protos(root))
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
