"""Phase 2 massing renders: each site built in 3D from the same model as the drawings and the AutoCAD file.

    <bpy venv>/bin/python phase2/render/build.py [--sites L1-D1,L1-T1] [--fac Cplus] [--res 1100] [--samples 24]
        -> phase2/render/out/<site>_aerial.png, <site>_street.png   (in the chosen facade direction, Cplus)

Low-detail on purpose: walls with real openings and glass, floor slabs, the thin roof edge, columns and
cedar gates at the carports, plus the site (paving, pátios, fences, walls, trees, street, neighbours).
Materials come from the Casa 01 library, so Phase 2 reads in the same language.

Facade options for Casa 02 (the three-option study, phase2/study):
    base  as drawn
    A     cedar veil: the upper floor behind a cedar slat screen, front and back
    B     stepped: the upper floor slides 8 ft back from the front; roof terrace in front, cantilever behind
    C     cobogó lantern: the entry and stair column clad two stories high in cobogó
    Cplus the direction chosen from the study: C as is, plus a cedar slat gate in the Casita's cobogó garden wall
A, B, C and Cplus also give the Casita a covered porch over its pátio, and its street wall becomes cobogó.
The cobogó screen, the porch and the garden gate come from the model (homes.LANTERN, CASITA["porch"],
sites.garden_wall), so the drawings and the 3D views match.
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
ROOT = os.path.dirname(P2)
sys.path.insert(0, P2)
sys.path.insert(0, os.path.join(ROOT, "casa01", "render"))
sys.path.insert(0, os.path.join(ROOT, "casa01"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import render as R  # noqa: E402  (Casa 01: reset, render settings, sky, cameras)
import materials as MAT  # noqa: E402
from geo import MB, M, merge_copies  # noqa: E402
import house as CASA01_HOUSE  # noqa: E402  (the Casa 01 cobogó block)
from model import homes as H  # noqa: E402
from model.sites import SITES, garden_wall, tp  # noqa: E402

OUT = os.path.join(HERE, "out")

# heights (ft)
FF = 1.0                    # finished floor, above grade
GF_TOP = 10.5               # ground floor walls stop under the upper floor slab
UP_FF = 11.5                # upper finished floor
UP_TOP = 21.0               # upper walls stop under the roof
ROOF = (21.0, 22.25)        # roof slab with its 15 in bronze edge
ONE_STORY_ROOF = (11.0, 12.25)
DOOR_HEAD, WIN_HEAD = 8.0, 8.5
SILLS = {"high": 5.5, "egress": 2.25, "slot": 0.0, "fluted below 5'": 2.25, "sill 3'-6\"": 3.5,
         "to the pátio, cedar-screened": 1.0, "slot, cedar slats": 0.0, "behind the cobogó": 1.0,
         "egress, fluted below 5'": 2.25}


def wall_pieces(plan, t, z0, z1, ext_only=True, ly=0.0):
    """Boxes (x0,y0,x1,y1,za,zb,kind) for one floor's walls, with openings cut. kind: wall | inner | glass | door."""
    out = []
    for w in plan["walls"]:
        if ext_only and not w["ext"]:
            continue
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        th = w["t"]
        d0, d1 = (0.0, th) if w["ext"] else (-th / 2, th / 2)

        def box(s0, s1, da, db, za, zb, kind=None):
            kind = kind or ("wall" if w["ext"] else "inner")
            pts = [tp(t, ax + ux * s + nx * d, ay + uy * s + ny * d + ly) for s in (s0, s1) for d in (da, db)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys), za, zb, kind))
        cuts = sorted(w["openings"], key=lambda o: o["off"])
        s = 0.0
        for o in cuts + [dict(off=L, w=0, kind="end")]:
            if o["off"] - s > 1e-6:
                box(s, o["off"], d0, d1, z0, z1)
            s = o["off"] + o["w"]
        for o in cuts:
            s0, s1 = o["off"], o["off"] + o["w"]
            mid0, mid1 = d0 + (d1 - d0) * 0.45, d0 + (d1 - d0) * 0.55
            if o["kind"] == "door":
                box(s0, s1, d0, d1, z0 + DOOR_HEAD, z1)
                box(s0, s1, mid0, mid1, z0, z0 + DOOR_HEAD, "door")
            else:
                sill = 0.0 if o["kind"] == "slider" else SILLS.get(o.get("note", ""), 2.5)
                head = DOOR_HEAD if o["kind"] == "slider" else WIN_HEAD
                if sill > 0:
                    box(s0, s1, d0, d1, z0, z0 + sill)
                box(s0, s1, d0, d1, z0 + head, z1)
                box(s0, s1, mid0, mid1, z0 + sill, z0 + head, "glass")
    return out


def lbox(mb, t, x0, y0, x1, y1, z0, z1, mat=0, mats6=None):
    """Box given in a home's own frame (ft), placed on the lot by transform t."""
    pts = [tp(t, x, y) for x in (x0, x1) for y in (y0, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mb.box(min(xs), min(ys), z0, max(xs), max(ys), z1, mat=mat, mats6=mats6)


_COBOGO = {}


def cobogo_mesh(L):
    if "mesh" not in _COBOGO or _COBOGO["mesh"].name not in bpy.data.meshes:
        _COBOGO["mesh"] = CASA01_HOUSE.make_cobogo_block(L, bpy.context.scene.collection)
    return _COBOGO["mesh"]


def cobogo_panel(L, name, x0, x1, y, z0, z1, holes=()):
    """A wall of 12 x 12 in cobogó blocks along x (face to the street), from x0 to x1 at y, z0 to z1 (ft).
    holes: (x0, x1, z0, z1) openings left free of blocks, e.g. a doorway."""
    nx, nz = int(round(x1 - x0)), int(round(z1 - z0))
    offs = []
    for i in range(nx):
        for k in range(nz):
            cx, cz = x0 + i + 0.5, z0 + k + 0.5
            if any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes):
                continue
            offs.append((cx * M, (y + 0.165) * M, cz * M))
    ob = merge_copies(cobogo_mesh(L), offs, name, bpy.context.scene.collection)
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width = 0.003
    bv.segments = 2
    bv.limit_method = "ANGLE"
    return ob


def build_home(h, origin, L, idx, fac="base"):
    plan = h["plan"]
    t = h["t"]
    ox, oy = origin
    casa = plan is not H.CASITA
    W, D = plan["W"], plan["D"]
    step = 8.0 if (casa and fac == "B") else 0.0
    clad = "stucco"                      # stone is added on top where the plan has it (stone_runs, piers)
    mb = MB(f"{h['id']} walls", [L[clad], L["stucco"], L["glass"], L["oak_door"], L["paint"]])
    for x0, y0, x1, y1, za, zb, kind in wall_pieces(plan, t, FF, GF_TOP if casa else ONE_STORY_ROOF[0], ext_only=False):
        m = {"wall": 0, "inner": 4, "glass": 2, "door": 3}[kind]
        mb.box(x0 + ox, y0 + oy, za, x1 + ox, y1 + oy, zb, mat=m)
    if casa:
        for x0, y0, x1, y1, za, zb, kind in wall_pieces(H.CASA02_UPPER, t, UP_FF, UP_TOP, ext_only=False, ly=step):
            m = {"wall": 1, "inner": 4, "glass": 2, "door": 3}[kind]
            mb.box(x0 + ox, y0 + oy, za, x1 + ox, y1 + oy, zb, mat=m)
    mb.build(bpy.context.scene.collection, bevel=0.004)

    # slabs, the thin edges, columns, gate
    sb = MB(f"{h['id']} slabs", [L["roof"], L["bronze"], L["cedar_y"], L["floor"], L["stucco"], L["glass"]])
    ext = [tp(t, *w["a"]) for w in plan["walls"] if w["ext"]]
    sb.prism([(x + ox, y + oy) for x, y in ext], 0.0, FF, top=3, side=4, bottom=4)
    o = 1.0  # roof overhang
    if casa:
        lbox(sb, t, 0, 0, W, D + step, UP_FF - 1.25, UP_FF, mats6=[2, 4, 1, 1, 1, 1])     # upper floor: bronze band
        lbox(sb, t, -o, step - o, W + o, D + step + o, ROOF[0], ROOF[1], mats6=[2, 0, 1, 1, 1, 1])
        if step:
            lbox(sb, t, 0.2, 0.15, W - 0.2, 0.4, UP_FF, UP_FF + 3.4, mat=5)              # terrace glass rail
            lbox(sb, t, 0, 0.1, W, 0.45, UP_FF + 3.4, UP_FF + 3.55, mat=1)
    else:
        lbox(sb, t, -o, -o, W + o, D + o, ONE_STORY_ROOF[0], ONE_STORY_ROOF[1], mats6=[2, 0, 1, 1, 1, 1])
        if plan.get("porch") and fac != "base":                                         # Casita porch over its pátio
            x0, y0, x1, y1 = plan["porch"]["roof"]
            lbox(sb, t, W + o, y0, x1, y1, ONE_STORY_ROOF[0], ONE_STORY_ROOF[1], mats6=[2, 0, 1, 1, 1, 1])
    sb.build(bpy.context.scene.collection, bevel=0.003)

    det = MB(f"{h['id']} details", [L["bronze"], L["cedar_z"]])
    for cx, cy in plan.get("columns", []):
        lbox(det, t, cx - 0.25, cy - 0.25, cx + 0.25, cy + 0.25, FF, UP_FF - 1.25, mat=0)
    if step:                                                                             # cantilever columns
        for cx in (0.4, W - 0.4):
            lbox(det, t, cx - 0.25, D + step - 0.65, cx + 0.25, D + step - 0.15, FF - 0.9, UP_FF - 1.25, mat=0)
    if plan.get("porch") and fac != "base":
        for cx, cy in plan["porch"]["posts"]:
            lbox(det, t, cx - 0.25, cy - 0.25, cx + 0.25, cy + 0.25, FF - 0.9, ONE_STORY_ROOF[0], mat=0)
    if plan.get("gate") and h.get("gate", True):
        (gx0, gy0), (gx1, gy1) = plan["gate"]
        n = int(abs(gx1 - gx0) / 0.42)
        for i in range(n):
            x = gx0 + (gx1 - gx0) * (i + 0.5) / n
            lbox(det, t, x - 0.14, gy0 + 0.16, x + 0.14, gy0 + 0.34, FF + 0.15, FF + 8.0, mat=1)
    if casa and fac == "A":                                                               # cedar veil, front and back
        n = int(W / 0.42)
        for i in range(n):
            x = (i + 0.5) * W / n
            for y0, y1 in ((-1.35, -1.1), (D + 1.1, D + 1.35)):
                lbox(det, t, x - 0.085, y0, x + 0.085, y1, UP_FF - 1.25, ROOF[0], mat=1)
        for y0, y1 in ((-1.4, -1.05), (D + 1.05, D + 1.4)):
            for z in (UP_FF - 1.4, ROOF[0] - 0.15):
                lbox(det, t, 0, y0, W, y1, z, z + 0.15, mat=0)
    det.build(bpy.context.scene.collection, bevel=0.002)
    if fac in ("C", "Cplus"):                                                            # the Casa 01 staples
        stone_and_calcada(plan, t, L, h["id"], casa)
    lan = plan.get("lantern")
    if casa and lan and fac in ("C", "Cplus") and t["rot"] in (0, 180):                  # cobogó lantern
        (xa, ya), (xb, yb) = tp(t, lan["x"][0], lan["y"][0]), tp(t, lan["x"][1], lan["y"][1])
        holes = []
        if lan.get("opening"):                                                           # open at the front door
            pa, pb = tp(t, lan["opening"][0], 0.0)[0], tp(t, lan["opening"][1], 0.0)[0]
            holes.append((min(pa, pb) + ox, max(pa, pb) + ox, FF - 0.1, FF + 8.0))
        cobogo_panel(L, f"{h['id']} cobogo", min(xa, xb) + ox, max(xa, xb) + ox, min(ya, yb) + oy, FF, ROOF[0], holes)


def stone_and_calcada(plan, t, L, hid, casa):
    """Lueders limestone on the plan's stone runs (cut at the openings) and piers; calçada rugs; the carport slab."""
    st = MB(f"{hid} stone", [L["limestone"], L["calcada"], L["concrete"]])
    top = GF_TOP if casa else ONE_STORY_ROOF[0]
    for run in H.stone_runs(plan):
        (ax, ay), (ux, uy), (nx, ny), Lr = run["a"], run["u"], run["n"], run["L"]

        def face(q0, q1, z0, z1):
            pts = [tp(t, ax + ux * q + nx * d, ay + uy * q + ny * d) for q in (q0, q1) for d in (-0.08, 0.02)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            st.box(min(xs), min(ys), z0, max(xs), max(ys), z1, mat=0)
        s0 = 0.0
        for h0, h1, o in run["holes"]:
            if h0 > s0:
                face(s0, h0, 0.0, top)
            sill = 0.0 if o["kind"] in ("door", "slider") else SILLS.get(o.get("note", ""), 2.5)
            head = DOOR_HEAD if o["kind"] in ("door", "slider") else WIN_HEAD
            if sill > 0:
                face(h0, h1, 0.0, FF + sill)
            face(h0, h1, FF + head, top)
            s0 = max(s0, h1)
        if s0 < Lr:
            face(s0, Lr, 0.0, top)
    for r in plan.get("stone", {}).get("piers", []):
        lbox(st, t, r[0], r[1], r[2], r[3], 0.0, UP_FF - 1.25, mat=0)
    for r in plan["rooms"]:                                                          # carport slab
        if r.get("outdoor"):
            lbox(st, t, *r["rect"], -0.2, 0.15, mat=2)
    for r in plan.get("calcada", []):
        x0, y0, x1, y1 = r
        under_door = y1 <= 0.01                                                      # threshold: a step to FF
        z1 = FF - 0.01 if under_door else 0.17
        lbox(st, t, x0, y0, x1, y1, z1 - 0.12, z1, mats6=[2, 2, 2, 2, 2, 2])
        b = 0.3 if min(x1 - x0, y1 - y0) > 1.5 else 0.1
        lbox(st, t, x0 + b, y0 + b, x1 - b, y1 - b, z1 - 0.1, z1 + 0.006, mats6=[2, 1, 2, 2, 2, 2])
    st.build(bpy.context.scene.collection, bevel=0.003)


def tree(x, y, r, L, seed):
    rng = random.Random(seed)
    coll = bpy.context.scene.collection
    h = max(10.0, r * 1.6)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45 * M * (r / 8), depth=h * 0.6 * M,
                                       location=(x * M, y * M, h * 0.3 * M))
    tr = bpy.context.active_object
    tr.data.materials.append(L["bark"])
    for k in range(4):
        a = rng.uniform(0, 2 * math.pi)
        d = r * rng.uniform(0.15, 0.45)
        rr = r * rng.uniform(0.55, 0.75)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rr * M,
                                              location=((x + d * math.cos(a)) * M, (y + d * math.sin(a)) * M,
                                                        (h * 0.62 + rng.uniform(-1, 2)) * M))
        s = bpy.context.active_object
        s.scale = (1.0, 1.0, 0.62)
        s.data.materials.append(L["leaf"])
        bpy.ops.object.shade_smooth()
    del coll


def build_site(s, L, fac="base"):
    W, Lo = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    g = MB("ground", [L["lawn_soil"], L["asphalt"], L["sidewalk"], L["turf"], L["concrete"], L["pavers"], L["dg"]])
    g.box(-400, -400, -0.3, W + 400, Lo + 400, -0.05, mat=0)                   # surrounding yards
    g.box(-400, -36, -0.25, W + 400, -12, 0.0, mat=1)                           # street
    g.box(-400, -6, -0.2, W + 400, -1, 0.02, mat=2)                             # sidewalk
    if lot.get("alley"):
        g.box(-400, Lo + 1, -0.25, W + 400, Lo + 15, 0.0, mat=1)
    if lot.get("corner"):
        g.box(W + 12, -400, -0.27, W + 36, Lo + 400, -0.01, mat=1)
        g.box(W + 6, -6, -0.2, W + 11, Lo + 400, 0.02, mat=2)
    g.box(0, 0, -0.05, W, 15, 0.02, mat=6)                                       # front yard: decomposed granite
    for p in s["patios"]:
        g.box(p[0], p[1], 0.0, p[2], p[3], 0.06, mat=3)
    for k, r in s["pave"]:
        g.box(r[0], r[1], 0.0, r[2], r[3], 0.1, mat=5 if k in ("Terrace", "Walk") else 4)
    for pts in s.get("paths", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 2.2))
            for i in range(n):
                f = (i + 0.5) / n
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                g.box(x - 0.8, y - 0.55, 0.0, x + 0.8, y + 0.55, 0.12, mat=5)
    g.build(bpy.context.scene.collection)
    f = MB("fences + walls", [L["fence"], L["stucco"]])
    for pts in s.get("fence", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            f.box(min(x0, x1) - 0.08, min(y0, y1) - 0.08, 0.0, max(x0, x1) + 0.08, max(y0, y1) + 0.08, 6.0, mat=0)
    for pts in s.get("walls", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            f.box(min(x0, x1) - 0.25, min(y0, y1) - 0.25, 0.0, max(x0, x1) + 0.25, max(y0, y1) + 0.25, 6.0, mat=1)
    sw = s.get("street_wall")
    if sw and fac == "base":
        (x0, y0), (x1, y1) = sw
        f.box(min(x0, x1) - 0.25, min(y0, y1) - 0.25, 0.0, max(x0, x1) + 0.25, max(y0, y1) + 0.25, 6.0, mat=1)
    f.build(bpy.context.scene.collection, bevel=0.003)
    if sw and fac != "base":                            # limestone piers, cobogó, and in Cplus a cedar gate
        gw = garden_wall(s if fac == "Cplus" else dict(s, garden_gate=None))
        y0 = gw["y"]
        pier = MB("garden wall piers", [L["limestone"], L["cedar_z"]])
        for p0, p1 in gw["piers"]:
            pier.box(p0, y0 - 0.4, 0.0, p1, y0 + 0.4, 8.5, mat=0)
        if gw["gate"]:
            g0, g1 = gw["gate"]
            n = int((g1 - g0) / 0.42)
            for i in range(n):
                x = g0 + (i + 0.5) * (g1 - g0) / n
                pier.box(x - 0.14, y0 - 0.09, 0.25, x + 0.14, y0 + 0.09, 7.5, mat=1)
        pier.build(bpy.context.scene.collection, bevel=0.003)
        cobogo_panel(L, "Casita garden cobogo", gw["cobogo"][0], gw["cobogo"][1], y0 - 0.165, 0.5, 8.5)
    for i, (x, y, r) in enumerate(s["trees"]):
        tree(x, y, r, L, i * 13 + int(x))
    # neighbouring houses for scale
    nb = MB("neighbours", [L["house_beige"], L["house_roof"]])
    for x0, x1 in ((-55, -10), (W + (40 if lot.get("corner") else 10), W + (85 if lot.get("corner") else 55))):
        nb.box(x0, 25, 0, x1, 75, 11, mat=0)
        nb.box(x0 - 1, 24, 11, x1 + 1, 76, 12.5, mat=1)
    nb.build(bpy.context.scene.collection)
    for h in s["homes"]:
        build_home(h, (0.0, 0.0), L, 0, fac)


def views(s):
    W, Lo = s["lot"]["W"], s["lot"]["L"]
    return {
        "aerial": dict(cam=(W + 48, -48, 72), tgt=(W / 2, Lo * 0.42, 4), lens=30, two_point=False),
        "street": dict(cam=(W * 0.85, -30, 5.5), tgt=(W * 0.45, 30, 11), lens=20),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default="")
    ap.add_argument("--res", type=int, default=1100)
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--fac", default="Cplus")
    a = ap.parse_args([x for x in sys.argv[1:] if x != "--"])
    want = set(filter(None, a.sites.split(",")))
    os.makedirs(OUT, exist_ok=True)
    for fn in SITES:
        s = fn()
        if want and s["id"] not in want:
            continue
        R.reset()
        _COBOGO.clear()                      # the cached block mesh went with the old scene
        L = MAT.build_library()
        build_site(s, L, a.fac)
        R.setup_render(a.samples, a.res, int(a.res * 9 / 16))
        R.set_world("day", 215, 1.0)
        bpy.context.scene.view_settings.exposure = -0.3
        for name, v in views(s).items():
            R.set_camera(v, a.res, int(a.res * 9 / 16))
            bpy.context.scene.render.filepath = os.path.join(OUT, f"{s['id']}_{name}.png")
            bpy.ops.render.render(write_still=True)
            print(f"[render] {s['id']} {name}", flush=True)


if __name__ == "__main__":
    main()
