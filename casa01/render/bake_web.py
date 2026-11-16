"""Realistic web model: Cycles-baked sky light + bounce light (lightmaps), leaf-card trees,
normal maps and a photographed sky, for the interactive viewer.

    python casa01/render/bake_web.py [--samples 48] [--scale 1.0]

Bakes in the full render scene (real oaks with every leaf, the 210 real cobogó blocks)
so the soft shading under the trees and through the screen is physically correct. The
sun is NOT baked: the viewer keeps a live sun with real-time shadows on top, so the
time-of-day slider still works.

Writes casa01/lookbook/web/: casa01_v2.glb, lm/*.jpg (lightmaps), tex/*.jpg (normal
maps, leaf cards, sky), lightmaps.json.
"""
import argparse
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, CASA)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import design as D  # noqa: E402
import materials as MAT  # noqa: E402
import plants as P  # noqa: E402
import house  # noqa: E402
import furniture  # noqa: E402
import landscape  # noqa: E402
import render as R  # noqa: E402
import export_web as EW  # noqa: E402
from geo import MB, M, new_coll  # noqa: E402

WEB = os.path.join(CASA, "lookbook", "web")
LM = os.path.join(WEB, "lm")
TX = os.path.join(WEB, "tex")
ASSETS = os.path.join(HERE, "assets")

BAKE_ARCH = {"Walls", "Slab", "Window frames", "Limestone ashlar", "Limestone mortar", "Slot window reveal",
             "Roof", "Cedar soffits", "Cobogo curb", "Gate steel", "Steel posts", "Limestone pavers",
             "Courtyard soil", "Cedar vertical", "Entry mosaic", "Bath floor tile", "Shower zellige",
             "Bath limestone", "Bath brass", "Bath vanity", "Bath wc"}
# small bath fixtures kept in the web model without a lightmap
KEEP_EXTRA = ("Glass", "Shower glass", "Rain head", "Vessel sink", "Mirror", "Mirror rim", "Sconce arm", "Sconce globe")
BAKE_FURN = {"Oak millwork", "Upholstery", "Walnut furniture", "Ceramic fixtures", "Grill limestone",
             "Outdoor teak", "Living extras"}
BAKE_LAND = {"Ground", "Cedar fences", "Neighbors"}


# ------------------------------------------------------------------ images (numpy, no PIL in bpy)
def save_rgb(path, arr, fmt="JPEG", alpha=None):
    h, w, _ = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=alpha is not None)
    a = np.ones((h, w, 1), np.float32) if alpha is None else alpha[..., None].astype(np.float32)
    img.pixels.foreach_set(np.concatenate([arr.astype(np.float32), a], axis=2).reshape(-1))
    img.filepath_raw = path
    img.file_format = fmt
    bpy.context.scene.render.image_settings.quality = 90
    img.save()
    bpy.data.images.remove(img)


def load_gray(path, size=512):
    img = bpy.data.images.load(path, check_existing=False)
    img.scale(size, size)
    px = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(size, size, 4)[..., :3].mean(axis=2)


def normal_maps():
    os.makedirs(TX, exist_ok=True)
    jobs = {"limestone": ("limestone", False, 3.0), "stucco": ("stucco", False, 2.0),
            "cedar": ("cedar", False, 2.5), "cedar_rot": ("cedar", True, 2.5),
            "concrete": ("concrete", False, 1.2), "dg": ("dg", False, 4.0), "bark": ("bark", False, 5.0),
            "grass": ("grass_ground", False, 3.0), "asphalt": ("asphalt", False, 2.0), "oak": ("oak", True, 1.0)}
    for name, (folder, rot, k) in jobs.items():
        out = os.path.join(TX, f"{name}_n.jpg")
        src = os.path.join(ASSETS, "textures", folder, ("rot_" if rot else "sq_") + "disp.jpg")
        if not os.path.exists(src):
            continue
        h = load_gray(src)
        h = (h - h.mean()) / (h.std() + 1e-5)
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
        n = np.dstack([-dx * k * 0.15, -dy * k * 0.15, np.ones_like(h)])
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        save_rgb(out, n * 0.5 + 0.5)


def leaf_card_texture(path, seed, base, var):
    """512x512 RGBA cluster of small elliptic live-oak leaves."""
    rng = np.random.default_rng(seed)
    S = 512
    rgb = np.zeros((S, S, 3), np.float32)
    alpha = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # leaves denser toward the middle, sparse at the edges
    for _ in range(520):
        r = abs(rng.normal(0, 0.28)) * S
        a = rng.uniform(0, 2 * math.pi)
        cx, cy = S / 2 + math.cos(a) * r, S / 2 + math.sin(a) * r
        if not (12 < cx < S - 12 and 12 < cy < S - 12):
            continue
        L, W = rng.uniform(16, 30), rng.uniform(6.5, 11)
        th = rng.uniform(0, math.pi)
        x0, x1 = int(max(cx - L, 0)), int(min(cx + L, S))
        y0, y1 = int(max(cy - L, 0)), int(min(cy + L, S))
        X = xx[y0:y1, x0:x1] - cx
        Y = yy[y0:y1, x0:x1] - cy
        u = X * math.cos(th) + Y * math.sin(th)
        v = -X * math.sin(th) + Y * math.cos(th)
        m = (u / L) ** 2 + (v / W) ** 2 < 1.0
        shade = rng.uniform(1 - var, 1 + var)
        col = np.clip(np.array(base) * shade * (0.85 + 0.3 * (u / L)[..., None] * 0.5 + 0.15), 0, 1)
        col = np.where((np.abs(v) < 0.9)[..., None], col * 0.82, col)  # mid-rib
        rgb[y0:y1, x0:x1][m] = col[m]
        alpha[y0:y1, x0:x1][m] = 1.0
    # twigs
    save_rgb(path, rgb, fmt="PNG", alpha=alpha)


def sky_texture(path, name="day"):
    """Tone-mapped LDR equirect of the HDRI sky (sun clipped) for the viewer background."""
    img = bpy.data.images.load(os.path.join(ASSETS, "hdri", f"{name}.hdr"), check_existing=False)
    img.scale(2048, 1024)
    px = np.empty(2048 * 1024 * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    rgb = px.reshape(1024, 2048, 4)[..., :3]
    rgb = rgb / (np.percentile(rgb.mean(axis=2), 70) * 1.9)
    rgb = rgb / (1 + rgb * 0.35)                 # soft shoulder
    rgb = np.clip(rgb, 0, 1) ** (1 / 2.2)
    save_rgb(path, rgb)


# ------------------------------------------------------------------ scene for baking
def build_bake_scene():
    R.reset()
    L = MAT.build_library()
    root = bpy.context.scene.collection
    arch = new_coll("Architecture", root)
    land = new_coll("Landscape", root)
    furn = new_coll("Furniture", root)
    protos = R.load_protos(root)
    house.build_house(L, arch)
    landscape.build_site(L, land, protos)
    furniture.build_furniture(L, furn, {})
    for c in list(root.children):
        if c.name.startswith(("proto", "inst_")) or c.name == "protos":
            R.exclude(c.name)
    # replace the render ground (500 ft wide) with the web-size ground so the bake lands on it
    bpy.data.objects.remove(bpy.data.objects["Ground"])
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
    return L


def sky_only_world():
    """Day HDRI with the sun clipped out: soft sky + bounce only (sun stays live in the viewer)."""
    R.set_world("day", 200, 1.0)
    nt = bpy.context.scene.world.node_tree
    env = [n for n in nt.nodes if n.type == "TEX_ENVIRONMENT"][0]
    bg = [n for n in nt.nodes if n.type == "BACKGROUND"][0]
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    comb = nt.nodes.new("ShaderNodeCombineColor")
    nt.links.new(env.outputs["Color"], sep.inputs[0])
    for i in range(3):
        mn = nt.nodes.new("ShaderNodeMath")
        mn.operation = "MINIMUM"
        mn.inputs[1].default_value = 2.5
        nt.links.new(sep.outputs[i], mn.inputs[0])
        nt.links.new(mn.outputs[0], comb.inputs[i])
    nt.links.new(comb.outputs[0], bg.inputs["Color"])


def box_uv_layer(ob, mats_tile):
    me = ob.data
    if "UVMap" not in me.uv_layers:
        me.uv_layers.new(name="UVMap")
    lay = me.uv_layers["UVMap"]
    co = [v.co.copy() for v in me.vertices]
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        mat = me.materials[poly.material_index] if me.materials else None
        tile = mats_tile.get(mat.name, 1.0) if mat else 1.0
        for li in poly.loop_indices:
            p = co[me.loops[li].vertex_index]
            u, v = ((p.y, p.z), (p.x, p.z), (p.x, p.y))[ax]
            lay.data[li].uv = (u / tile, v / tile)


def lightmap_uv(ob):
    me = ob.data
    if "Lightmap" not in me.uv_layers:
        me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = me.uv_layers["Lightmap"]
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")


def area(ob):
    return sum(p.area for p in ob.data.polygons)


def bake_all(objs_res, samples):
    """Bake every target in ONE Cycles pass (scene sync happens once). Each object gets
    private copies of its materials so each can point at its own lightmap image."""
    imgs = {}
    for ob, res in objs_res:
        img = bpy.data.images.new("LM_" + ob.name, res, res, float_buffer=True)
        imgs[ob.name] = (img, res)
        for slot in ob.material_slots:
            m = slot.material.copy()
            m["orig"] = slot.material.name
            slot.material = m
            nt = m.node_tree
            node = nt.nodes.new("ShaderNodeTexImage")
            node.name = "BAKE_TARGET"
            node.image = img
            nt.nodes.active = node
        ob.data.uv_layers.active = ob.data.uv_layers["Lightmap"]
    bpy.ops.object.select_all(action="DESELECT")
    for ob, _ in objs_res:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs_res[0][0]
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.render.bake.use_pass_direct = True
    sc.render.bake.use_pass_indirect = True
    sc.render.bake.use_pass_color = False
    sc.render.bake.margin = 8
    sc.render.bake.target = "IMAGE_TEXTURES"
    t = time.time()
    bpy.ops.object.bake(type="DIFFUSE")
    print(f"[bake] {len(objs_res)} objects in {time.time() - t:.0f}s", flush=True)
    out = {}
    for name, (img, res) in imgs.items():
        px = np.empty(res * res * 4, np.float32)
        img.pixels.foreach_get(px)
        out[name] = px.reshape(res, res, 4)[..., :3].copy()
        bpy.data.images.remove(img)
    # restore the shared library materials so the web swap can map them
    for ob, _ in objs_res:
        for slot in ob.material_slots:
            orig = slot.material.get("orig")
            if orig:
                slot.material = bpy.data.materials[orig]
    return out


def blur(a, s=1.2):
    k = np.exp(-0.5 * (np.arange(-3, 4) / s) ** 2)
    k /= k.sum()
    for ax in (0, 1):
        a = sum(np.roll(a, i - 3, axis=ax) * k[i] for i in range(7))
    return a


# ------------------------------------------------------------------ web-weight replacements
def leafcard_tree(name, t, coll, W, cards):
    loc = Vector((t["x"] * M, t["y"] * M, 0.0 if t["y"] < 28 or t["y"] > 92 else D.HARDSCAPE * M - 0.05))
    tmpc = bpy.data.collections.new("tmp_leaf")
    bpy.context.scene.collection.children.link(tmpc)
    P.leaf_mesh("tmp_leafmesh", tmpc, None)
    wood, leaves, n = P.live_oak(name, tuple(loc), t["h"] * M, t["spread"] * M, t["seed"], coll, W["bark"], tmpc,
                                 leaf_density=0.35, crown_base=t.get("crown", 0.2))
    cu = wood.data
    cu.bevel_resolution = 1
    for sp in list(cu.splines):
        if sp.points[0].radius < 0.03:
            cu.splines.remove(sp)
    pts = np.array([v.co[:] for v in leaves.data.vertices], dtype=np.float32)
    bpy.data.objects.remove(leaves)
    vox = 0.8 if t["spread"] > 30 else 0.65
    keys = {}
    for p in pts:
        keys.setdefault(tuple((p // vox).astype(int)), []).append(p)
    rng = random.Random(t["seed"])
    verts, faces, uvs = [], [], []
    for k, ps in keys.items():
        if len(ps) < 3:
            continue
        c = Vector(np.mean(ps, axis=0).tolist()) + loc
        s = vox * rng.uniform(0.85, 1.15)
        for q in range(3):
            # random orientation, biased to face outward/up a little
            a = rng.uniform(0, math.pi)
            tilt = rng.uniform(-0.6, 0.6)
            u = Vector((math.cos(a), math.sin(a), 0))
            w = Vector((-math.sin(a) * math.sin(tilt), math.cos(a) * math.sin(tilt), math.cos(tilt)))
            b = len(verts)
            for (du, dv, uv) in ((-1, -1, (0, 0)), (1, -1, (1, 0)), (1, 1, (1, 1)), (-1, 1, (0, 1))):
                verts.append(c + u * du * s + w * dv * s)
                uvs.append(uv)
            faces.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new(name + "_canopy")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    lay = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            lay.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(cards[t["seed"] % len(cards)])
    ob = bpy.data.objects.new(name + "_canopy", me)
    coll.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    wm = bpy.data.meshes.new_from_object(wood.evaluated_get(dg))
    wm.shade_smooth()
    wob = bpy.data.objects.new(name + "_wood", wm)
    wob.location = wood.location
    coll.objects.link(wob)
    bpy.data.objects.remove(wood)
    bpy.data.collections.remove(tmpc)


def card_material(name, tex):
    m = bpy.data.materials.new(name)
    bs = m.node_tree.nodes.get("Principled BSDF")
    tx = m.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(tex, check_existing=True)
    m.node_tree.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
    m.node_tree.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
    bs.inputs["Roughness"].default_value = 0.7
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--scale", type=float, default=1.0, help="lightmap resolution multiplier")
    ap.add_argument("--only", default="")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    for d in (WEB, LM, TX):
        os.makedirs(d, exist_ok=True)

    t0 = time.time()
    L = build_bake_scene()
    R.setup_render(args.samples, 64, 64)
    sky_only_world()
    by_name = {m.name: k for k, m in L.items()}

    targets = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        if ob.name in BAKE_ARCH | BAKE_FURN | BAKE_LAND:
            for mod in list(ob.modifiers):
                if mod.type == "BEVEL":
                    ob.modifiers.remove(mod)
            targets.append(ob)
    if args.only:
        targets = [o for o in targets if o.name in args.only.split(",")]
    print(f"[bake] scene built in {time.time() - t0:.0f}s; {len(targets)} targets", flush=True)

    tiles = {m.name: EW.WEB.get(by_name.get(m.name, ""), (None, False, "#fff", 1.0))[3] for m in bpy.data.materials}
    for ob in targets:
        box_uv_layer(ob, tiles)
    # Cycles re-syncs the whole (very heavy) scene once per baked object, so join the targets
    # into 4 groups: one bake call each, with one lightmap atlas per group.
    groups = {"House": [o for o in targets if o.name not in ("Roof", "Cedar soffits", "Ground", "Neighbors", "Cedar fences")],
              "Roof": [o for o in targets if o.name in ("Roof", "Cedar soffits")],
              "Ground": [o for o in targets if o.name == "Ground"],
              "Context": [o for o in targets if o.name in ("Neighbors", "Cedar fences")]}
    sizes = {"House": 4096, "Roof": 2048, "Ground": 2048, "Context": 1024}
    jobs = []
    joined = []
    for gname, obs in groups.items():
        if not obs:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        if len(obs) > 1:
            bpy.ops.object.join()
        g = bpy.context.view_layer.objects.active
        g.name = gname
        lightmap_uv(g)
        res = max(128, int(sizes[gname] * args.scale))
        jobs.append((g, res))
        joined.append(gname)
        print(f"[bake] {gname}: {area(g):.0f} m2 -> {res}px", flush=True)
    targets = [g for g, _ in jobs]
    raw = {k: blur(v, 1.3 if v.shape[0] >= 2048 else 1.0) for k, v in bake_all(jobs, args.samples).items()}

    # one global scale: open-sky ground irradiance -> 0.5 (headroom), stored sRGB-encoded
    gref = float(np.percentile(raw["Ground"].mean(axis=2), 97)) if "Ground" in raw else 1.0
    scale = 2.0 * gref
    manifest = {"scale": scale, "maps": {}}
    for name, arr in raw.items():
        fn = name.replace(" ", "_") + ".jpg"
        v = np.clip(arr / scale, 0, 1) ** (1 / 2.2)
        save_rgb(os.path.join(LM, fn), v)
        manifest["maps"][name.replace(" ", "_")] = fn
    with open(os.path.join(WEB, "lightmaps.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"[bake] lightmaps done ({len(raw)}) ref={gref:.3f}", flush=True)

    # ---- turn the bake scene into the web scene
    keep = set(o.name for o in targets) | {o.name for o in bpy.data.objects if o.name.split(".")[0] in KEEP_EXTRA}
    for ob in list(bpy.data.objects):
        if ob.name not in keep:
            bpy.data.objects.remove(ob)
    W = {k: EW.web_material(k) for k in EW.WEB}
    normal_maps()
    leaf_card_texture(os.path.join(TX, "leaves_a.png"), 1, (0.16, 0.24, 0.09), 0.25)
    leaf_card_texture(os.path.join(TX, "leaves_b.png"), 2, (0.22, 0.29, 0.11), 0.25)
    sky_texture(os.path.join(TX, "sky_day.jpg"))
    cards = [card_material("web_leafcard_a", os.path.join(TX, "leaves_a.png")),
             card_material("web_leafcard_b", os.path.join(TX, "leaves_b.png"))]
    land = bpy.data.collections.get("Landscape") or new_coll("Landscape", bpy.context.scene.collection)
    for t in D.TREES:
        leafcard_tree(f"tree_{t['seed']}", t, land, W, cards)
    EW.web_planting(land, W)
    arch = bpy.data.collections.get("Architecture")
    c = D.COBOGO
    pm = MB("Cobogo screen", [L["cobogo"]])
    pm.box(c["x0"], c["y"] + 0.12, c["z0"], c["x1"], c["y"] + 0.21, c["z1"])
    pm.build(arch)
    for ob in list(bpy.data.objects):
        if ob.type != "MESH":
            continue
        for slot in ob.material_slots:
            if slot.material and slot.material.name in by_name:
                slot.material = W.get(by_name[slot.material.name], W["paint"])
        if ob.name not in keep and not ob.name.endswith("_canopy"):
            EW.box_uv(ob)
        elif ob.name in keep:
            if "UVMap" not in ob.data.uv_layers:
                EW.box_uv(ob)
        # albedo textures read the first (box) layout; the lightmap layout stays second
        if "UVMap" in ob.data.uv_layers:
            ob.data.uv_layers.active = ob.data.uv_layers["UVMap"]
            ob.data.uv_layers["UVMap"].active_render = True
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.name = ob.name.replace(" ", "_")
    out = os.path.join(WEB, "casa01_v2.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_materials="EXPORT",
                              export_image_format="AUTO", export_yup=True, export_cameras=False,
                              export_lights=False, export_texcoords=True)
    print(f"[web] wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB) in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
