"""Export a light, web-ready GLB of Casa 01 for the interactive viewer.

    python casa01/render/export_web.py   ->  casa01/lookbook/web/casa01.glb

Same architecture as the renders (house.py / furniture.py from design.py),
with web-weight landscape: low-poly trees, lighter plants, an alpha-cut
cobogó panel instead of 210 modeled blocks, and baked, colorized 512px maps.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, CASA)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import design as D  # noqa: E402
import materials as MAT  # noqa: E402
import plants as P  # noqa: E402
import house  # noqa: E402
import furniture  # noqa: E402
import landscape  # noqa: E402
from geo import MB, M, new_coll  # noqa: E402
import render as R  # noqa: E402

OUT_DIR = os.path.join(CASA, "lookbook", "web")
TEXOUT = os.path.join(HERE, "assets", "web_tex")

# web material: (texture folder or None, rotated grain, hex color, tile meters, roughness, metallic)
WEB = {
    "stucco": ("stucco", False, "#ECE6DB", 1.6, 0.9, 0.0),
    "paint": (None, False, "#EFECE6", 1, 0.9, 0.0),
    "limestone": ("limestone", False, "#D9CBAE", 1.4, 0.85, 0.0),
    "mortar": (None, False, "#BFB197", 1, 0.95, 0.0),
    "cobogo": ("cobogo", False, "#ECE8DF", 0.3048, 0.9, 0.0),
    "cedar_z": ("cedar", True, "#A9693F", 0.9, 0.65, 0.0),
    "cedar_y": ("cedar", True, "#A9693F", 0.9, 0.65, 0.0),
    "cedar_x": ("cedar", False, "#A9693F", 0.9, 0.65, 0.0),
    "fence": ("cedar", False, "#8E6A4E", 0.9, 0.8, 0.0),
    "oak": ("oak", True, "#C9A57A", 0.8, 0.5, 0.0),
    "dark_wood": ("walnut", False, "#5E3D26", 0.9, 0.45, 0.0),
    "floor": ("concrete", False, "#B3AA9E", 2.5, 0.3, 0.0),
    "concrete": ("concrete", False, "#C4BCB0", 1.8, 0.8, 0.0),
    "pavers": ("limestone", False, "#DCD1BA", 1.4, 0.8, 0.0),
    "dg": ("dg", False, "#C2A27C", 1.2, 0.95, 0.0),
    "mulch": ("mulch", False, "#4E3D2E", 1.2, 0.95, 0.0),
    "lawn_soil": ("grass_ground", False, "#6A8040", 2.0, 0.95, 0.0),
    "asphalt": ("asphalt", False, "#4A4845", 3.0, 0.9, 0.0),
    "sidewalk": (None, False, "#C3BDB2", 1, 0.85, 0.0),
    "bronze": (None, False, "#2A2622", 1, 0.5, 0.4),
    "black": (None, False, "#1A1A19", 1, 0.5, 0.4),
    "brass": (None, False, "#B08A4A", 1, 0.3, 1.0),
    "roof": (None, False, "#C6C3BC", 1, 0.8, 0.0),
    "glass": (None, False, "#B9CCD0", 1, 0.05, 0.0),
    "granite": (None, False, "#232322", 1, 0.3, 0.0),
    "tile": (None, False, "#3E6B58", 1, 0.15, 0.0),
    "linen": (None, False, "#DCD3C4", 1, 1.0, 0.0),
    "olive_fabric": (None, False, "#5E6142", 1, 1.0, 0.0),
    "terracotta_fabric": (None, False, "#A8613F", 1, 1.0, 0.0),
    "leather": (None, False, "#7A4426", 1, 0.5, 0.0),
    "rug": (None, False, "#D5CAB6", 1, 1.0, 0.0),
    "ceramic": (None, False, "#F2F0EC", 1, 0.1, 0.0),
    "house_beige": (None, False, "#CFC6B6", 1, 0.9, 0.0),
    "house_roof": (None, False, "#5B5953", 1, 0.9, 0.0),
    "lamp": (None, False, "#FFE9C8", 1, 0.5, 0.0),
    "leaf": (None, False, "#3E5126", 1, 0.8, 0.0),
    "leaf_dark": (None, False, "#33441F", 1, 0.8, 0.0),
    "bark": ("bark", False, "#4A4038", 0.8, 0.9, 0.0),
    "agave": (None, False, "#86A196", 1, 0.5, 0.0),
    "grass": (None, False, "#A39A62", 1, 0.8, 0.0),
    "feather": (None, False, "#C8BA86", 1, 0.8, 0.0),
    "palm": (None, False, "#3F5A31", 1, 0.7, 0.0),
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_texture(folder, rotated, color):
    """Colorize the scanned map to the target mean color (keeps its detail), 512px."""
    os.makedirs(TEXOUT, exist_ok=True)
    name = f"{folder}{'_rot' if rotated else ''}.jpg"
    out = os.path.join(TEXOUT, name)
    if folder == "cobogo":
        _cobogo_png(out)
        return out
    src = os.path.join(HERE, "assets", "textures", folder, ("rot_" if rotated else "sq_") + "color.jpg")
    img = bpy.data.images.load(src, check_existing=False)
    img.scale(512, 512)
    px = np.empty(512 * 512 * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    lum = px[:, :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    detail = lum / max(lum.mean(), 1e-4)
    detail = 1.0 + (detail - 1.0) * 0.8
    tgt = np.array([((c / 255) ** 2.2) for c in hex_rgb(color)], dtype=np.float32)
    rgb = np.clip(tgt[None, :] * detail[:, None], 0, 1)
    px[:, :3] = rgb
    px[:, 3] = 1.0
    img.pixels.foreach_set(px.reshape(-1))
    img.filepath_raw = out
    img.file_format = "JPEG"
    img.save()
    bpy.data.images.remove(img)
    return out


def _cobogo_png(out):
    """One 12" block with alpha cut-outs (big center circle, corner + edge circles)."""
    S = 256
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) + 0.5
    x = xx / S
    y = yy / S
    alpha = np.ones((S, S), dtype=np.float32)
    holes = [(0.5, 0.5, 0.30)] + [(cx, cy, 0.24) for cx in (0, 1) for cy in (0, 1)] + \
        [(0.5, 0, 0.085), (0.5, 1, 0.085), (0, 0.5, 0.085), (1, 0.5, 0.085)]
    for cx, cy, r in holes:
        alpha[(x - cx) ** 2 + (y - cy) ** 2 < r * r] = 0
    # soft shading near hole edges for depth
    edge = np.ones((S, S), dtype=np.float32)
    for cx, cy, r in holes:
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
        edge = np.minimum(edge, np.clip(d / 0.035, 0, 1))
    base = np.array([0.83, 0.80, 0.75], dtype=np.float32)
    rgb = base[None, None, :] * (0.78 + 0.22 * edge[:, :, None])
    img = bpy.data.images.new("cobogo_tile", S, S, alpha=True)
    px = np.dstack([rgb, alpha[:, :, None]])[::-1].reshape(-1)
    img.pixels.foreach_set(px)
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def web_material(key):
    folder, rot, col, tile, rough, metal = WEB[key]
    m = bpy.data.materials.new(f"web_{key}")
    bs = m.node_tree.nodes.get("Principled BSDF")
    r, g, b = [(c / 255) ** 2.2 for c in hex_rgb(col)]
    bs.inputs["Base Color"].default_value = (r, g, b, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if folder:
        path = make_texture(folder, rot, col)
        tx = m.node_tree.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(path, check_existing=True)
        m.node_tree.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
        if folder == "cobogo":
            m.node_tree.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
    m["tile"] = tile
    return m


# ------------------------------------------------------------------ UVs
def box_uv(ob):
    me = ob.data
    if not me.polygons:
        return
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    mats = me.materials
    co = [v.co.copy() for v in me.vertices]
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        mat = mats[poly.material_index] if mats else None
        tile = float(mat.get("tile", 1.0)) if mat else 1.0
        for li in poly.loop_indices:
            p = co[me.loops[li].vertex_index]
            if ax == 0:
                u, v = p.y, p.z
            elif ax == 1:
                u, v = p.x, p.z
            else:
                u, v = p.x, p.y
            uv[li].uv = (u / tile, v / tile)


def merge_transformed(name, src_mesh, xforms, coll, mat):
    """Realize copies of src_mesh with (loc, rotz, scale) transforms into one mesh."""
    bm = bmesh.new()
    for loc, rz, s in xforms:
        tmp = src_mesh.copy()
        tmp.transform(Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(s, 4))
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# ------------------------------------------------------------------ web landscape
def web_tree(name, t, coll, W):
    loc = Vector((t["x"] * M, t["y"] * M, 0.0 if t["y"] < 28 or t["y"] > 92 else D.HARDSCAPE * M - 0.05))
    tmpc = bpy.data.collections.new("tmp_leaf")
    bpy.context.scene.collection.children.link(tmpc)
    lf = P.leaf_mesh("tmp_leafmesh", tmpc, None)
    wood, leaves, n = P.live_oak(name, tuple(loc), t["h"] * M, t["spread"] * M, t["seed"], coll, W["bark"], tmpc,
                                 leaf_density=0.35, crown_base=t.get("crown", 0.2))
    # prune twigs, lower resolution
    cu = wood.data
    cu.bevel_resolution = 0
    for sp in list(cu.splines):
        if sp.points[0].radius < 0.045:
            cu.splines.remove(sp)
    # canopy: icosphere clusters on a voxel grid of the leaf points
    pts = np.array([v.co[:] for v in leaves.data.vertices], dtype=np.float32)
    bpy.data.objects.remove(leaves)
    vox = 0.95 if t["spread"] > 30 else 0.8
    keys = {}
    for p in pts:
        k = tuple((p // vox).astype(int))
        keys.setdefault(k, []).append(p)
    rng = random.Random(t["seed"])
    bm = bmesh.new()
    for k, ps in keys.items():
        if len(ps) < 3:
            continue
        c = Vector(np.mean(ps, axis=0).tolist()) + loc
        r = vox * rng.uniform(0.55, 0.8)
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=r)
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=c)
        me = bpy.data.meshes.new("t")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name + "_canopy")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(W["leaf"] if t["seed"] % 2 else W["leaf_dark"])
    me.shade_smooth()
    ob = bpy.data.objects.new(name + "_canopy", me)
    coll.objects.link(ob)
    bpy.data.collections.remove(tmpc)
    # convert wood to mesh now (so export is predictable)
    dg = bpy.context.evaluated_depsgraph_get()
    wm = bpy.data.meshes.new_from_object(wood.evaluated_get(dg))
    wm.shade_smooth()
    wob = bpy.data.objects.new(name + "_wood", wm)
    wob.location = wood.location
    coll.objects.link(wob)
    bpy.data.objects.remove(wood)
    return ob


def web_planting(coll, W):
    rng = random.Random(5)
    pc = bpy.data.collections.new("tmp_plants")
    bpy.context.scene.collection.children.link(pc)
    ag = P.agave("ag", pc, W["agave"], seed=21, n_leaves=22, length=0.7)
    gr = P.grass_clump("gr", pc, W["feather"], seed=1, blades=18, height=0.6, spread=0.4, width=0.012, droop=0.8, segs=3)
    mu = P.grass_clump("mu", pc, W["grass"], seed=2, blades=18, height=0.8, spread=0.35, width=0.014, droop=0.5, segs=3)
    so = P.grass_clump("so", pc, W["grass"], seed=3, blades=40, height=0.9, spread=0.8, width=0.016, droop=0.25, segs=3)
    pa = P.palmetto("pa", pc, W["palm"], seed=4)
    S = landscape
    fm, fe = D.PLANTING[0]["poly"], D.PLANTING[1]["poly"]
    avoid = [(28.5, -1, 33.5, 28.5)]
    pts_ag = S.sample_poly(fm, 7, rng, avoid, 5.5) + S.sample_poly(fe, 5, rng, avoid + [(44, 0, 56, 27)], 5.5)
    pts_so = S.sample_poly(fm, 4, rng, avoid, 7.0, pts_ag) + S.sample_poly(fe, 3, rng, avoid, 7.0, pts_ag)
    pts_fe = S.sample_poly(fm, 150, rng, avoid + [(-1, -1, 9, 18)], 2.0, pts_ag + pts_so) + \
        S.sample_poly(fe, 130, rng, avoid, 2.0, pts_ag + pts_so)
    zc = (D.HARDSCAPE - 0.08) * M
    cy = [(31.6, 36.6), (53.5, 36.6), (53.5, 49.0), (39.5, 49.0), (39.5, 56.3), (31.6, 56.3)]
    pts_pa = S.sample_poly(cy, 12, rng, [(42.2, 44.8, 45.8, 48.2)], 3.0)
    pts_mu = S.sample_poly([(32, 36.6), (53.4, 36.6), (53.4, 39.0), (32, 39.0)], 16, rng, (), 1.5) + \
        S.sample_poly([(31.6, 38), (36.5, 38), (36.5, 56), (31.6, 56)], 18, rng, (), 1.6, pts_pa)

    def xf(pts, z=0.0, s=(0.8, 1.2)):
        return [(Vector((x * M, y * M, z)), rng.uniform(0, 6.28), rng.uniform(*s)) for x, y in pts]

    merge_transformed("Plants agave", ag.data, xf(pts_ag, 0, (0.9, 1.3)) + xf([(50.5, 49.0), (47.8, 41.0)], zc), coll, W["agave"])
    merge_transformed("Plants sotol", so.data, xf(pts_so), coll, W["grass"])
    merge_transformed("Plants feather grass", gr.data, xf(pts_fe, 0, (0.7, 1.2)), coll, W["feather"])
    merge_transformed("Plants muhly", mu.data, xf(pts_mu, zc), coll, W["grass"])
    merge_transformed("Plants palmetto", pa.data, xf(pts_pa, zc, (1.1, 1.5)), coll, W["palm"])
    for o in list(pc.objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(pc)


def web_cobogo(L, coll):
    c = D.COBOGO
    mb = MB("Cobogo screen", [L["cobogo"]])
    mb.box(c["x0"], c["y"] + 0.12, c["z0"], c["x1"], c["y"] + 0.21, c["z1"])
    ob = mb.build(coll)
    # UVs: one texture repeat per 12" block on the faces
    mb2 = MB("Cobogo curb", [L["concrete"]])
    mb2.box(c["x0"] - 0.5, c["y"] - 0.05, D.GRADE, c["x1"] + 0.3, c["y"] + c["t"] + 0.05, c["z0"])
    mb2.build(coll)
    return ob


def main():
    R.reset()
    L = MAT.build_library()
    W = {k: web_material(k) for k in WEB}
    root = bpy.context.scene.collection
    arch = new_coll("Architecture", root)
    land = new_coll("Landscape", root)
    furn = new_coll("Furniture", root)
    house._cobogo = web_cobogo
    house.build_house(L, arch)
    furniture.build_furniture(L, furn, {})
    # ground (same surfaces as the renders, cropped to the neighborhood)
    g = MB("Ground", [L["lawn_soil"], L["dg"], L["sidewalk"], L["asphalt"], L["concrete"]])
    g.box(-60, -11.0, -0.3, 125, 190, -0.02, mats6=[0] * 6)
    g.box(-60, -70, -0.3, 125, -48.0, -0.02, mats6=[0] * 6)
    g.box(-60, -47.5, -0.8, 125, -11.5, -0.5, mats6=[3] * 6)
    g.box(-60, -11.5, -0.8, 125, -11.0, 0.02, mat=4)
    g.box(-60, -48.0, -0.8, 125, -47.5, 0.02, mat=4)
    g.box(-60, -5.0, -0.1, 125, -0.5, 0.04, mat=2)
    g.box(0.0, -0.5, -0.1, 54.0, 27.0, 0.0, mats6=[1] * 6)
    g.box(54.0, -0.5, -0.1, 65.0, 125.0, 0.0, mats6=[1] * 6)
    g.box(0.0, 27.0, -0.1, 6.0, 125.0, 0.0, mats6=[1] * 6)
    for (sx0, sx1) in D.DRIVEWAY["strips"]:
        g.box(sx0, D.DRIVEWAY["y0"], -0.1, sx1, D.DRIVEWAY["y1"], 0.05, mat=4)
    g.build(land)
    landscape._fences(L, land)
    landscape._neighbors(L, land)
    for t in D.TREES:
        web_tree(f"tree_{t['seed']}", t, land, W)
    web_planting(land, W)

    # swap every render material for its web twin, drop bevels, add box UVs
    by_name = {m.name: k for k, m in L.items()}
    for ob in list(bpy.data.objects):
        if ob.type != "MESH":
            continue
        for mod in list(ob.modifiers):
            if mod.type == "BEVEL":
                ob.modifiers.remove(mod)
        for slot in ob.material_slots:
            if slot.material and slot.material.name in by_name:
                k = by_name[slot.material.name]
                slot.material = W.get(k, W["paint"])
        box_uv(ob)
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT" or ob.users_collection and ob.users_collection[0].name.startswith(("proto", "tmp")):
            bpy.data.objects.remove(ob)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "casa01.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_materials="EXPORT",
                              export_image_format="AUTO", export_yup=True, export_cameras=False, export_lights=False)
    print(f"[web] wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
