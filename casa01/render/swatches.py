"""Render the material board: one tile per finish, using the exact render materials.

    python casa01/render/swatches.py   ->  casa01/renders/swatches/<name>.png
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
import materials as MAT  # noqa: E402
import house  # noqa: E402
from geo import MB, M, merge_copies  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "renders", "swatches")

SW = [
    ("limestone", "Lueders limestone"), ("cobogo", "Cobogó block"), ("cedar_z", "Western red cedar"),
    ("stucco", "Warm-white stucco"), ("floor", "Polished concrete"), ("pavers", "Limestone pavers"),
    ("oak", "Rift white oak"), ("granite", "Honed black granite"), ("tile", "Green glazed tile"),
    ("bronze", "Dark bronze metal"), ("dg", "Decomposed granite"), ("linen", "Natural linen"),
]


def main():
    R.reset()
    L = MAT.build_library()
    coll = bpy.context.scene.collection
    os.makedirs(OUT, exist_ok=True)
    T = 2.0  # tile size in feet
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    for key, label in SW:
        if only and key not in only:
            continue
        for o in list(coll.objects):
            bpy.data.objects.remove(o)
        if key == "limestone":
            mb = MB("st", [L["limestone"], L["mortar"]])
            mb.box(-2, -2, -0.3, 2, 2, -0.05, mat=1)
            z = -2
            import random
            rng = random.Random(4)
            for h in (0.667, 0.333, 1.0, 0.333, 0.667, 0.667):
                x = -2 - rng.uniform(0, 1)
                while x < 2:
                    ln = rng.uniform(1.2, 2.6)
                    mb.box(x + 0.015, z + 0.015, -0.05, x + ln - 0.015, z + h - 0.015, 0.0, mat=0, r=rng.random())
                    x += ln
                z += h
            mb.build(coll, bevel=0.003)
        elif key == "cobogo":
            blk = house.make_cobogo_block(L, coll)
            offs = []
            for i in range(-2, 3):
                for k in range(-2, 3):
                    offs.append((i * 0.3048, 0, k * 0.3048))
            ob = merge_copies(blk, offs, "cob", coll)
            ob.rotation_euler = (math.pi / 2, 0, 0)
            mb = MB("back", [L["pavers"]])
            mb.box(-3, -3, -1.6, 3, 3, -1.5)
            mb.build(coll)
        elif key in ("cedar_z",):
            mb = MB("boards", [L["cedar_x"]])
            y = -2
            import random
            rng = random.Random(2)
            while y < 2:
                mb.box(-2, y, -0.1, 2, y + 0.45, 0.0, r=rng.random())
                y += 0.47
            mb.build(coll, bevel=0.002)
        else:
            mb = MB("tile", [L[key]])
            mb.box(-2, -2, -0.1, 2, 2, 0.0, r=0.37)
            mb.build(coll, bevel=0.002)
        cd = bpy.data.cameras.new("c")
        cd.type = "ORTHO"
        cd.ortho_scale = T * M
        cam = bpy.data.objects.new("c", cd)
        cam.location = (0, 0, 3)
        coll.objects.link(cam)
        bpy.context.scene.camera = cam
        sun = bpy.data.lights.new("s", "SUN")
        sun.energy = 3.2
        sun.angle = math.radians(8)
        so = bpy.data.objects.new("s", sun)
        so.rotation_euler = (math.radians(38), 0, math.radians(35))
        coll.objects.link(so)
        R.setup_render(64, 600, 600)
        R.set_world("day", 200, 0.6)
        bpy.context.scene.view_settings.exposure = {"cedar_z": -1.1, "oak": -0.2}.get(key, -0.4)
        bpy.context.scene.render.filepath = os.path.join(OUT, f"{key}.png")
        bpy.ops.render.render(write_still=True)
        print("[swatch]", key, flush=True)


if __name__ == "__main__":
    main()
