"""Builds the Casa 01 architecture from design.py (feet) into Blender (meters)."""
import math
import random

import bpy
import bmesh
from mathutils import Vector, Matrix

import design as D
from geo import MB, M, merge_copies, subtract_rect

FF, CEIL = D.FF, D.CEIL


def _wall_frame(w):
    a = Vector(w["a"]); b = Vector(w["b"])
    L = (b - a).length
    u = (b - a) / L
    n = Vector((-u.y, u.x))
    return a, b, L, u, n


def _rect(a, u, n, s0, s1, d0, d1):
    p0 = a + u * s0 + n * d0
    p1 = a + u * s1 + n * d1
    return min(p0.x, p1.x), min(p0.y, p1.y), max(p0.x, p1.x), max(p0.y, p1.y)


def _outer_idx(n):
    if n.y > 0.5:
        return 2
    if n.y < -0.5:
        return 3
    if n.x > 0.5:
        return 4
    return 5


def _is_reflex(i):
    P = D.FOOTPRINT
    k = len(P)
    a, b, c = Vector(P[(i - 1) % k]), Vector(P[i]), Vector(P[(i + 1) % k])
    u1, u2 = b - a, c - b
    return u1.x * u2.y - u1.y * u2.x < 0


def build_house(L, coll):
    walls = MB("Walls", [L["paint"], L["stucco"]])
    frames = MB("Window frames", [L["bronze"]])
    glass = MB("Glass", [L["glass"]])
    cedar_z = MB("Cedar vertical", [L["cedar_z"]])
    slab = MB("Slab", [L["floor"], L["concrete"]])

    # ---- slab
    slab.prism(D.FOOTPRINT, 0.0, FF, top=0, side=1, bottom=1)

    # ---- exterior walls with openings
    nP = len(D.FOOTPRINT)
    for wi, w in enumerate(D.EXT_WALLS):
        a, b, Lw, u, n = _wall_frame(w)
        t = D.EXT_T
        ext_end = t if _is_reflex((wi + 1) % nP) else 0.0
        oi = _outer_idx(n)
        mats6 = [0, 0, 0, 0, 0, 0]
        mats6[oi] = 1
        ops = sorted(w["openings"], key=lambda o: o["off"])
        s = 0.0
        for o in ops:
            s0, s1 = o["off"], o["off"] + o["w"]
            x0, y0, x1, y1 = _rect(a, u, n, s, s0, 0, t)
            walls.box(x0, y0, 0, x1, y1, CEIL, mats6=mats6)
            x0, y0, x1, y1 = _rect(a, u, n, s0, s1, 0, t)
            if o["sill"] > 0:
                walls.box(x0, y0, 0, x1, y1, FF + o["sill"], mats6=mats6)
            walls.box(x0, y0, FF + o["head"], x1, y1, CEIL, mats6=mats6)
            _opening(o, a, u, n, frames, glass, cedar_z, L)
            s = s1
        x0, y0, x1, y1 = _rect(a, u, n, s, Lw + ext_end, 0, t)
        walls.box(x0, y0, 0, x1, y1, CEIL, mats6=mats6)

    # ---- interior partitions
    for p in D.PARTITIONS:
        a = Vector(p["a"]); b = Vector(p["b"])
        Lp = (b - a).length
        u = (b - a) / Lp
        n = Vector((-u.y, u.x))
        t = D.INT_T
        s = 0.0
        for o in sorted(p["openings"], key=lambda o: o["off"]):
            x0, y0, x1, y1 = _rect(a, u, n, s, o["off"], -t / 2, t / 2)
            walls.box(x0, y0, FF, x1, y1, CEIL, mat=0)
            x0, y0, x1, y1 = _rect(a, u, n, o["off"], o["off"] + o["w"], -t / 2, t / 2)
            walls.box(x0, y0, FF + 8.0, x1, y1, CEIL, mat=0)
            s = o["off"] + o["w"]
        x0, y0, x1, y1 = _rect(a, u, n, s, Lp, -t / 2, t / 2)
        walls.box(x0, y0, FF, x1, y1, CEIL, mat=0)

    walls.build(coll, bevel=0.004)
    slab.build(coll)
    frames.build(coll, bevel=0.002)
    glass.build(coll)

    _limestone_wall(L, coll)
    roof_ob = _roof(L, coll)
    _skylights(L, coll, roof_ob)
    _cobogo(L, coll)
    _gate_and_screen(L, coll, cedar_z)
    _doors(L, coll)
    _posts(L, coll)
    _hardscape(L, coll)
    cedar_z.build(coll, bevel=0.002)


# --------------------------------------------------------------------------- openings
def _opening(o, a, u, n, frames, glass, cedar, L):
    s0, s1 = o["off"], o["off"] + o["w"]
    z0 = FF + o["sill"]
    z1 = FF + o["head"]
    fw = 0.17
    d0, d1 = 0.06, 0.42
    if o["kind"] == "pivot":
        # dark bronze frame + cedar-slat pivot door, slightly ajar
        for (q0, q1, zz0, zz1) in ((s0, s0 + 0.12, z0, z1), (s1 - 0.12, s1, z0, z1), (s0, s1, z1 - 0.12, z1)):
            x0, y0, x1, y1 = _rect(a, u, n, q0, q1, d0, d1)
            frames.box(x0, y0, zz0, x1, y1, zz1)
        dw = o["w"] - 0.24
        piv = s0 + 0.12 + dw * 0.25
        ang = math.radians(28)
        # door panel as a rotated slab built from slats
        n_sl = int(dw / 0.24)
        for k in range(n_sl):
            t0 = -dw * 0.25 + k * (dw / n_sl) + 0.01
            t1 = t0 + dw / n_sl - 0.03
            for (tt0, tt1) in ((t0, t1),):
                c0 = Vector((tt0 * math.cos(ang), tt0 * math.sin(ang)))
                c1 = Vector((tt1 * math.cos(ang), tt1 * math.sin(ang)))
                base = a + u * piv + n * 0.22
                p0 = base + u * c0.x + n * c0.y
                p1 = base + u * c1.x + n * c1.y
                # thin slat: approximate rotated box with a quad strip box
                _rot_box(cedar, p0, p1, n.copy(), 0.18, z0 + 0.05, z1 - 0.15)
        return
    # frame members
    for (q0, q1, zz0, zz1) in ((s0, s0 + fw, z0, z1), (s1 - fw, s1, z0, z1),
                               (s0, s1, z0, z0 + fw), (s0, s1, z1 - fw, z1)):
        x0, y0, x1, y1 = _rect(a, u, n, q0, q1, d0, d1)
        frames.box(x0, y0, zz0, x1, y1, zz1)
    panels = o.get("panels", 1)
    if o["kind"] == "casement" and o["w"] > 3.5:
        panels = 2
    pw = (s1 - s0) / panels
    for k in range(panels):
        q0 = s0 + k * pw
        q1 = q0 + pw
        dd = 0.0
        if o["kind"] == "slider":
            dd = 0.09 if k % 2 else -0.06
        if k > 0:
            x0, y0, x1, y1 = _rect(a, u, n, q0 - 0.09, q0 + 0.09, d0 + 0.05, d1 - 0.05)
            frames.box(x0, y0, z0, x1, y1, z1)
        x0, y0, x1, y1 = _rect(a, u, n, q0 + 0.05, q1 - 0.05, 0.23 + dd, 0.25 + dd)
        glass.box(x0, y0, z0 + 0.1, x1, y1, z1 - 0.1)
        if o["kind"] == "slider":
            # slim sash rails
            for (zz0, zz1) in ((z0 + fw, z0 + fw + 0.12), (z1 - fw - 0.08, z1 - fw)):
                x0, y0, x1, y1 = _rect(a, u, n, q0 + 0.05, q1 - 0.05, 0.19 + dd, 0.29 + dd)
                frames.box(x0, y0, zz0, x1, y1, zz1)


def _rot_box(mb, p0, p1, n, depth, z0, z1):
    """Box whose base edge runs p0->p1 (plan) with thickness `depth` along the
    perpendicular. Appends 8-vertex box directly."""
    d = (p1 - p0)
    perp = Vector((-d.y, d.x)).normalized() * depth
    q = [p0, p1, p1 + perp, p0 + perp]
    verts = [(c.x, c.y, z0) for c in q] + [(c.x, c.y, z1) for c in q]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mb._add(verts, faces, [0] * 6, random.random())


# --------------------------------------------------------------------------- limestone
def _limestone_wall(L, coll):
    lw = D.LIMESTONE_WALL
    stones = MB("Limestone ashlar", [L["limestone"]])
    mort = MB("Limestone mortar", [L["mortar"]])
    rng = random.Random(42)
    yf, yb = lw["y_face"], lw["y_back"]
    joint = 0.03
    # window hole (Bed 2 slot window)
    w = D.EXT_WALLS[0]
    o = w["openings"][0]
    hole = (w["a"][0] + o["off"], w["a"][0] + o["off"] + o["w"], FF + o["sill"], FF + o["head"])
    # mortar bed behind the stones, with the window opening cut out of it
    for (a0, a1, b0, b1) in subtract_rect((lw["x0"], lw["x1"], lw["z0"], lw["z1"]), hole):
        mort.box(a0, yf + 0.06, b0, a1, yb, b1)
    courses = []
    z = lw["z0"]
    pattern = [0.667, 0.333, 1.0, 0.333, 0.667, 0.667, 1.0, 0.333]
    i = 0
    while z < lw["z1"] - 0.05:
        h = pattern[i % len(pattern)] if i else 0.667
        h = min(h, lw["z1"] - z)
        courses.append((z, z + h))
        z += h
        i += 1
    for (cz0, cz1) in courses:
        x = lw["x0"] - rng.uniform(0, 1.5)
        while x < lw["x1"]:
            ln = rng.uniform(1.4, 3.6) if cz1 - cz0 < 0.9 else rng.uniform(1.8, 4.2)
            sx0, sx1 = max(x, lw["x0"]), min(x + ln, lw["x1"])
            x += ln
            if sx1 - sx0 < 0.25:
                continue
            r = rng.random()
            for (a0, a1, b0, b1) in subtract_rect((sx0, sx1, cz0, cz1), (hole[0] - 0.02, hole[1] + 0.02, hole[2], hole[3])):
                if a1 - a0 < 0.05 or b1 - b0 < 0.05:
                    continue
                proud = rng.uniform(-0.012, 0.012)
                stones.box(a0 + joint / 2, yf + proud, b0 + joint / 2, a1 - joint / 2, yb - 0.01, b1 - joint / 2, r=r)
    stones.build(coll, bevel=0.003)
    mort.build(coll)
    # window frame in the veneer reveal (bronze), deep-set look
    fr = MB("Slot window reveal", [L["bronze"]])
    hx0, hx1, hz0, hz1 = hole
    fr.box(hx0 - 0.02, yf - 0.02, hz0 - 0.08, hx1 + 0.02, yb, hz0)       # sill flashing
    fr.build(coll)


# --------------------------------------------------------------------------- roof
def _roof(L, coll):
    roof = MB("Roof", [L["roof"], L["bronze"], L["stucco"]])
    roof.prism(D.ROOF, D.FASCIA_BOT, D.FASCIA_TOP, top=0, side=1, bottom=2)
    # gravel-stop lip
    roof_ob = roof.build(coll, bevel=0.003)
    # cedar soffit + ceiling boards
    boards = MB("Cedar soffits", [L["cedar_y"]])
    rng = random.Random(9)
    bw, gap, th = 5.5 / 12, 0.25 / 12, 0.06
    for zone in D.CEDAR_SOFFITS + D.CEDAR_CEILINGS:
        x = zone["x0"]
        while x < zone["x1"] - 0.05:
            x1 = min(x + bw, zone["x1"])
            y = zone["y0"]
            while y < zone["y1"] - 0.05:
                ln = rng.uniform(8, 16)
                y1 = min(y + ln, zone["y1"])
                boards.box(x, y, D.CEIL - th, x1, y1 - 0.01, D.CEIL - 0.002, r=rng.random())
                y = y1
            x = x1 + gap
    boards.build(coll, bevel=0.002)
    return roof_ob


# --------------------------------------------------------------------------- cobogó
def make_cobogo_block(L, coll):
    """12x12x4 precast breeze block: large circle at center, medium circles at
    corners and small circles at edge mid-points (they complete across blocks)."""
    s = D.BLOCK * M
    dep = D.COBOGO["t"] * M
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(s * 0.985, dep, s * 0.985), verts=bm.verts)
    me = bpy.data.meshes.new("cobogo_block_base")
    bm.to_mesh(me)
    bm.free()
    blk = bpy.data.objects.new("cobogo_block_base", me)
    coll.objects.link(blk)
    cutters = []

    def cyl(x, z, r):
        bmc = bmesh.new()
        bmesh.ops.create_cone(bmc, cap_ends=True, segments=40, radius1=r, radius2=r, depth=dep * 3)
        bmesh.ops.rotate(bmc, verts=bmc.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
        bmesh.ops.translate(bmc, verts=bmc.verts, vec=(x, 0, z))
        mc = bpy.data.meshes.new("cut")
        bmc.to_mesh(mc)
        bmc.free()
        oc = bpy.data.objects.new("cut", mc)
        coll.objects.link(oc)
        oc.hide_render = True
        cutters.append(oc)
        mod = blk.modifiers.new("b", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = oc

    h = s / 2
    cyl(0, 0, 0.30 * s)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cyl(sx * h, sz * h, 0.24 * s)
    for (x, z) in ((0, h), (0, -h), (h, 0), (-h, 0)):
        cyl(x, z, 0.085 * s)
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(blk.evaluated_get(dg))
    for o in cutters + [blk]:
        bpy.data.objects.remove(o)
    me2.materials.append(L["cobogo"])
    return me2


def _cobogo(L, coll):
    c = D.COBOGO
    block = make_cobogo_block(L, coll)
    offs = []
    nx = int(round((c["x1"] - c["x0"]) / D.BLOCK))
    nz = int(round((c["z1"] - c["z0"]) / D.BLOCK))
    for i in range(nx):
        for k in range(nz):
            x = (c["x0"] + (i + 0.5) * D.BLOCK) * M
            y = (c["y"] + c["t"] / 2) * M
            z = (c["z0"] + (k + 0.5) * D.BLOCK) * M
            offs.append((x, y, z))
    ob = merge_copies(block, offs, "Cobogo screen", coll)
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width = 0.003
    bv.segments = 2
    bv.limit_method = "ANGLE"
    # mortar backing strips + cast concrete curb
    mb = MB("Cobogo curb", [L["concrete"], L["cobogo"]])
    mb.box(c["x0"] - 0.5, c["y"] - 0.05, D.GRADE, c["x1"] + 0.3, c["y"] + c["t"] + 0.05, c["z0"], mat=0)
    for i in range(nx + 1):
        x = c["x0"] + i * D.BLOCK
        mb.box(x - 0.008, c["y"] + 0.03, c["z0"], x + 0.008, c["y"] + c["t"] - 0.03, c["z1"], mat=1)
    for k in range(nz + 1):
        z = c["z0"] + k * D.BLOCK
        mb.box(c["x0"], c["y"] + 0.03, z - 0.008, c["x1"], c["y"] + c["t"] - 0.03, z + 0.008, mat=1)
    mb.build(coll)


# --------------------------------------------------------------------------- gate & screen
def _slats_y(cedar_z, x, y0, y1, z0, z1, sw, sd, gap, skip=()):
    """Vertical cedar slats along a screen line parallel to Y (face at x, depth -sd)."""
    y = y0
    while y + sw <= y1 + 1e-6:
        if not any(a - 0.02 < y + sw and y < b + 0.02 for (a, b) in skip):
            cedar_z.box(x - sd, y, z0, x, y + sw, z1)
        y += sw + gap


def _slats_x(cedar_z, y, x0, x1, z0, z1, sw, sd, gap):
    x = x0
    while x + sw <= x1 + 1e-6:
        cedar_z.box(x, y, z0, x + sw, y + sd, z1)
        x += sw + gap


def _gate_and_screen(L, coll, cedar_z):
    g = D.ENTRY_GATE
    steel = MB("Gate steel", [L["bronze"], L["brass"]])
    # jamb posts
    steel.box(g["x0"] - 0.33, g["y"], g["z0"] - 0.85, g["x0"], g["y"] + 0.33, g["z1"])
    steel.box(g["x1"], g["y"], g["z0"] - 0.85, g["x1"] + 0.5, g["y"] + 0.33, g["z1"])
    # gate leaf: frame + cedar slats, closed
    gx0, gx1 = g["x0"] + 0.04, g["x1"] - 0.04
    steel.box(gx0, g["y"] + 0.12, g["z0"] + 0.05, gx1, g["y"] + 0.2, g["z0"] + 0.15)
    steel.box(gx0, g["y"] + 0.12, g["z1"] - 0.15, gx1, g["y"] + 0.2, g["z1"] - 0.05)
    pitch = 0.29
    x = gx0 + 0.02
    while x + 0.125 < gx1:
        cedar_z.box(x, g["y"] + 0.02, g["z0"] + 0.15, x + 0.125, g["y"] + 0.31, g["z1"] - 0.15)
        x += pitch
    # brass pull
    steel.box(gx0 + 0.25, g["y"] - 0.12, D.FF + 3.0, gx0 + 0.32, g["y"] - 0.05, D.FF + 6.0, mat=1)

    # cedar screen between the carport and the courtyard, with the side gate (D15) in it
    s = D.CEDAR_SCREEN
    sw, sd, gap = s["slat_w"], s["slat_d"], s["gap"]
    ops = s.get("openings", [])
    z0, z1 = s["z0"] + 0.1, s["z1"] - 0.02
    _slats_y(cedar_z, s["x"], s["y0"], s["y1"], z0, z1, sw, sd, gap, skip=ops)
    spans = []
    yy = s["y0"]
    for (a, b) in ops:
        spans.append((yy, a - 0.05))
        yy = b + 0.05
    spans.append((yy, s["y1"]))
    for (a, b) in spans:   # rails behind the slats (courtyard side), posts at the ends + every ~6 ft
        steel.box(s["x"], a, s["z0"] + 0.6, s["x"] + 0.12, b, s["z0"] + 0.75)
        steel.box(s["x"], a, s["z1"] - 1.0, s["x"] + 0.12, b, s["z1"] - 0.85)
        n = max(1, int(round((b - a) / 6.0)))
        for k in range(n + 1):
            py = min(a + k * (b - a) / n, b - 0.25)
            steel.box(s["x"], py, D.GRADE, s["x"] + 0.25, py + 0.25, s["z1"])
    steel.box(s["x"] - sd - 0.02, s["y0"], s["z1"] - 0.02, s["x"] + 0.12, s["y1"], s["z1"] + 0.06)
    cg = getattr(D, "CARPORT_GATE", None)
    if cg:   # side gate leaf, closed: the same slats on a bronze frame + a brass pull
        x = cg["x"]
        steel.box(x - sd, cg["y0"] + 0.05, cg["z0"] + 0.08, x, cg["y1"] - 0.05, cg["z0"] + 0.2)
        steel.box(x - sd, cg["y0"] + 0.05, cg["z1"] - 0.3, x, cg["y1"] - 0.05, cg["z1"] - 0.18)
        _slats_y(cedar_z, x, cg["y0"] + 0.08, cg["y1"] - 0.08, cg["z0"] + 0.2, cg["z1"] - 0.3, sw, sd, gap)
        steel.box(x + 0.02, cg["y1"] - 0.45, D.FF + 2.6, x + 0.08, cg["y1"] - 0.38, D.FF + 5.6, mat=1)
        steel.box(x - sd - 0.08, cg["y1"] - 0.45, D.FF + 2.6, x - sd - 0.02, cg["y1"] - 0.38, D.FF + 5.6, mat=1)
    for sc in getattr(D, "SLAT_SCREENS", []):
        top = s["z1"] - 0.02
        if sc["axis"] == "x":   # carport north: slats along x, posts at the ends + middle
            _slats_x(cedar_z, sc["y"], sc["x0"] + 0.35, sc["x1"] - 0.35, s["z0"] + 0.1, top, sw, sd, gap)
            for px in (sc["x0"] + 0.1, (sc["x0"] + sc["x1"]) / 2, sc["x1"] - 0.35):
                steel.box(px, sc["y"] + sd, D.GRADE, px + 0.25, sc["y"] + sd + 0.25, s["z1"])
            for zz in (s["z0"] + 0.6, s["z1"] - 1.0):
                steel.box(sc["x0"], sc["y"] + sd, zz, sc["x1"], sc["y"] + sd + 0.12, zz + 0.15)
            steel.box(sc["x0"], sc["y"] - 0.02, s["z1"] - 0.02, sc["x1"], sc["y"] + sd + 0.12, s["z1"] + 0.06)
        else:                   # courtyard east: slats along y on the lot's side-yard edge
            _slats_y(cedar_z, sc["x"], sc["y0"] + 0.3, sc["y1"] - 0.3, s["z0"] + 0.1, top, sw, sd, gap)
            for py in (sc["y0"] + 0.05, (sc["y0"] + sc["y1"]) / 2, sc["y1"] - 0.6):
                steel.box(sc["x"], py, D.GRADE, sc["x"] + 0.25, py + 0.25, s["z1"])
            for zz in (s["z0"] + 0.6, s["z1"] - 1.0):
                steel.box(sc["x"], sc["y0"], zz, sc["x"] + 0.12, sc["y1"] - 0.5, zz + 0.15)
            steel.box(sc["x"] - sd - 0.02, sc["y0"], s["z1"] - 0.02, sc["x"] + 0.12, sc["y1"] - 0.5, s["z1"] + 0.06)
    sl = getattr(D, "CARPORT_SLIDER", None)
    if sl and sl.get("installed", True):   # motorized sliding cedar gate, closed
        y = sl["y"]
        steel.box(sl["park_x0"] - 0.3, y - 0.05, sl["z0"] - 0.02, sl["x1"], y + 0.05, sl["z0"] + 0.04)   # ground track
        steel.box(sl["x0"] + 0.05, y - 0.15, sl["z0"] + 0.08, sl["x1"] - 0.05, y + 0.15, sl["z0"] + 0.24)
        steel.box(sl["x0"] + 0.05, y - 0.15, sl["z1"] - 0.32, sl["x1"] - 0.05, y + 0.15, sl["z1"] - 0.16)
        for ex in (sl["x0"] + 0.05, sl["x1"] - 0.2):
            steel.box(ex, y - 0.15, sl["z0"] + 0.08, ex + 0.15, y + 0.15, sl["z1"] - 0.16)
        x = sl["x0"] + 0.25
        while x + 0.125 < sl["x1"] - 0.2:
            cedar_z.box(x, y - 0.14, sl["z0"] + 0.24, x + 0.125, y + 0.14, sl["z1"] - 0.32)
            x += 0.29
        ri = getattr(D, "GATE_ROUGH_IN", None)
        if ri:   # gate operator on its pad, behind the cobogó
            mx0, my0, mx1, my1 = ri["motor_pad"]
            steel.box(mx0 + 0.35, my0 + 0.15, D.HARDSCAPE, mx1 - 0.35, my1 - 0.1, D.HARDSCAPE + 1.15)
    steel.build(coll, bevel=0.002)


# how far each door stands open in the renders (degrees; 90 = flat against the swing side)
DOOR_OPEN = {"Bed 2": 55, "Bed 3": 55, "Bath": 84, "Laundry": 70, "Primary": 75, "WIC": 80, "Primary bath": 86}


def _doors(L, coll):
    """Interior doors (V2): flush solid-core rift oak veneer leaves, painted flush jambs, brass
    levers; closets get bypass oak leaves. Swings follow the plan (hinge at the opening start,
    opening along the wall normal * swing)."""
    dm = MB("Interior doors", [L.get("oak_door", L["oak"]), L["paint"], L["brass"], L["black"]])
    t = D.INT_T
    for p in D.PARTITIONS:
        a = Vector(p["a"]); b = Vector(p["b"])
        Lp = (b - a).length
        u = (b - a) / Lp
        n = Vector((-u.y, u.x))
        for o in p["openings"]:
            s0, s1 = o["off"], o["off"] + o["w"]
            for (q0, q1) in ((s0, s0 + 0.06), (s1 - 0.06, s1)):
                x0, y0, x1, y1 = _rect(a, u, n, q0, q1, -t / 2, t / 2)
                dm.box(x0, y0, FF, x1, y1, FF + 8.0, mat=1)
            x0, y0, x1, y1 = _rect(a, u, n, s0, s1, -t / 2, t / 2)
            dm.box(x0, y0, FF + 7.94, x1, y1, FF + 8.0, mat=1)
            if o["kind"] == "closet":
                half = o["w"] / 2
                for k, dd in enumerate((-0.07, 0.07)):
                    q0 = s0 + 0.06 if k == 0 else s0 + half - 0.06
                    q1 = s0 + half + 0.06 if k == 0 else s1 - 0.06
                    x0, y0, x1, y1 = _rect(a, u, n, q0, q1, dd - 0.055, dd + 0.055)
                    dm.box(x0, y0, FF + 0.06, x1, y1, FF + 7.9, mat=0)
                    pq = q0 + 0.25 if k == 0 else q1 - 0.33
                    for side in (-1, 1):
                        x0, y0, x1, y1 = _rect(a, u, n, pq, pq + 0.08, dd + side * 0.055, dd + side * 0.065)
                        dm.box(x0, y0, FF + 3.2, x1, y1, FF + 4.4, mat=3)
                continue
            sw = o.get("swing", 1)
            ang = math.radians(o.get("open", DOOR_OPEN.get(o.get("name"), 82)))
            nn = n * sw
            hinge = a + u * (s0 + 0.06) + nn * (t / 2)
            lw = o["w"] - 0.12
            d = u * math.cos(ang) + nn * math.sin(ang)
            p0, p1 = hinge, hinge + d * lw
            _rot_box_m(dm, p0, p1, 0.146, FF + 0.04, FF + 7.92, 0)
            perp = Vector((-d.y, d.x))
            for side in (-1, 1):   # brass lever on both faces
                c0 = hinge + d * (lw - 0.62) + perp * (0.073 + side * 0.073 + side * 0.07)
                c1 = hinge + d * (lw - 0.2) + perp * (0.073 + side * 0.073 + side * 0.07)
                _rot_box_m(dm, c0, c1, 0.05, FF + 3.15, FF + 3.21, 2)
    dm.build(coll, bevel=0.003)


def _rot_box_m(mb, p0, p1, depth, z0, z1, mat):
    d = (p1 - p0)
    perp = Vector((-d.y, d.x)).normalized() * depth
    q = [p0, p1, p1 + perp, p0 + perp]
    verts = [(c.x, c.y, z0) for c in q] + [(c.x, c.y, z1) for c in q]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    if d.x * perp.y - d.y * perp.x < 0:
        faces = [tuple(reversed(f)) for f in faces]
    mb._add(verts, faces, [mat] * 6, random.random())


def _skylights(L, coll, roof_ob):
    """Cut each skylight through the roof plate; painted light well, membrane curb, bronze
    frame and a laminated glass lid (design.SKYLIGHTS)."""
    sk = getattr(D, "SKYLIGHTS", [])
    if not sk or roof_ob is None:
        return
    well = MB("Skylight wells", [L["paint"], L["roof"], L["bronze"]])
    lid = MB("Skylight glass", [L["glass"]])
    ft, curb = D.FASCIA_TOP, 0.42
    for k in sk:
        x0, y0, x1, y1 = k["rect"]
        cm = MB("cut", [L["paint"]])
        cm.box(x0, y0, D.CEIL - 1.0, x1, y1, ft + 2.0)
        cut = cm.build(coll)
        cut.hide_render = cut.hide_viewport = True
        mod = roof_ob.modifiers.new("skylight", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cut
        w = 0.05
        for (a0, b0, a1, b1) in ((x0, y0, x0 + w, y1), (x1 - w, y0, x1, y1), (x0, y0, x1, y0 + w), (x0, y1 - w, x1, y1)):
            well.box(a0, b0, D.CEIL - 0.01, a1, b1, ft + curb, mat=0)
        c = 0.3   # curb, flashed with the roof membrane
        for (a0, b0, a1, b1) in ((x0 - c, y0 - c, x0, y1 + c), (x1, y0 - c, x1 + c, y1 + c),
                                 (x0, y0 - c, x1, y0), (x0, y1, x1, y1 + c)):
            well.box(a0, b0, ft - 0.02, a1, b1, ft + curb, mat=1)
        for (a0, b0, a1, b1) in ((x0 - c, y0 - c, x0 + 0.08, y1 + c), (x1 - 0.08, y0 - c, x1 + c, y1 + c),
                                 (x0, y0 - c, x1, y0 + 0.08), (x0, y1 - 0.08, x1, y1 + c)):
            well.box(a0, b0, ft + curb, a1, b1, ft + curb + 0.12, mat=2)
        lid.box(x0 + 0.02, y0 + 0.02, ft + curb + 0.02, x1 - 0.02, y1 - 0.02, ft + curb + 0.08)
    well.build(coll, bevel=0.002)
    lid.build(coll)


def _posts(L, coll):
    p = MB("Steel posts", [L["bronze"]])
    for (x, y) in D.POSTS:
        p.box(x - 0.17, y - 0.17, D.HARDSCAPE, x + 0.17, y + 0.17, D.CEIL)
    p.build(coll, bevel=0.003)


# --------------------------------------------------------------------------- hardscape
def _hardscape(L, coll):
    pv = MB("Limestone pavers", [L["pavers"], L["concrete"]])
    soil = MB("Courtyard soil", [L["mulch"], L["concrete"]])
    H = D.HARDSCAPE
    # courtyard platform (covered entry + L-shaped courtyard), retained by concrete curbs
    court = [p for p in D.OUTDOOR if p["name"].startswith("Pátio")][0]["poly"]
    entry = [p for p in D.OUTDOOR if p["name"] == "Covered entry"][0]["poly"]
    ex0, ey0 = entry[0]
    poly = [(ex0, ey0), (entry[1][0], ey0)] + [q for q in court if q[1] > 36.0 or q[0] > entry[1][0]]
    poly = [(26.0, 30.33), (48.5, 30.33), (48.5, 50.0), (59.5, 50.0), (59.5, 60.0), (26.0, 60.0)] \
        if len(poly) < 6 else poly
    soil.prism(poly, 0.0, H - 0.08, top=0, side=1, bottom=1)
    # carport slab at the courtyard level: level arrival, one level for the sliding gate track
    cp = getattr(D, "CARPORT", None)
    if cp:
        slab = MB("Carport slab", [L["concrete"]])
        slab.box(cp["x0"], cp["y0"], -0.3, cp["x1"], cp["y1"], H - 0.02)
        slab.build(coll, bevel=0.004)
    # black calçada portuguesa at the entry, framed by a light concrete band
    em = D.ENTRY_MOSAIC
    mo = MB("Entry mosaic", [L["calcada"], L["concrete"]])
    bd = em["band"]
    mo.box(em["x0"], em["y0"], H - 0.12, em["x1"], em["y1"], H - 0.002, mats6=[1, 1, 1, 1, 1, 1])
    mo.box(em["x0"] + bd, em["y0"] + bd, H - 0.1, em["x1"] - bd, em["y1"] - bd, H + 0.004,
           mats6=[1, 0, 1, 1, 1, 1])
    mo.build(coll)
    for pz in D.PAVING:
        x0, y0, x1, y1 = pz["rect"]
        if pz["name"] == "Veranda":
            pv.box(x0, y0, 0.0, x1, y1, H, mats6=[1, 0, 1, 1, 1, 1])
            pv.box(x0, y1, 0.0, x1, y1 + 1.3, H * 0.5, mats6=[1, 0, 1, 1, 1, 1])   # step
            continue
        for (a0, a1, b0, b1) in subtract_rect((x0, x1, y0, y1), (em["x0"], em["x1"], em["y0"], em["y1"])):
            pv.box(a0, b0, H - 0.12, a1, b1, H, mats6=[1, 0, 1, 1, 1, 1])
    # entry step outside the gate + front stepping slabs
    g = D.ENTRY_GATE
    pv.box(g["x0"] - 0.3, 27.6, 0.0, g["x1"] + 0.3, 29.95, H * 0.5)
    st = D.PATHS[0]
    y = st["y0"] + 0.4
    while y + st["d"] < 27.3:
        pv.box(st["x"] - st["w"] / 2, y, -0.05, st["x"] + st["w"] / 2, y + st["d"], 0.12)
        y += st["d"] + st["gap"]
    pv.build(coll, bevel=0.004)
    soil.build(coll)
