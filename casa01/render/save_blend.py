"""Save the full Casa 01 render scene as a .blend you can open in Blender 5.3+.

    python casa01/render/save_blend.py      ->  casa01/blender/casa01.blend

One camera per view (Cam_street, Cam_interior, ...), the street sky loaded,
night lights in their own (hidden) collection. Textures are linked by relative
path to casa01/render/assets/ (run fetch_assets.py first), not packed, so the
file stays small enough for GitHub.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import render as R  # noqa: E402
from geo import M  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "blender", "casa01.blend")


def main():
    night = R.build_scene()
    R.setup_render(128, 1920, 1080)
    R.set_world("afternoon", 232, 1.0)
    R.set_night(night, False)
    night.hide_viewport = True
    cams = bpy.data.collections.new("Cameras")
    bpy.context.scene.collection.children.link(cams)
    for name, v in R.VIEWS.items():
        if v.get("ortho"):
            R.set_ortho(v)
        else:
            R.set_camera(v, 1920, 1080)
        cam = bpy.data.objects["Cam"]
        c = cam.copy()
        c.data = cam.data.copy()
        c.name = f"Cam_{name}"
        cams.objects.link(c)
        for key, prop in (("hdri", "hdri"), ("sun", "sun_azimuth"), ("exposure", "exposure")):
            if key in v:
                c[prop] = v[key]
    bpy.data.objects.remove(bpy.data.objects["Cam"])
    bpy.context.scene.camera = bpy.data.objects["Cam_street"]
    bpy.context.scene.view_settings.exposure = R.VIEWS["street"]["exposure"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(compress=True)
    print(f"[blend] {OUT} {os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
