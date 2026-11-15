"""Furniture, fixtures and lighting fixtures (positions from design.FURNITURE)."""
import math
import random

import bpy
from mathutils import Vector

import design as D
from geo import MB, M

FF = D.FF
# Poly Haven seating faces -Y at rotation 0; angle that makes it face n/s/e/w
FACE_ANGLE = {"n": math.pi, "s": 0.0, "e": math.pi / 2, "w": -math.pi / 2}


def ground_z(y):
    if y > 93.5:
        return 0.0
    return D.HARDSCAPE if y > 80 else FF


def place(proto, x, y, z, rot, coll, scale=1.0):
    """linked duplicate of a prototype object (feet -> meters)."""
    ob = proto.copy()
    coll.objects.link(ob)
    ob.location = (x * M, y * M, z * M)
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (scale, scale, scale)
    return ob


def build_furniture(L, coll, protos):
    oak = MB("Oak millwork", [L["oak"], L["granite"], L["tile"], L["bronze"]])
    soft = MB("Upholstery", [L["linen"], L["oak"], L["olive_fabric"], L["terracotta_fabric"], L["rug"]])
    wood = MB("Walnut furniture", [L["dark_wood"], L["black"], L["leather"]])
    cer = MB("Ceramic fixtures", [L["ceramic"], L["bronze"], L["glass"]])
    stone = MB("Grill limestone", [L["limestone"], L["granite"], L["black"]])
    outdoor = MB("Outdoor teak", [L["cedar_x"], L["linen"]])
    rng = random.Random(3)
    for it in D.FURNITURE:
        t = it["t"]
        x, y = it["x"], it["y"]
        w, d = it.get("w", 2), it.get("d", 2)
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - d / 2, y + d / 2
        if t == "counter":
            oak.box(x0 + 0.08, y0 + 0.08, FF, x1 - 0.08, y1 - 0.08, FF + 0.35, mat=3)   # toe kick
            # door / drawer fronts with shadow gaps
            long_x = w > d
            n = max(1, int((w if long_x else d) / 2.0))
            for k in range(n):
                if long_x:
                    a0 = x0 + k * w / n + 0.01; a1 = x0 + (k + 1) * w / n - 0.01
                    oak.box(a0, y0, FF + 0.35, a1, y1, FF + 2.92, mat=0)
                else:
                    a0 = y0 + k * d / n + 0.01; a1 = y0 + (k + 1) * d / n - 0.01
                    oak.box(x0, a0, FF + 0.35, x1, a1, FF + 2.92, mat=0)
            oak.box(x0 - 0.02, y0 - 0.02, FF + 2.92, x1 + 0.02, y1 + 0.02, FF + 3.05, mat=1)
            # green glazed tile backsplash on the wall behind
            if long_x:
                oak.box(x0, y1 - 0.05, FF + 3.05, x1, y1 + 0.02, FF + 3.6, mat=2)
            else:
                oak.box(x0 - 0.02, y0, FF + 3.05, x0 + 0.05, y1, FF + 5.2, mat=2)
                oak.box(x0, y0 + 2.0, FF + 5.5, x0 + 1.0, y1 - 1.0, FF + 5.62, mat=0)   # floating shelf
        elif t == "tall":
            oak.box(x0, y0, FF, x1, y1, FF + 8.0, mat=0)
            oak.box(x1 - 0.02, y0 + 0.4, FF + 3.0, x1 + 0.06, y0 + 0.47, FF + 6.0, mat=3)
        elif t == "island":
            oak.box(x0 + 0.15, y0 + 0.3, FF, x1 - 0.15, y1 - 0.05, FF + 2.92, mat=0)
            oak.box(x0, y0, FF + 2.92, x1, y1, FF + 3.05, mat=1)
            oak.box(x0, y0, FF, x0 + 0.13, y1, FF + 2.92, mat=1)      # waterfall ends
            oak.box(x1 - 0.13, y0, FF, x1, y1, FF + 2.92, mat=1)
        elif t == "stool":
            wood.box(x - 0.6, y - 0.6, FF + 2.1, x + 0.6, y + 0.6, FF + 2.25, mat=2)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    wood.box(x + sx * 0.45 - 0.04, y + sy * 0.45 - 0.04, FF, x + sx * 0.45 + 0.04,
                             y + sy * 0.45 + 0.04, FF + 2.1, mat=1)
            wood.box(x - 0.5, y - 0.5, FF + 0.8, x + 0.5, y + 0.5, FF + 0.85, mat=1)
        elif t in ("dining_table", "outdoor_table"):
            top = FF + 2.45 if t == "dining_table" else D.HARDSCAPE + 2.45
            base = FF if t == "dining_table" else D.HARDSCAPE
            tm = wood if t == "dining_table" else outdoor
            tm.box(x0, y0, top, x1, y1, top + 0.14, mat=0)
            for sx in (x0 + 0.6, x1 - 0.9):
                tm.box(sx, y0 + 0.35, base, sx + 0.3, y1 - 0.35, top, mat=0)
            nch = it.get("chairs", 6)
            per = nch // 2
            for k in range(per):
                cx = x0 + (k + 0.5) * w / per
                if t == "dining_table" and "chair" in protos:
                    place(protos["chair"], cx, y0 - 0.7, base, FACE_ANGLE["n"], coll)
                    place(protos["chair"], cx, y1 + 0.7, base, FACE_ANGLE["s"], coll)
                else:
                    _chair(outdoor, cx, y0 - 0.85, base, "n")
                    _chair(outdoor, cx, y1 + 0.85, base, "s")
        elif t == "pendant":
            if "pendant" in protos:
                for dx in (-1.6, 1.6):
                    place(protos["pendant"], x + dx, y, D.CEIL - 3.15, 0, coll, scale=1.0)
                # pendants over the island too
                place(protos["pendant"], 12.5, 71.6, D.CEIL - 3.1, 0, coll, scale=0.9)
                place(protos["pendant"], 16.5, 71.6, D.CEIL - 3.1, 0, coll, scale=0.9)
        elif t == "rug":
            soft.box(x0, y0, FF, x1, y1, FF + 0.04, mat=4)
        elif t == "sofa":
            # low modern sofa: oak plinth, linen box, three seat + back cushions
            base = FF + 0.3
            soft.box(x0 + 0.1, y0 + 0.1, FF, x1 - 0.1, y1 - 0.1, base, mat=1)
            soft.box(x0, y0, base, x1, y1, base + 0.75, mat=0)
            back_x0 = x1 - 0.75 if it.get("face") == "w" else x0
            soft.box(back_x0, y0, base + 0.75, back_x0 + 0.75, y1, base + 2.0, mat=0)
            for k in range(3):
                a0 = y0 + 0.55 + k * (d - 1.1) / 3 + 0.03
                a1 = y0 + 0.55 + (k + 1) * (d - 1.1) / 3 - 0.03
                soft.box(x0 + 0.1, a0, base + 0.75, x1 - 0.8, a1, base + 1.15, mat=0, r=rng.random())
                soft.box(x1 - 1.25, a0 + 0.05, base + 1.1, x1 - 0.78, a1 - 0.05, base + 2.3, mat=0)
            soft.box(x0, y0, base + 0.75, x1, y0 + 0.5, base + 1.55, mat=0)
            soft.box(x0, y1 - 0.5, base + 0.75, x1, y1, base + 1.55, mat=0)
            # throw pillows
            soft.box(x1 - 1.35, y0 + 0.7, base + 1.15, x1 - 1.0, y0 + 2.0, base + 2.25, mat=3)
            soft.box(x1 - 1.35, y1 - 2.0, base + 1.15, x1 - 1.0, y1 - 0.7, base + 2.25, mat=2)
        elif t == "coffee_table":
            wood.box(x0, y0, FF + 1.0, x1, y1, FF + 1.25, mat=0)
            wood.box(x0 + 0.3, y0 + 0.3, FF, x1 - 0.3, y1 - 0.3, FF + 1.0, mat=0)
        elif t == "lounge_chair":
            key = "armchair" if y > 80 else "lounge"
            if key in protos:
                place(protos[key], x, y, ground_z(y), FACE_ANGLE[it.get("face", "n")], coll)
        elif t == "side_table":
            if "side_table" in protos:
                place(protos["side_table"], x, y, ground_z(y), 0, coll)
        elif t == "credenza":
            oak.box(x0, y0, FF + 0.5, x1, y1, FF + 2.6, mat=0)
            for k in range(4):
                oak.box(x0 + 0.05 + k * w / 4, y1 - 0.02, FF + 0.55, x0 + (k + 1) * w / 4 - 0.05, y1 + 0.01, FF + 2.55, mat=0)
            oak.box(x0 + 0.3, y0 + 0.2, FF, x0 + 0.42, y1 - 0.2, FF + 0.5, mat=3)
            oak.box(x1 - 0.42, y0 + 0.2, FF, x1 - 0.3, y1 - 0.2, FF + 0.5, mat=3)
            if "vase" in protos:
                place(protos["vase"], x0 + 1.2, y, FF + 2.6, 0, coll, scale=1.3)
        elif t == "planter":
            if "plant" in protos:
                place(protos["plant"], x, y, ground_z(y), rng.uniform(0, 6), coll, scale=1.5)
        elif t == "bed":
            hw, hd = (w / 2, d / 2)
            soft.box(x0, y0, FF, x1, y1, FF + 0.9, mat=1)
            soft.box(x0 + 0.1, y0 + 0.1, FF + 0.9, x1 - 0.1, y1 - 0.1, FF + 1.75, mat=0)
            soft.box(x1 - 0.25, y0 - 0.1, FF, x1, y1 + 0.1, FF + 3.6, mat=1)   # headboard (east)
            soft.box(x0 + 0.05, y0 + 0.05, FF + 1.75, x1 - 2.0, y1 - 0.05, FF + 1.9, mat=2)
            for py in (y0 + 0.5, y + 0.15):
                soft.box(x1 - 1.6, py, FF + 1.75, x1 - 0.35, py + d / 2 - 0.65, FF + 2.3, mat=0)
        elif t == "nightstand":
            oak.box(x - 0.9, y - 0.9, FF, x + 0.9, y + 0.9, FF + 1.9, mat=0)
        elif t in ("vanity",):
            oak.box(x0, y0, FF + 0.8, x1, y1, FF + 2.85, mat=0)
            cer.box(x0 - 0.03, y0 - 0.03, FF + 2.85, x1 + 0.03, y1 + 0.03, FF + 3.0, mat=0)
        elif t == "shower":
            cer.box(x0, y0, FF, x1, y1, FF + 0.08, mat=0)
            cer.box(x0, y0 - 0.02, FF, x0 + 0.03, y1, FF + 7.0, mat=2)
        elif t == "tub":
            cer.box(x0, y0, FF, x1, y1, FF + 1.7, mat=0)
        elif t == "wc":
            cer.box(x - 0.7, y - 0.95, FF, x + 0.7, y + 0.95, FF + 1.35, mat=0)
        elif t == "desk":
            oak.box(x0, y0, FF + 2.4, x1, y1, FF + 2.55, mat=0)
            oak.box(x0, y0, FF, x0 + 0.1, y1, FF + 2.4, mat=0)
            oak.box(x1 - 0.1, y0, FF, x1, y1, FF + 2.4, mat=0)
        elif t in ("washer", "dryer"):
            cer.box(x - 1.2, y - 1.3, FF, x + 1.2, y + 1.3, FF + 3.1, mat=0)
        elif t == "grill_counter":
            base = D.HARDSCAPE
            for k in range(4):   # limestone-clad block, coursed
                stone.box(x0, y0, base + k * 0.73, x1, y1, base + (k + 1) * 0.73 - 0.02, mat=0, r=rng.random())
            stone.box(x0 - 0.08, y0 - 0.08, base + 2.9, x1 + 0.08, y1 + 0.08, base + 3.05, mat=1)
            stone.box(x0 + 0.3, y0 + 1.0, base + 3.05, x1 - 0.3, y0 + 4.0, base + 3.2, mat=2)
        elif t == "fan":
            wood.box(x - 0.2, y - 0.2, D.CEIL - 1.0, x + 0.2, y + 0.2, D.CEIL, mat=1)
            for k in range(3):
                a = k * 2 * math.pi / 3 + 0.3
                cx, cy = x + math.cos(a) * 1.4, y + math.sin(a) * 1.4
                # blades approximated by small rotated boxes
                _blade(wood, x, y, a, D.CEIL - 1.0)
    oak.build(coll, bevel=0.003)
    soft.build(coll, bevel=0.035)
    wood.build(coll, bevel=0.004)
    cer.build(coll, bevel=0.01)
    stone.build(coll, bevel=0.004)
    outdoor.build(coll, bevel=0.004)

    # living-room extras: credenza, art, plants, vases
    ex = MB("Living extras", [L["oak"], L["terracotta_fabric"], L["olive_fabric"], L["linen"], L["black"]])
    # art canvas above the sofa (geometric color fields, Brazilian modernist palette)
    xa = 38.75
    ex.box(xa - 0.08, 66.5, FF + 4.4, xa, 73.5, FF + 8.2, mat=3)
    ex.box(xa - 0.1, 67.0, FF + 4.9, xa - 0.07, 69.4, FF + 7.7, mat=1)
    ex.box(xa - 0.1, 69.7, FF + 4.9, xa - 0.07, 73.0, FF + 6.2, mat=2)
    ex.box(xa - 0.1, 69.7, FF + 6.5, xa - 0.07, 73.0, FF + 7.7, mat=4)
    # second piece over the credenza (south wall of the dining zone)
    ex.box(15.2, 60.19, FF + 4.0, 20.8, 60.27, FF + 7.6, mat=3)
    for k, mt in enumerate((2, 1, 4)):
        ex.box(15.6 + k * 1.65, 60.26, FF + 4.4, 15.6 + k * 1.65 + 1.45, 60.3, FF + 7.2, mat=mt)
    ex.build(coll)
    if "plant" in protos:
        place(protos["plant"], 37.9, 61.6, FF, 0.6, coll, scale=1.7)
        place(protos["plant"], 29.3, 35.2, D.HARDSCAPE, 1.2, coll, scale=1.5)
        place(protos["plant"], 21.4, 91.0, D.HARDSCAPE, 2.0, coll, scale=1.4)
    if "vase" in protos:
        place(protos["vase"], 14.0, 71.4, FF + 3.05, 0, coll, scale=1.0)
        place(protos["vase"], 22.3, 72.0, FF + 2.59, 0, coll, scale=0.8)


def _blade(mb, x, y, a, z):
    import mathutils
    ln, wd = 2.3, 0.45
    d = Vector((math.cos(a), math.sin(a)))
    p = Vector((-d.y, d.x)) * wd / 2
    c0 = Vector((x, y)) + d * 0.25
    c1 = Vector((x, y)) + d * ln
    pts = [c0 - p, c1 - p, c1 + p, c0 + p]
    v = [(q.x, q.y, z) for q in pts] + [(q.x, q.y, z + 0.04) for q in pts]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mb._add(v, f, [1] * 6, 0.5)


def _chair(mb, x, y, base, face):
    """Simple teak dining chair with a cream cushion. face = direction the sitter faces."""
    w, d = 1.75, 1.8
    sy = 1 if face == "n" else -1        # back is on the side opposite the facing direction
    x0, x1 = x - w / 2, x + w / 2
    y0, y1 = y - d / 2, y + d / 2
    for (lx, ly) in ((x0 + 0.08, y0 + 0.08), (x1 - 0.2, y0 + 0.08), (x0 + 0.08, y1 - 0.2), (x1 - 0.2, y1 - 0.2)):
        mb.box(lx, ly, base, lx + 0.12, ly + 0.12, base + 1.45, mat=0)
    mb.box(x0, y0, base + 1.3, x1, y1, base + 1.45, mat=0)
    mb.box(x0 + 0.06, y0 + 0.06, base + 1.45, x1 - 0.06, y1 - 0.06, base + 1.65, mat=1)
    by0 = y0 if sy > 0 else y1 - 0.14
    for (lx,) in ((x0 + 0.08,), (x1 - 0.2,)):
        mb.box(lx, by0, base + 1.45, lx + 0.12, by0 + 0.14, base + 2.9, mat=0)
    for k in range(4):
        z = base + 1.9 + k * 0.25
        mb.box(x0 + 0.08, by0, z, x1 - 0.08, by0 + 0.1, z + 0.16, mat=0)
