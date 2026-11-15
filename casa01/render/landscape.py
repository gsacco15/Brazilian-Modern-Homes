"""Site, street, neighbors and Texas-native landscape."""
import math
import os
import random

import bpy
from mathutils import Vector

import design as D
import plants as P
from geo import MB, M, new_coll

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "models")


def append_objects(asset, names=None):
    path = os.path.join(ASSETS, asset, f"{asset}.blend")
    if not os.path.exists(path):
        return []
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if (names is None or n in names)]
    return [o for o in dst.objects if o is not None]


def proto_collection(name, objs, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    for o in objs:
        c.objects.link(o)
        o.location = (0, 0, 0)
    return c


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xi:
                inside = not inside
    return inside


def sample_poly(poly, n, rng, avoid=(), min_d=0.0, pts_existing=None):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    out = []
    tries = 0
    while len(out) < n and tries < n * 60:
        tries += 1
        x = rng.uniform(min(xs), max(xs))
        y = rng.uniform(min(ys), max(ys))
        if not point_in_poly(x, y, poly):
            continue
        if any(ax0 <= x <= ax1 and ay0 <= y <= ay1 for (ax0, ay0, ax1, ay1) in avoid):
            continue
        if min_d > 0:
            if any((x - px) ** 2 + (y - py) ** 2 < min_d ** 2 for (px, py) in out + (pts_existing or [])):
                continue
        out.append((x, y))
    return out


def build_site(L, coll, protos):
    rng = random.Random(5)
    g = MB("Ground", [L["lawn_soil"], L["dg"], L["sidewalk"], L["asphalt"], L["concrete"], L["mulch"]])
    # base ground (lawns / neighbors) north of the curb and across the street
    g.box(-220, -11.0, -0.3, 285, 330, -0.02, mats6=[0, 0, 0, 0, 0, 0])
    g.box(-220, -260, -0.3, 285, -48.0, -0.02, mats6=[0, 0, 0, 0, 0, 0])
    # street + curbs + sidewalks
    g.box(-220, -47.5, -0.8, 285, -11.5, -0.5, mats6=[3, 3, 3, 3, 3, 3])
    g.box(-220, -11.5, -0.8, 285, -11.0, 0.02, mat=4)
    g.box(-220, -48.0, -0.8, 285, -47.5, 0.02, mat=4)
    g.box(-220, -5.0, -0.1, 285, -0.5, 0.04, mat=2)
    g.box(-220, -58.0, -0.1, 285, -53.5, 0.04, mat=2)
    # front yard decomposed granite & driveway ribbons
    g.box(0.0, -0.5, -0.1, 54.0, 27.0, 0.0, mats6=[1, 1, 1, 1, 1, 1])
    g.box(54.0, -0.5, -0.1, 65.0, 125.0, 0.0, mats6=[1, 1, 1, 1, 1, 1])
    g.box(0.0, 27.0, -0.1, 6.0, 125.0, 0.0, mats6=[1, 1, 1, 1, 1, 1])
    for (sx0, sx1) in D.DRIVEWAY["strips"]:
        g.box(sx0, D.DRIVEWAY["y0"], -0.1, sx1, D.DRIVEWAY["y1"], 0.05, mat=4)
    # rear: buffalo-grass lawn ground under the oak, DG paths
    g.box(6.0, 92.5, -0.1, 54.0, 125.0, -0.005, mats6=[0, 0, 0, 0, 0, 0])
    g.build(coll)

    _fences(L, coll)
    _neighbors(L, coll)
    _trees(L, coll)
    _planting(L, coll, protos, rng)


def _fences(L, coll):
    f = MB("Cedar fences", [L["fence"], L["black"]])
    bh, gap = 5.5 / 12, 0.6 / 12
    for (a, b) in D.FENCES:
        a = Vector(a); b = Vector(b)
        horiz = abs(a.y - b.y) < 1e-6
        z = 0.15
        while z + bh < D.FENCE_H:
            if horiz:
                f.box(min(a.x, b.x), a.y - 0.06, z, max(a.x, b.x), a.y + 0.06, z + bh, mat=0)
            else:
                f.box(a.x - 0.06, min(a.y, b.y), z, a.x + 0.06, max(a.y, b.y), z + bh, mat=0)
            z += bh + gap
        L_ = (b - a).length
        for k in range(int(L_ / 8) + 1):
            p = a + (b - a) * (k * 8 / L_)
            f.box(p.x - 0.15, p.y - 0.15, 0, p.x + 0.15, p.y + 0.15, D.FENCE_H + 0.1, mat=1)
    f.build(coll, bevel=0.002)


def _neighbors(L, coll):
    nb = MB("Neighbors", [L["house_beige"], L["house_roof"], L["glass"], L["bronze"]])
    for (x0, y0, x1, y1, ridge) in ((-46, 32, -12, 78, 17.0), (78, 30, 112, 74, 16.0),
                                    (-46, -150, -10, -100, 16), (20, -150, 58, -102, 17), (80, -150, 115, -100, 16)):
        nb.box(x0, y0, 0, x1, y1, 10.0, mat=0)
        # hipped roof as a truncated pyramid
        inset = 6.0
        pts = [(x0 - 1.5, y0 - 1.5, 10), (x1 + 1.5, y0 - 1.5, 10), (x1 + 1.5, y1 + 1.5, 10), (x0 - 1.5, y1 + 1.5, 10),
               (x0 + inset, y0 + inset, ridge), (x1 - inset, y0 + inset, ridge), (x1 - inset, y1 - inset, ridge),
               (x0 + inset, y1 - inset, ridge)]
        faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)]
        nb._add(pts, faces, [1] * 6, 0.5)
        # a few dark windows facing the street side
        face_y = y0 if y0 > 0 else y1
        sgn = -1 if y0 > 0 else 1
        for k in range(3):
            wx = x0 + 5 + k * (x1 - x0 - 10) / 2
            nb.box(wx - 2, face_y + sgn * 0.05 - 0.05, 3.0, wx + 2, face_y + sgn * 0.05 + 0.05, 7.5, mat=3)
    nb.build(coll)


def _trees(L, coll):
    leafc = bpy.data.collections.new("proto_leaf")
    bpy.context.scene.collection.children.link(leafc)
    lf = P.leaf_mesh("oak_leaf", leafc, L["leaf"], length=0.085, width=0.038)
    lf2 = P.leaf_mesh("oak_leaf_b", leafc, L["leaf"], length=0.06, width=0.03, bend=0.4)
    trees = list(D.TREES) + [
        dict(kind="live_oak", x=-22, y=14, h=30, spread=40, seed=23),
        dict(kind="live_oak", x=88, y=12, h=27, spread=36, seed=29),
        dict(kind="live_oak", x=-16, y=104, h=34, spread=46, seed=31),
        dict(kind="live_oak", x=84, y=108, h=32, spread=44, seed=37),
        dict(kind="live_oak", x=-30, y=-62, h=30, spread=40, seed=41),
        dict(kind="live_oak", x=70, y=-64, h=26, spread=34, seed=43),
        # neighborhood canopy beyond the fences
        dict(kind="live_oak", x=8, y=150, h=36, spread=50, seed=51, leaf=0.7),
        dict(kind="live_oak", x=52, y=158, h=40, spread=56, seed=53, leaf=0.7),
        dict(kind="live_oak", x=-40, y=140, h=32, spread=44, seed=57, leaf=0.7),
        dict(kind="live_oak", x=100, y=145, h=34, spread=46, seed=59, leaf=0.7),
        dict(kind="live_oak", x=-60, y=60, h=30, spread=40, seed=61, leaf=0.7),
        dict(kind="live_oak", x=125, y=60, h=30, spread=40, seed=67, leaf=0.7),
    ]
    for t in trees:
        P.live_oak(f"oak_{t['seed']}", (t["x"] * M, t["y"] * M, 0.0 if t["y"] < 28 or t["y"] > 92 else D.HARDSCAPE * M - 0.05),
                   t["h"] * M, t["spread"] * M, t["seed"], coll, L["bark"], leafc,
                   leaf_density=t.get("leaf", 1.0), crown_base=t.get("crown", 0.2))
    lc = bpy.context.view_layer.layer_collection.children[leafc.name]
    lc.exclude = True


def _planting(L, coll, protos, rng):
    feather = bpy.data.collections.new("proto_feather")
    muhly = bpy.data.collections.new("proto_muhly")
    agv = bpy.data.collections.new("proto_agave")
    sot = bpy.data.collections.new("proto_sotol")
    palm = bpy.data.collections.new("proto_palmetto")
    for c in (feather, muhly, agv, sot, palm):
        bpy.context.scene.collection.children.link(c)
    for i in range(4):
        P.grass_clump(f"feather_{i}", feather, L["feather"], seed=i, blades=110, height=0.62, spread=0.42,
                      width=0.0035, droop=0.9)
        P.grass_clump(f"muhly_{i}", muhly, L["grass"], seed=10 + i, blades=90, height=0.85, spread=0.35,
                      width=0.006, droop=0.5)
        P.agave(f"agave_{i}", agv, L["agave"], seed=20 + i, n_leaves=24 + 3 * i, length=0.62 + 0.08 * i)
        P.sotol(f"sotol_{i}", sot, L["grass"], seed=30 + i)
        P.palmetto(f"palmetto_{i}", palm, L["palm"], seed=40 + i)
    for c in (feather, muhly, agv, sot, palm):
        bpy.context.view_layer.layer_collection.children[c.name].exclude = True

    to_m = lambda pts, z=0.0: [(x * M, y * M, z) for x, y in pts]
    path_avoid = [(28.5, -1, 33.5, 28.5)]
    # front meadow: feather grass drifts + muhly + agave + sotol + boulders
    fm = D.PLANTING[0]["poly"]
    fe = D.PLANTING[1]["poly"]
    pts_ag = sample_poly(fm, 7, rng, path_avoid, 5.5) + sample_poly(fe, 5, rng, path_avoid + [(44, 0, 56, 27)], 5.5)
    pts_so = sample_poly(fm, 4, rng, path_avoid, 7.0, pts_ag) + sample_poly(fe, 3, rng, path_avoid, 7.0, pts_ag)
    used = pts_ag + pts_so
    pts_fe = []
    for poly in (fm, fe):
        pts_fe += sample_poly(poly, 300, rng, path_avoid + [(-1, -1, 9, 18)], 1.55, used)
    pts_mu = sample_poly([(33, 22), (54, 22), (54, 27), (33, 27)], 26, rng, (), 1.6) + \
        sample_poly([(0.5, 22), (27.5, 22), (27.5, 27), (0.5, 27)], 30, rng, (), 1.6)
    P.scatter("Front agave", to_m(pts_ag), agv, coll, scale=(0.9, 1.4))
    P.scatter("Front sotol", to_m(pts_so), sot, coll, scale=(0.9, 1.3))
    P.scatter("Front feather grass", to_m(pts_fe), feather, coll, scale=(0.6, 1.1))
    P.scatter("Front muhly", to_m(pts_mu), muhly, coll, scale=(0.8, 1.2))
    if "lawn" in protos:
        greens = []
        for poly in (fm, fe):
            greens += sample_poly(poly, 260, rng, path_avoid, 0.0)
        P.scatter("Front green tufts", to_m(greens, -0.02), protos["lawn"], coll, scale=(1.2, 2.2))
    if "boulder" in protos:
        P.scatter("Front boulders", to_m([(20.5, 14.0), (36.5, 9.0), (38.0, 11.5), (11.0, 22.0)], -0.12),
                  protos["boulder"], coll, scale=(0.45, 0.8))
    if "shrub" in protos:
        sh = [(1.5 + k * 2.6, 0.9 + rng.uniform(-0.3, 0.3)) for k in range(0)] + \
             [(0.8, y) for y in (4, 8, 12, 16, 20, 24)] + [(64.0, y) for y in (30, 34)]
        P.scatter("Front shrubs", to_m(sh), protos["shrub"], coll, scale=(1.4, 2.0))

    # courtyard: dwarf palmetto, ferns in the shade, muhly along the cobogó, agave accents
    zc = (D.HARDSCAPE - 0.08) * M
    cy = [(31.6, 36.6), (53.5, 36.6), (53.5, 49.0), (39.5, 49.0), (39.5, 56.3), (31.6, 56.3)]
    tree_avoid = [(42.2, 44.8, 45.8, 48.2)]
    pts_pa = sample_poly(cy, 11, rng, tree_avoid, 3.2)
    pts_fn = sample_poly([(31.6, 38), (36.5, 38), (36.5, 56), (31.6, 56)], 26, rng, (), 1.5, pts_pa)
    pts_mu2 = sample_poly([(32, 36.6), (53.4, 36.6), (53.4, 39.0), (32, 39.0)], 16, rng, (), 1.5)
    pts_ag2 = [(50.5, 49.0), (47.8, 41.0)]
    P.scatter("Courtyard palmetto", to_m(pts_pa, zc), palm, coll, scale=(1.1, 1.6))
    if "fern" in protos:
        P.scatter("Courtyard ferns", to_m(pts_fn, zc), protos["fern"], coll, scale=(0.9, 1.4))
    P.scatter("Courtyard muhly", to_m(pts_mu2, zc), muhly, coll, scale=(0.8, 1.1))
    P.scatter("Courtyard agave", to_m(pts_ag2, zc), agv, coll, scale=(1.0, 1.2))

    # rear: buffalo grass lawn clumps + native beds along the fence
    if "lawn" in protos:
        lawn_pts = sample_poly([(7, 94.2), (53, 94.2), (53, 124.2), (7, 124.2)], 5200, rng,
                               [(29.0, 108.0, 33.0, 112.0)], 0.0)
        P.scatter("Rear lawn", to_m(lawn_pts, -0.02), protos["lawn"], coll, scale=(1.1, 1.9))
        park = sample_poly([(-30, -10.8), (95, -10.8), (95, -5.2), (-30, -5.2)], 2400, rng, [(55, -11, 64, -5)], 0.0)
        P.scatter("Parkway lawn", to_m(park, -0.02), protos["lawn"], coll, scale=(1.1, 1.9))
    bed = sample_poly([(1, 94), (6, 94), (6, 124), (1, 124)], 30, rng, (), 1.4) + \
        sample_poly([(54.5, 62), (64, 62), (64, 124), (54.5, 124)], 70, rng, (), 1.4)
    P.scatter("Rear muhly", to_m(bed), muhly, coll, scale=(0.9, 1.3))
    if "shrub" in protos:
        sb = sample_poly([(1, 32), (5.5, 32), (5.5, 92), (1, 92)], 12, rng, (), 4.0)
        P.scatter("Side shrubs", to_m(sb), protos["shrub"], coll, scale=(1.3, 1.9))
