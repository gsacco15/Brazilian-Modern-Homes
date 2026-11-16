"""Primary bathroom build-out (design.PRIMARY_BATH): wet room, vanity, fixtures."""
import math

import bpy
import bmesh
from mathutils import Matrix

import design as D
from geo import MB, M

FF, CEIL = D.FF, D.CEIL


def cyl(name, coll, mat, x, y, z0, z1, r, axis="Z", segs=40, bowl=0.0):
    """Cylinder in feet. axis X/Y/Z. bowl>0 hollows the top (vessel sink)."""
    bm = bmesh.new()
    h = (z1 - z0) * M
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r * M, radius2=r * M, depth=h)
    if bowl > 0:
        top = [f for f in bm.faces if f.normal.z > 0.9][0]
        ret = bmesh.ops.inset_individual(bm, faces=[top], thickness=0.03 * M * 1.6)
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
    # which turned the mirror into what looked like a polished brass bowl
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


def build_primary_bath(L, coll, protos=None):
    B = D.PRIMARY_BATH
    rx0, ry0, rx1, ry1 = B["room"]
    sx0, sy0, sx1, sy1 = B["shower"]
    tile = MB("Bath floor tile", [L["ladrilho"]])
    tile.box(rx0, ry0, FF, rx1, ry1, FF + 0.03)
    tile.build(coll)

    z = MB("Shower zellige", [L["zellige"]])
    t = 0.045
    # north wall (exterior) with the high clerestory window x 47.0-52.5, sill FF+6, head FF+9
    wy = ry1 - t
    z.box(sx0, wy, FF + 0.03, sx1, ry1, FF + 6.0)
    z.box(sx0, wy, FF + 9.0, sx1, ry1, CEIL)
    z.box(sx0, wy, FF + 6.0, 47.0, ry1, FF + 9.0)
    z.box(52.5, wy, FF + 6.0, sx1, ry1, FF + 9.0)
    # east wall with the garden window y 76.9-79.2, sill FF+3.6
    ex = rx1 - t
    z.box(ex, sy0, FF + 0.03, rx1, 76.9, CEIL)
    z.box(ex, 79.2, FF + 0.03, rx1, sy1, CEIL)
    z.box(ex, 76.9, FF + 0.03, rx1, 79.2, FF + 3.6)
    z.box(ex, 76.9, FF + 9.0, rx1, 79.2, CEIL)
    # west wall of the shower
    z.box(rx0, sy0, FF + 0.03, rx0 + t, sy1, CEIL)
    z.build(coll, bevel=0.001)

    # floating limestone bench, glass panel + brass channels, towel bar + towel
    stone = MB("Bath limestone", [L["limestone"]])
    bx0, by0, bx1, by1 = B["bench"]
    stone.box(bx0, by0, FF + 1.35, bx1, by1, FF + 1.6)
    vx0, vy0, vx1, vy1 = B["vanity"]
    stone.box(vx0, vy0 - 0.05, FF + 2.55, vx1 + 0.1, vy1 + 0.05, FF + 2.7)
    stone.build(coll, bevel=0.004)

    gx0, gx1, gy = B["glass"]
    gl = MB("Shower glass", [L["glass"]])
    gl.box(gx0 + t, gy - 0.02, FF + 0.1, gx1, gy + 0.02, FF + 7.6)
    gl.build(coll)
    br = MB("Bath brass", [L["brass"], L["linen"]])
    br.box(gx0 + t, gy - 0.04, FF + 7.6, gx1 + 0.04, gy + 0.04, FF + 7.68)
    br.box(gx1, gy - 0.04, FF + 0.03, gx1 + 0.05, gy + 0.04, FF + 7.68)
    br.box(gx0 + t, gy - 0.04, FF + 0.03, gx1, gy + 0.04, FF + 0.1)
    # towel bar on the glass, outside face, and a folded linen towel over it
    br.box(48.9, gy - 0.16, FF + 4.15, 50.1, gy - 0.12, FF + 4.2)
    br.box(49.05, gy - 0.2, FF + 2.9, 49.95, gy - 0.08, FF + 4.25, mat=1)
    # rain head arm, faucet spout, flush plate
    hx, hy = B["rain_head"]
    br.box(hx - 0.03, hy - 0.03, FF + 7.95, hx + 0.03, hy + 0.03, CEIL)
    sx, sy = B["sink"]
    br.box(rx0, sy - 0.04, FF + 3.55, rx0 + 0.62, sy + 0.04, FF + 3.62)
    br.box(rx0, sy - 0.32, FF + 3.4, rx0 + 0.08, sy - 0.24, FF + 3.48)
    br.box(rx0, sy + 0.24, FF + 3.4, rx0 + 0.08, sy + 0.32, FF + 3.48)
    br.box(rx1 - 0.03, 73.0, FF + 3.4, rx1, 73.4, FF + 3.7)
    br.build(coll, bevel=0.002)
    cyl("Rain head", coll, L["brass"], hx, hy, FF + 7.9, FF + 7.95, 0.42)

    # floating oak vanity with a drawer reveal + vessel sink
    oak = MB("Bath vanity", [L["oak"], L["black"]])
    oak.box(vx0, vy0, FF + 1.15, vx1, vy1, FF + 2.55)
    oak.box(vx1 - 0.005, vy0 + 0.1, FF + 1.88, vx1 + 0.002, vy1 - 0.1, FF + 1.9, mat=1)
    oak.build(coll, bevel=0.004)
    cyl("Vessel sink", coll, L["ceramic"], sx, sy, FF + 2.7, FF + 3.15, 0.62, bowl=0.38)

    # round mirror with a brass rim, two brass sconces with glass globes
    my, md = B["mirror"]
    cyl("Mirror rim", coll, L["brass"], rx0, my, 0.0, 0.05, md / 2 + 0.07, axis="X")  # thin brass ring behind the glass
    rim = bpy.data.objects["Mirror rim"]
    rim.location = (rx0 * M, my * M, (FF + 5.3) * M)
    cyl("Mirror", coll, L["mirror"], rx0, my, 0, 0.065, md / 2, axis="X")
    mir = bpy.data.objects["Mirror"]
    mir.location = (rx0 * M, my * M, (FF + 5.3) * M)
    for yy in B["sconces"]:
        a = cyl("Sconce arm", coll, L["brass"], rx0, yy, 0, 0.32, 0.06, axis="X")
        a.location = (rx0 * M, yy * M, (FF + 5.4) * M)
        g = bpy.data.objects.new("Sconce globe", None)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.19 * M)
        me = bpy.data.meshes.new("globe")
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        me.materials.append(L["lamp"])
        g = bpy.data.objects.new("Sconce globe", me)
        g.location = ((rx0 + 0.5) * M, yy * M, (FF + 5.4) * M)
        coll.objects.link(g)

    # wall-hung wc
    wc = MB("Bath wc", [L["ceramic"]])
    wc.box(52.2, 72.88, FF + 1.05, rx1, 73.52, FF + 1.42)
    wc.box(52.55, 72.95, FF + 0.95, rx1, 73.45, FF + 1.05)
    wc.build(coll, bevel=0.03)
    if protos and "plant" in protos:
        px, py = B["plant"]
        ob = protos["plant"].copy()
        coll.objects.link(ob)
        ob.location = (px * M, py * M, FF * M)
        ob.scale = (0.9, 0.9, 0.9)
