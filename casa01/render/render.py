"""Casa 01 render pipeline (Blender 5.3 / Cycles via the `bpy` module).

    python casa01/render/render.py --views street,courtyard --res 1920 --samples 256

Builds the whole scene from casa01/design.py, then renders each view to
casa01/renders/<view>.png. Runs headless (no Blender UI needed).
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import design as D  # noqa: E402
import materials as MAT  # noqa: E402
from geo import M, new_coll  # noqa: E402
import house  # noqa: E402
import landscape as SITE  # noqa: E402
import furniture  # noqa: E402

HDRI = os.path.join(HERE, "assets", "hdri")
OUT = os.path.join(os.path.dirname(HERE), "renders")

# camera: position & target in feet, lens mm. sun = compass azimuth of the sun.
VIEWS = {
    "street": dict(cam=(41.0, -15.5, 5.4), tgt=(27.0, 30.0, 7.4), lens=22, hdri="afternoon", sun=232,
                   strength=1.0, exposure=-0.2, night=False),
    "street_dusk": dict(cam=(41.0, -15.5, 5.4), tgt=(27.0, 30.0, 7.4), lens=22, hdri="dusk", sun=290,
                        strength=0.07, exposure=0.9, night=True, night_level=1.6),
    "courtyard": dict(cam=(48.6, 58.6, D.HARDSCAPE + 5.6), tgt=(35.0, 33.0, 6.4), lens=18, hdri="day",
                      sun=192, strength=1.0, exposure=0.7, night=False),
    "entry": dict(cam=(51.5, 35.0, D.HARDSCAPE + 5.0), tgt=(31.0, 31.5, 5.6), lens=24, hdri="day", sun=198,
                  strength=1.0, exposure=0.6, night=False),
    "veranda": dict(cam=(41.8, 90.4, D.HARDSCAPE + 4.9), tgt=(20.5, 83.8, 5.4), lens=20, hdri="afternoon",
                    sun=284, strength=1.0, exposure=0.9, night=True, night_level=0.35),
    "interior": dict(cam=(21.6, 78.9, D.FF + 4.7), tgt=(33.5, 60.0, D.FF + 4.0), lens=17, hdri="day", sun=200,
                     strength=1.0, exposure=2.6, night=True, night_level=0.25),
    "gallery": dict(cam=(25.4, 59.6, D.FF + 4.8), tgt=(25.4, 31.0, D.FF + 4.4), lens=17, hdri="day", sun=120,
                    strength=1.0, exposure=2.6, night=True, night_level=0.3),
    "aerial": dict(cam=(118.0, -52.0, 96.0), tgt=(31.0, 58.0, 0.0), lens=30, hdri="day", sun=215,
                   strength=1.0, exposure=0.0, night=False, two_point=False),
    "rear": dict(cam=(46.0, 121.0, 5.6), tgt=(27.0, 82.0, 7.0), lens=20, hdri="afternoon", sun=292,
                 strength=1.0, exposure=0.5, night=True, night_level=0.35),
    # 360° equirectangular panoramas for the web tour (tgt only sets the initial heading)
    "pano_street": dict(cam=(31.5, -2.6, 5.3), tgt=(31.5, 30.0, 5.3), lens=20, hdri="afternoon", sun=232,
                        strength=1.0, exposure=-0.2, night=False, pano=True),
    "pano_entry": dict(cam=(31.2, 33.2, D.HARDSCAPE + 5.2), tgt=(31.2, 60.0, 5.3), lens=20, hdri="day", sun=198,
                       strength=1.0, exposure=0.5, night=False, pano=True),
    "pano_patio": dict(cam=(35.5, 56.6, D.HARDSCAPE + 5.2), tgt=(44.0, 40.0, 5.3), lens=20, hdri="day", sun=192,
                       strength=1.0, exposure=0.6, night=False, pano=True),
    "pano_room": dict(cam=(30.0, 70.5, D.FF + 5.0), tgt=(30.0, 55.0, 5.3), lens=20, hdri="day", sun=200,
                      strength=1.0, exposure=1.8, night=True, night_level=0.25, pano=True),
    "pano_veranda": dict(cam=(30.0, 87.5, D.HARDSCAPE + 5.2), tgt=(30.0, 110.0, 5.3), lens=20, hdri="afternoon",
                         sun=284, strength=1.0, exposure=0.9, night=True, night_level=0.35, pano=True),
    "bath": dict(cam=(52.45, 72.2, D.FF + 4.7), tgt=(46.3, 78.9, D.FF + 3.2), lens=15, hdri="day", sun=95,
                 strength=1.0, exposure=2.0, night=True, night_level=0.5),
    # orthographic presentation renders (rendered plan, landscape plan, elevations).
    # center/width in feet; rot in degrees; res in px. Also written to renders/ortho/ortho_views.json
    "plan_render": dict(ortho=True, center=(32.5, 59.5, 60.0), rot=(0, 0, 0), width=67.0, res=(2400, 2687),
                        clip=60.0 - (D.FF + 4.5), hide=["Roof", "Cedar soffits"], hdri="day", sun=215,
                        strength=1.0, exposure=0.15, night=False),
    "site_render": dict(ortho=True, center=(32.5, 57.5, 140.0), rot=(0, 0, 0), width=93.0, res=(1500, 2371),
                        hdri="day", sun=225, strength=1.0, exposure=0.0, night=False),
    "elev_s": dict(ortho=True, center=(30.0, -45.0, 13.0), rot=(90, 0, 0), width=72.0, res=(2400, 1000),
                   hide=["oak_11", "oak_19", "oak_23", "oak_29", "Neighbors", "Front shrubs"], transparent=True,
                   hdri="day", sun=200, strength=1.0, exposure=0.0, night=False),
    "elev_n": dict(ortho=True, center=(30.0, 170.0, 13.0), rot=(90, 0, 180), width=72.0, res=(2400, 1000),
                   hide=["oak_7", "oak_51", "oak_53", "Neighbors", "Rear lawn", "Cedar fences"], transparent=True,
                   hdri="afternoon", sun=300, strength=1.0, exposure=0.2, night=False),
    "elev_e": dict(ortho=True, center=(140.0, 61.0, 13.0), rot=(90, 0, 90), width=86.0, res=(2400, 837),
                   hide=["Neighbors", "Cedar fences", "oak_29", "oak_37", "oak_59", "oak_67"], transparent=True,
                   hdri="day", sun=110, strength=1.0, exposure=0.0, night=False),
    "elev_w": dict(ortho=True, center=(-80.0, 61.0, 13.0), rot=(90, 0, -90), width=86.0, res=(2400, 837),
                   hide=["Neighbors", "Cedar fences", "oak_23", "oak_31", "oak_57", "oak_61", "oak_11", "Side shrubs"],
                   transparent=True, hdri="day", sun=250, strength=1.0, exposure=0.0, night=False),
    "kitchen": dict(cam=(28.2, 61.3, D.FF + 4.9), tgt=(9.5, 76.5, D.FF + 3.6), lens=19, hdri="day", sun=200,
                    strength=1.0, exposure=2.4, night=True, night_level=0.3),
}

SENSOR = 36.0


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_protos(root):
    pc = new_coll("protos", root)
    protos = {}

    def one(key, asset, name=None):
        objs = SITE.append_objects(asset)
        if not objs:
            return
        for o in objs:
            pc.objects.link(o)
        if name:
            ob = [o for o in objs if o.name.startswith(name)][0]
            ob.location = (0, 0, 0)
            protos[key] = ob
        return objs

    def group(key, asset, pick):
        objs = SITE.append_objects(asset)
        if not objs:
            return
        c = bpy.data.collections.new("proto_" + key)
        root.children.link(c)
        for o in objs:
            if pick(o.name):
                c.objects.link(o)
                o.location = (0, 0, 0)
        protos[key] = c

    def inst(key, asset):
        objs = SITE.append_objects(asset)
        if not objs:
            return
        c = bpy.data.collections.new("inst_" + key)
        root.children.link(c)
        for o in objs:
            c.objects.link(o)
        e = bpy.data.objects.new("proto_" + key, None)
        e.instance_type = "COLLECTION"
        e.instance_collection = c
        pc.objects.link(e)
        protos[key] = e

    one("chair", "dining_chair_02", "dining_chair_02")
    one("lounge", "mid_century_lounge_chair", "mid_century_lounge_chair")
    one("armchair", "modern_arm_chair_01", "modern_arm_chair_01")
    one("side_table", "side_table_01", "side_table_01")
    one("pendant", "modern_ceiling_lamp_01", "modern_ceiling_lamp_01")
    one("vase", "ceramic_vase_01", "ceramic_vase_01")
    inst("plant", "potted_plant_02")
    group("fern", "fern_02", lambda n: True)
    group("lawn", "grass_medium_02", lambda n: not n.endswith("_geo") and "geometry_nodes" not in n)
    group("shrub", "searsia_lucida", lambda n: n.endswith("LOD1"))
    group("boulder", "boulder_01", lambda n: n.endswith("LOD0"))
    return protos


def exclude(coll_name):
    def walk(lc):
        if lc.collection.name == coll_name:
            lc.exclude = True
            return True
        return any(walk(c) for c in lc.children)
    walk(bpy.context.view_layer.layer_collection)


# ---------------------------------------------------------------- world
_SUN_CACHE = {}


def hdri_sun(path):
    """(azimuth_deg compass, elevation_deg) of the brightest pixel."""
    if path in _SUN_CACHE:
        return _SUN_CACHE[path]
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    lum = (px.reshape(-1, 4)[:, :3] * [0.2126, 0.7152, 0.0722]).sum(1)
    i = int(np.argmax(lum))
    yy, xx = divmod(i, w)
    u = (xx + 0.5) / w
    v = (yy + 0.5) / h
    phi = (u - 0.5) * 2 * math.pi
    elev = (v - 0.5) * math.pi
    az = math.degrees(math.atan2(-math.cos(phi), math.sin(phi))) % 360
    _SUN_CACHE[path] = (az, math.degrees(elev))
    return _SUN_CACHE[path]


def set_world(name, sun_az, strength):
    path = os.path.join(HDRI, f"{name}.hdr")
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Strength"].default_value = strength
    az, el = hdri_sun(path)
    rot = math.radians(sun_az - az)
    mp.inputs["Rotation"].default_value = (0, 0, -rot)
    print(f"[world] {name}: hdri sun az={az:.1f} el={el:.1f} -> target az={sun_az}")
    return el


# ---------------------------------------------------------------- lights
def build_night_lights(coll):
    warm = (1.0, 0.70, 0.42)

    def spot(name, x, y, z, power, size=110, blend=0.7, rot=(0, 0, 0), radius=0.04, color=warm, aim=None):
        ld = bpy.data.lights.new(name, "SPOT")
        ld.energy = power
        ld.spot_size = math.radians(size)
        ld.spot_blend = blend
        ld.shadow_soft_size = radius
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = (x * M, y * M, z * M)
        ob.rotation_euler = rot
        if aim is not None:
            d = Vector(aim) * M - Vector((x, y, z)) * M
            ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        coll.objects.link(ob)
        return ob

    def point(name, x, y, z, power, radius=0.08, color=warm):
        ld = bpy.data.lights.new(name, "POINT")
        ld.energy = power
        ld.shadow_soft_size = radius
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = (x * M, y * M, z * M)
        coll.objects.link(ob)
        return ob

    c = D.CEIL - 0.08
    # interior downlights
    for x in (10, 15, 21, 26, 31, 35.5):
        for y in (64, 70, 76):
            spot("dl", x, y, c, 22)
    for y in (34, 40, 46, 52, 57):
        spot("dl_gal", 25.4, y, c, 16)
    for (x, y) in ((14, 36), (14, 54), (46, 66), (49, 76), (18, 45)):
        spot("dl_bed", x, y, c, 18)
    # primary bath: sconces + shower downlight
    for yy in D.PRIMARY_BATH["sconces"]:
        point("sconce", D.PRIMARY_BATH["room"][0] + 0.55, yy, D.FF + 5.4, 6, radius=0.12)
    spot("dl_shower", 49.5, 78.0, c, 18)
    # pendants
    for (x, y) in ((23.0, 72.0), (26.2, 72.0), (12.5, 71.6), (16.5, 71.6)):
        point("pendant", x, y, D.CEIL - 3.0, 18, radius=0.1)
    # canopy / soffit downlights
    for x in (30.5, 36, 42, 48, 52):
        spot("dl_canopy", x, 33.4, c, 22)
    for x in (20, 26, 32, 38):
        spot("dl_veranda", x, 86.5, c, 26)
    for y in (40, 46, 52):
        spot("dl_eave", 29.6, y, c, 14)
    # limestone grazers (in-grade, aimed up the wall face)
    for x in (6.5, 11.5, 16.5, 21.5, 26.0):
        spot("graze", x, 28.7, 0.15, 26, size=70, blend=0.7, aim=(x, 29.75, 9.0))
    # low path lights along the stepping slabs
    for y in (4.0, 11.0, 18.0, 25.0):
        point("path", 32.6, y, 0.9, 6, radius=0.05)
    # courtyard tree uplights + cobogó backlight (wash the inside face)
    for (x, y) in ((41.5, 45.0), (46.5, 48.5), (44.5, 43.8)):
        spot("tree_up", x, y, D.HARDSCAPE + 0.2, 110, size=50, blend=0.6, aim=(44.0, 46.5, 16.0))
    for x in (36, 42, 48):
        spot("cobogo_back", x, 38.5, D.HARDSCAPE + 0.4, 90, size=95, blend=0.8, aim=(x, 30.5, 5.0))
    # rear oak uplights
    for (x, y) in ((27, 106), (35, 108), (31, 114)):
        spot("oak_up", x, y, 0.2, 160, size=45, blend=0.6, aim=(31.0, 110.0, 25.0))


def set_night(coll, on, level=1.0):
    for ob in coll.objects:
        ob.hide_render = not on
        if on and ob.type == "LIGHT":
            base = ob.get("base_energy", ob.data.energy)
            ob["base_energy"] = base
            ob.data.energy = base * level


# ---------------------------------------------------------------- camera
def set_camera(v, res_x, res_y):
    cam = bpy.data.objects.get("Cam")
    if cam is None:
        cd = bpy.data.cameras.new("Cam")
        cam = bpy.data.objects.new("Cam", cd)
        bpy.context.scene.collection.objects.link(cam)
    cd = cam.data
    if v.get("pano"):
        cd.type = "PANO"
        try:
            cd.panorama_type = "EQUIRECTANGULAR"
        except Exception:
            cd.cycles.panorama_type = "EQUIRECTANGULAR"
    else:
        cd.type = "PERSP"
    cd.lens = v["lens"]
    cd.sensor_width = SENSOR
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 600
    p = Vector(v["cam"]) * M
    t = Vector(v["tgt"]) * M
    d = t - p
    cam.location = p
    yaw = math.atan2(d.y, d.x) - math.pi / 2
    if v.get("pano"):
        cam.rotation_euler = (math.pi / 2, 0, yaw)
        cd.shift_x = cd.shift_y = 0
    elif v.get("two_point", True):
        # level camera; vertical framing via lens shift keeps verticals straight
        cam.rotation_euler = (math.pi / 2, 0, yaw)
        horiz = math.hypot(d.x, d.y)
        cd.shift_y = (v["lens"] * d.z / horiz) / SENSOR
        cd.shift_x = 0
    else:
        pitch = math.atan2(d.z, math.hypot(d.x, d.y))
        cam.rotation_euler = (math.pi / 2 + pitch, 0, yaw)
        cd.shift_y = 0
    bpy.context.scene.camera = cam


def set_ortho(v):
    cam = bpy.data.objects.get("Cam")
    if cam is None:
        cd = bpy.data.cameras.new("Cam")
        cam = bpy.data.objects.new("Cam", cd)
        bpy.context.scene.collection.objects.link(cam)
    cd = cam.data
    cd.type = "ORTHO"
    cd.ortho_scale = v["width"] * M
    cd.sensor_fit = "HORIZONTAL"
    cd.shift_x = cd.shift_y = 0
    cd.clip_start = v.get("clip", 0.1) * M
    cd.clip_end = 1000
    cam.location = Vector(v["center"]) * M
    cam.rotation_euler = tuple(math.radians(a) for a in v["rot"])
    bpy.context.scene.camera = cam


def _ortho_meta(name, v, out):
    import json
    f = os.path.join(out, "ortho_views.json")
    meta = json.load(open(f)) if os.path.exists(f) else {}
    meta[name] = {k: v[k] for k in ("center", "rot", "width", "res")}
    json.dump(meta, open(f, "w"), indent=1)


def setup_render(samples, res_x, res_y):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.015
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    try:
        s.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        s.cycles.denoising_prefilter = "ACCURATE"
        s.cycles.denoising_quality = "HIGH"
    except Exception:
        pass
    s.cycles.max_bounces = 8
    s.cycles.diffuse_bounces = 4
    s.cycles.glossy_bounces = 4
    s.cycles.transmission_bounces = 8
    s.cycles.transparent_max_bounces = 8
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    s.cycles.sample_clamp_indirect = 8.0
    s.cycles.use_light_tree = True
    s.render.resolution_x = res_x
    s.render.resolution_y = res_y
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_depth = "8"
    s.render.use_persistent_data = True
    s.render.threads_mode = "AUTO"
    s.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "AgX - Base Contrast"):
        try:
            s.view_settings.look = look
            break
        except Exception:
            continue


def build_scene():
    reset()
    scene = bpy.context.scene
    root = scene.collection
    L = MAT.build_library()
    arch = new_coll("Architecture", root)
    land = new_coll("Landscape", root)
    furn = new_coll("Furniture", root)
    night = new_coll("NightLights", root)
    protos = load_protos(root)
    t = time.time()
    house.build_house(L, arch)
    print(f"[build] house {time.time() - t:.1f}s"); t = time.time()
    SITE.build_site(L, land, protos)
    print(f"[build] site {time.time() - t:.1f}s"); t = time.time()
    furniture.build_furniture(L, furn, protos)
    build_night_lights(night)
    print(f"[build] furniture+lights {time.time() - t:.1f}s")
    for c in list(root.children):
        if c.name.startswith(("proto", "inst_")) or c.name == "protos":
            exclude(c.name)
    return night


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default="street")
    ap.add_argument("--res", type=int, default=1920)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--save-blend", default="")
    ap.add_argument("--oscale", type=float, default=1.0, help="resolution multiplier for ortho views")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    os.makedirs(args.out, exist_ok=True)
    night = build_scene()
    res_x = args.res
    res_y = int(round(res_x * 9 / 16))
    setup_render(args.samples, res_x, res_y)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=args.save_blend)
    for name in args.views.split(","):
        v = VIEWS[name]
        set_world(v["hdri"], v["sun"], v["strength"])
        set_night(night, v["night"], v.get("night_level", 1.0))
        bpy.context.scene.view_settings.exposure = v["exposure"]
        rs = bpy.context.scene.render
        hidden = []
        if v.get("ortho"):
            set_ortho(v)
            rs.resolution_x, rs.resolution_y = (int(v["res"][0] * args.oscale), int(v["res"][1] * args.oscale))
            for ob in bpy.data.objects:
                if any(ob.name == h or ob.name.startswith(h + "_") for h in v.get("hide", [])):
                    if not ob.hide_render:
                        ob.hide_render = True
                        hidden.append(ob)
            rs.film_transparent = bool(v.get("transparent"))
            _ortho_meta(name, v, args.out)
        else:
            set_camera(v, res_x, res_y)
            rs.film_transparent = False
            rs.resolution_x, rs.resolution_y = (args.res, args.res // 2) if v.get("pano") else (res_x, res_y)
        bpy.context.scene.render.filepath = os.path.join(args.out, f"{name}{args.suffix}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"[render] {name} {rs.resolution_x}x{rs.resolution_y} {args.samples}spp in {time.time() - t:.0f}s", flush=True)
        for ob in hidden:
            ob.hide_render = False


if __name__ == "__main__":
    main()
