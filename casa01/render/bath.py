"""Bathroom build-outs from design.PRIMARY_BATH and design.HALL_BATH (V2).

Both baths share one language: concrete floor (the house slab), glazed zellige-look tile
only in the wet zone, a floating rift-oak vanity with a stone top, brushed brass, a
wall-hung wc and a skylight. Primary: green tile, curbless walk-in shower, round mirror.
Hall bath: terracotta tile around the house's one tub, fixed glass panel, pill mirror.
"""
import math

import bpy
import bmesh
from mathutils import Matrix

import design as D
from geo import MB, M, subtract_rect

FF, CEIL = D.FF, D.CEIL
T = 0.045   # tile layer thickness (ft)


def cyl(name, coll, mat, x, y, z0, z1, r, axis="Z", segs=40, bowl=0.0):
    """Cylinder in feet. axis X/Y/Z. bowl>0 hollows the top (vessel sink)."""
    bm = bmesh.new()
    h = (z1 - z0) * M
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r * M, radius2=r * M, depth=h)
    if bowl > 0:
        top = [f for f in bm.faces if f.normal.z > 0.9][0]
        bmesh.ops.inset_individual(bm, faces=[top], thickness=0.03 * M * 1.6)
        bmesh.ops.translate(bm, verts=top.verts, vec=(0, 0, -bowl * M))
        bmesh.ops.scale(bm, vec=(0.92, 0.92, 1.0), verts=top.verts, space=Matrix.Translation((0, 0, -h / 2)))
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    # smooth the round sides only: smoothing the flat caps bends their normals into a dome,
    # which turns a mirror into what looks like a polished brass bowl
    for poly in me.polygons:
        poly.use_smooth = len(poly.vertices) <= 4
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    if axis == "Z":
        ob.location = (x * M, y * M, (z0 + z1) / 2 * M)
    else:
        ob.location = (x * M, y * M, z0 * M)
    coll.objects.link(ob)
    return ob


def pill(name, coll, mat, cx, y_face, cz, w, h, depth, segs=24):
    """Stadium-shaped slab (pill mirror) on a wall facing -Y at y_face; feet."""
    r = w / 2
    pts = []
    for k in range(segs + 1):                      # top arc
        a = math.pi * k / segs
        pts.append((cx + r * math.cos(a), cz + h / 2 - r + r * math.sin(a)))
    for k in range(segs + 1):                      # bottom arc
        a = math.pi + math.pi * k / segs
        pts.append((cx + r * math.cos(a), cz - h / 2 + r + r * math.sin(a)))
    bm = bmesh.new()
    front = [bm.verts.new((x * M, (y_face - depth) * M, z * M)) for x, z in pts]
    back = [bm.verts.new((x * M, y_face * M, z * M)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:   # flat front/back (a true mirror plane), smooth rim
        poly.use_smooth = len(poly.vertices) == 4
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def basin(name, coll, mat, x0, y0, x1, y1, z0, z1, wall=0.08, depth=0.3, bevel=0.02):
    """Hollow rectangular basin (tub or vessel sink): a box with its top inset and pushed down."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=((x1 - x0) * M, (y1 - y0) * M, (z1 - z0) * M), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2 * M, (y0 + y1) / 2 * M, (z0 + z1) / 2 * M), verts=bm.verts)
    top = [f for f in bm.faces if f.normal.z > 0.9][0]
    bmesh.ops.inset_individual(bm, faces=[top], thickness=wall * M)
    bmesh.ops.inset_individual(bm, faces=[top], thickness=0.04 * M, depth=-0.04 * M)
    bmesh.ops.translate(bm, verts=top.verts, vec=(0, 0, -(depth - 0.04) * M))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if bevel:
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width = bevel * M
        b.segments = 3
        b.limit_method = "ANGLE"
    return ob


def globe(name, coll, mat, x, y, z, r=0.19):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r * M)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.materials.append(mat)
    g = bpy.data.objects.new(name, me)
    g.location = (x * M, y * M, z * M)
    coll.objects.link(g)
    return g


def _ext_hole(wid, s_to_xy):
    """Window holes (in the wall's own coordinate) for an exterior wall id."""
    w = [w for w in D.EXT_WALLS if w["id"] == wid][0]
    return [(o["off"], o["off"] + o["w"], FF + o["sill"], FF + o["head"]) for o in w["openings"]]


def _tile_x_wall(mb, x0, x1, y_face, side, z0, z1, holes=(), depth=T, mat=0):
    """Tile on a wall face parallel to X at y_face; side=-1 tile is south of the face."""
    for (a0, a1, b0, b1) in _sub_all((x0, x1, z0, z1), holes):
        mb.box(a0, y_face, b0, a1, y_face + side * depth, b1, mat=mat)


def _tile_y_wall(mb, y0, y1, x_face, side, z0, z1, holes=(), depth=T, mat=0):
    for (a0, a1, b0, b1) in _sub_all((y0, y1, z0, z1), holes):
        mb.box(x_face, a0, b0, x_face + side * depth, a1, b1, mat=mat)


def _sub_all(r, holes):
    rects = [r]
    for h in holes:
        rects = [q for rr in rects for q in subtract_rect(rr, h)]
    return [q for q in rects if q[1] - q[0] > 1e-3 and q[3] - q[2] > 1e-3]


def _towel_stack(mb, x0, y0, x1, y1, z, n=3, mat=0):
    """Folded towels: n slightly uneven soft slabs."""
    for k in range(n):
        inset = 0.02 * (k % 2)
        mb.box(x0 + inset, y0 + inset, z + k * 0.16, x1 - inset, y1 - inset * 2, z + k * 0.16 + 0.15, mat=mat)


# ------------------------------------------------------------------------- primary bath
def build_primary_bath(L, coll, protos=None):
    B = D.PRIMARY_BATH
    rx0, ry0, rx1, ry1 = B["room"]
    sx0, sy0, sx1, sy1 = B["shower"]
    # curbless shower: matte green mosaic floor flush with the concrete (slab recessed), slot drain
    fl = MB("Primary shower floor", [L["shower_mosaic"], L["brass"]])
    fl.box(sx0, sy0, FF - 0.05, sx1, sy1, FF + 0.006)
    if "drain" in B:
        dx0, dy, dx1 = B["drain"]
        fl.box(dx0, dy - 0.06, FF + 0.004, dx1, dy + 0.06, FF + 0.01, mat=1)
    fl.build(coll)

    z = MB("Shower zellige", [L["zellige"]])
    # north wall (exterior, inner face ry1) with the clerestory; east wall with the garden window
    nwin = [w for w in D.EXT_WALLS if w["id"] == "N-bar"][0]
    ax = nwin["a"][0]
    holes_n = [(ax - o["off"] - o["w"], ax - o["off"], FF + o["sill"], FF + o["head"]) for o in nwin["openings"]]
    _tile_x_wall(z, sx0, sx1, ry1, -1, FF, CEIL, holes_n)
    ewin = [w for w in D.EXT_WALLS if w["id"] == "E-bar"][0]
    ay = ewin["a"][1]
    holes_e = [(ay + o["off"], ay + o["off"] + o["w"], FF + o["sill"], FF + o["head"]) for o in ewin["openings"]]
    _tile_y_wall(z, sy0, sy1, rx1, -1, FF, CEIL, holes_e)
    # window returns (jambs, sill, head) tiled too, so the openings read as cut through the tile
    for (a0, a1, b0, b1) in holes_e:
        if a1 > sy0 and a0 < sy1:
            z.box(rx1 - 0.5, a0 - T, b0 - T, rx1, a0, b1 + T)
            z.box(rx1 - 0.5, a1, b0 - T, rx1, a1 + T, b1 + T)
            z.box(rx1 - 0.5, a0, b0 - T, rx1, a1, b0)
            z.box(rx1 - 0.5, a0, b1, rx1, a1, b1 + T)
    for (a0, a1, b0, b1) in holes_n:
        lo, hi = max(a0, sx0), min(a1, sx1)
        if hi > lo:
            z.box(lo, ry1, b0 - T, hi, ry1 + 0.5, b0)
            z.box(lo, ry1, b1, hi, ry1 + 0.5, b1 + T)
    _tile_y_wall(z, sy0, sy1, rx0, 1, FF, CEIL)                 # west end of the shower
    z.build(coll, bevel=0.001)

    # floating limestone bench + vanity top
    stone = MB("Bath limestone", [L["limestone"]])
    bx0, by0, bx1, by1 = B["bench"]
    stone.box(bx0, by0, FF + 1.35, bx1, by1, FF + 1.6)
    vx0, vy0, vx1, vy1 = B["vanity"]
    stone.box(vx0, vy0 - 0.05, FF + 2.55, vx1 + 0.1, vy1 + 0.05, FF + 2.7)
    stone.build(coll, bevel=0.004)

    # fixed glass panel (low-iron, 1/2") in slim brass channels
    gx0, gx1, gy = B["glass"]
    gl = MB("Shower glass", [L["glass"]])
    gl.box(gx0 + T, gy - 0.02, FF + 0.03, gx1, gy + 0.02, FF + 7.6)
    gl.build(coll)
    br = MB("Bath brass", [L["brass"], L["linen"]])
    br.box(gx0 + T, gy - 0.04, FF + 7.6, gx1 + 0.04, gy + 0.04, FF + 7.66)      # top channel
    br.box(gx1, gy - 0.04, FF + 0.01, gx1 + 0.04, gy + 0.04, FF + 7.66)         # free-edge trim
    br.box(gx0 + T, gy - 0.04, FF + 0.01, gx1, gy + 0.04, FF + 0.06)            # floor channel
    br.box(gx1 - 0.02, gy, FF + 7.6, gx1 + 0.02, sy1 - T, FF + 7.64)            # stabilizer bar to the wall
    # towel bar on the room side of the glass, with a linen towel over it
    tx = (gx0 + gx1) / 2
    br.box(tx - 0.6, gy - 0.16, FF + 4.15, tx + 0.6, gy - 0.12, FF + 4.2)
    br.box(tx - 0.45, gy - 0.2, FF + 2.9, tx + 0.45, gy - 0.08, FF + 4.25, mat=1)
    # rain head arm from the ceiling, valve trim on the west wall, wall faucet, flush plate
    hx, hy = B["rain_head"]
    br.box(hx - 0.03, hy - 0.03, FF + 7.95, hx + 0.03, hy + 0.03, CEIL)
    br.box(rx0 + T, hy - 0.2, FF + 3.9, rx0 + T + 0.03, hy + 0.2, FF + 4.3)
    sx, sy = B["sink"]
    br.box(rx0, sy - 0.04, FF + 3.55, rx0 + 0.62, sy + 0.04, FF + 3.62)
    br.box(rx0, sy - 0.32, FF + 3.4, rx0 + 0.08, sy - 0.24, FF + 3.48)
    br.box(rx0, sy + 0.24, FF + 3.4, rx0 + 0.08, sy + 0.32, FF + 3.48)
    wcs = [f for f in D.FURNITURE if f["t"] == "wc_wall"]
    wcy = wcs[0]["y"] if wcs else (ry0 + 1.5)
    br.box(rx1 - 0.03, wcy - 0.25, FF + 3.4, rx1, wcy + 0.25, FF + 3.7)
    br.build(coll, bevel=0.002)
    cyl("Rain head", coll, L["brass"], hx, hy, FF + 7.9, FF + 7.95, 0.42)

    # floating oak vanity with a drawer reveal + vessel sink
    oak = MB("Bath vanity", [L["oak"], L["black"]])
    oak.box(vx0, vy0, FF + 1.15, vx1, vy1, FF + 2.55)
    oak.box(vx1 - 0.005, vy0 + 0.1, FF + 1.88, vx1 + 0.002, vy1 - 0.1, FF + 1.9, mat=1)
    oak.build(coll, bevel=0.004)
    cyl("Vessel sink", coll, L["ceramic"], sx, sy, FF + 2.7, FF + 3.15, 0.62, bowl=0.38)

    # round mirror: thin brass ring behind silvered glass, two brass sconces with glass globes
    my, md = B["mirror"]
    rim = cyl("Mirror rim", coll, L["brass"], rx0, my, 0.0, 0.05, md / 2 + 0.07, axis="X", segs=64)
    rim.location = (rx0 * M, my * M, (FF + 5.3) * M)
    mir = cyl("Mirror", coll, L["mirror"], rx0, my, 0, 0.065, md / 2, axis="X", segs=64)
    mir.location = (rx0 * M, my * M, (FF + 5.3) * M)
    for yy in B["sconces"]:
        a = cyl("Sconce arm", coll, L["brass"], rx0, yy, 0, 0.32, 0.06, axis="X")
        a.location = (rx0 * M, yy * M, (FF + 5.4) * M)
        globe("Sconce globe", coll, L["lamp"], rx0 + 0.5, yy, FF + 5.4)

    # wall-hung wc on the east wall (14.5" wide, 21" projection)
    wc = MB("Bath wc", [L["ceramic"]])
    wc.box(rx1 - 1.75, wcy - 0.6, FF + 1.05, rx1, wcy + 0.6, FF + 1.42)
    wc.box(rx1 - 1.45, wcy - 0.45, FF + 0.95, rx1, wcy + 0.45, FF + 1.05)
    wc.build(coll, bevel=0.03)


# ------------------------------------------------------------------------- hall bath
def build_hall_bath(L, coll, protos=None):
    B = getattr(D, "HALL_BATH", None)
    if not B:
        return
    rx0, ry0, rx1, ry1 = B["room"]
    tx0, ty0, tx1, ty1 = B["tub"]
    rim = FF + 1.75
    # alcove: a short wall at the foot of the tub, open oak shelves behind it
    sh = B["shelf"]
    stub = MB("Hall bath tub wall", [L["paint"]])
    stub.box(sh[0], sh[1], FF, sh[2], sh[1] + D.INT_T, CEIL)
    stub.build(coll, bevel=0.003)
    foot = sh[1]

    z = MB("Hall bath terracotta tile", [L["zellige_terracotta"]])
    # tub apron (front), back wall above the rim (furred 4" for the niche), head + foot walls
    z.box(tx1 - 0.12, ty0, FF, tx1, foot, rim - 0.01)                       # tiled apron, flush with the rim
    nx, ny0, ny1, nz0, nz1 = B["niche"]
    fur = 0.3
    for (a0, a1, b0, b1) in _sub_all((ty0, foot, rim, CEIL), [(ny0, ny1, FF + nz0, FF + nz1)]):
        z.box(tx0, a0, b0, tx0 + fur, a1, b1)
    z.box(tx0, ny0, FF + nz0, tx0 + 0.05, ny1, FF + nz1)                    # niche back
    _tile_x_wall(z, tx0, tx1, ty0, 1, FF, CEIL)                              # head wall (south)
    _tile_x_wall(z, tx0, tx1, foot, -1, FF, CEIL)                            # foot wall (stub)
    z.box(tx1 - 0.02, foot, FF, tx1 + 0.02 + T, foot + D.INT_T, CEIL)       # wrap the stub's end
    z.build(coll, bevel=0.0008)

    # the tub: white enameled steel, set into the tiled alcove (rim lip over the tile apron)
    basin("Hall bath tub", coll, L["ceramic"], tx0 + fur - 0.02, ty0 + T, tx1 - 0.12, foot - T, FF + 0.2, rim,
          wall=0.22, depth=1.25, bevel=0.05)

    # fixed glass panel at the shower (head) end, brass wall channel + top stabilizer
    gx, gy0, gy1 = B["glass"]
    gl = MB("Hall bath glass", [L["glass"]])
    gl.box(gx - 0.12, gy0 + T, rim + 0.01, gx - 0.08, gy1, rim + 5.9)
    gl.build(coll)
    br = MB("Hall bath brass", [L["brass"], L["linen"], L["olive_fabric"]])
    br.box(gx - 0.14, gy0 + T, rim, gx - 0.06, gy0 + T + 0.04, rim + 5.95)
    br.box(gx - 0.12, gy1 - 0.02, rim + 5.85, tx0 + fur, gy1 + 0.02, rim + 5.89)     # stabilizer bar to the wall
    # shower head on an arm, valve trim, tub spout (head wall), centered on the tub
    cx = (tx0 + fur + tx1) / 2
    br.box(cx - 0.03, ty0 + T, FF + 6.9, cx + 0.03, ty0 + T + 0.7, FF + 6.96)
    br.box(cx - 0.18, ty0 + T, FF + 4.0, cx + 0.18, ty0 + T + 0.03, FF + 4.4)
    br.box(cx - 0.05, ty0 + T, rim + 0.35, cx + 0.05, ty0 + T + 0.5, rim + 0.45)
    # wall faucet over the vessel sink, flush plate, towel hook + towel by the tub
    sx, sy = B["sink"]
    br.box(sx - 0.04, ry1 - 0.62, FF + 3.55, sx + 0.04, ry1, FF + 3.62)
    br.box(sx - 0.32, ry1 - 0.08, FF + 3.4, sx - 0.24, ry1, FF + 3.48)
    br.box(sx + 0.24, ry1 - 0.08, FF + 3.4, sx + 0.32, ry1, FF + 3.48)
    wx, wy = B["wc"]
    br.box(wx - 0.25, ry0, FF + 3.4, wx + 0.25, ry0 + 0.03, FF + 3.7)
    # bath mat
    br.box(tx1 + 0.25, 43.9, FF, tx1 + 1.75, 46.2, FF + 0.03, mat=2)
    br.build(coll, bevel=0.004)
    cyl("Hall shower head", coll, L["brass"], cx, ty0 + T + 0.7, FF + 6.75, FF + 6.9, 0.3)

    # open oak shelves with folded towels in the alcove beside the tub
    oak = MB("Hall bath oak", [L["oak"], L["linen"], L["terracotta_fabric"]])
    for zz in (FF + 1.4, FF + 3.1, FF + 4.8):
        oak.box(sh[0] + 0.05, foot + D.INT_T, zz, sh[2] - 0.02, sh[3] - 0.02, zz + 0.1)
    for zz, m in ((FF + 1.5, 1), (FF + 3.2, 1), (FF + 4.9, 2)):
        _towel_stack(oak, sh[0] + 0.4, foot + D.INT_T + 0.1, sh[0] + 1.6, sh[3] - 0.15, zz, n=2 if m == 2 else 3, mat=m)
    # floating rift-oak vanity (drawer reveal), honed limestone top, rectangular vessel
    vx0, vy0, vx1, vy1 = B["vanity"]
    oak.box(vx0, vy0, FF + 1.2, vx1, vy1, FF + 2.55)
    oak.build(coll, bevel=0.004)
    blk = MB("Hall bath vanity reveal", [L["black"]])
    blk.box(vx0 + 0.1, vy0 - 0.004, FF + 1.88, vx1 - 0.1, vy0 + 0.002, FF + 1.9)
    blk.build(coll)
    st = MB("Hall bath limestone", [L["limestone"]])
    st.box(vx0 - 0.03, vy0 - 0.06, FF + 2.55, vx1 + 0.03, vy1, FF + 2.7)
    st.build(coll, bevel=0.004)
    # rectangular ceramic vessel (the primary's is round)
    basin("Hall bath vessel", coll, L["ceramic"], sx - 0.75, sy - 0.48, sx + 0.75, sy + 0.42, FF + 2.7, FF + 3.12,
          wall=0.06, depth=0.33, bevel=0.03)

    # pill mirror with a brass rim, two brass sconces with glass globes
    mx, mw, mh = B["mirror"]
    mz = FF + 5.35
    pill("Hall mirror rim", coll, L["brass"], mx, ry1, mz, mw + 0.12, mh + 0.12, 0.05)
    pill("Hall mirror", coll, L["mirror"], mx, ry1 - 0.05, mz, mw, mh, 0.02)
    for xx in B["sconces"]:
        a = cyl("Hall sconce arm", coll, L["brass"], xx, ry1, 0, 0.32, 0.06, axis="Y")
        a.location = (xx * M, (ry1 - 0.16) * M, (FF + 5.7) * M)
        globe("Hall sconce globe", coll, L["lamp"], xx, ry1 - 0.5, FF + 5.7, r=0.17)

    # wall-hung wc on the south wall
    wc = MB("Hall bath wc", [L["ceramic"]])
    wc.box(wx - 0.6, ry0, FF + 1.05, wx + 0.6, ry0 + 1.75, FF + 1.42)
    wc.box(wx - 0.45, ry0, FF + 0.95, wx + 0.45, ry0 + 1.45, FF + 1.05)
    wc.build(coll, bevel=0.03)
    if protos and "vase" in protos:
        ob = protos["vase"].copy()
        coll.objects.link(ob)
        ob.location = ((vx1 - 0.35) * M, (vy0 + 0.9) * M, (FF + 2.7) * M)
        ob.scale = (0.7, 0.7, 0.7)
