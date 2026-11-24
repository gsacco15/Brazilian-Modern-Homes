"""Three-option facade study for Casa 02 (plus the Casita upgrade), rendered from the shared model.

    <bpy venv>/bin/python phase2/study/facade_study.py [--options base,A,B,C,Cplus] [--views ...] [--res 1100]
        -> phase2/study/out/<option>_<view>.png

Same plans, same lots, same camera for every option; only the street face changes (see phase2/render/build.py).
Views: L1-D1 street by day and at dusk, L1-D1 aerial, L2-T2 street by day and at dusk (the Casita and its
garden wall). Cplus, the chosen direction, is rendered with --views alley_trio,alley_dusk; its duo is C's.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P2 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P2, "render"))
import bpy  # noqa: E402
import build as B  # noqa: E402  (phase2/render/build.py)

OUT = os.path.join(HERE, "out")
SITE = {fn().get("id"): fn for fn in B.SITES}
VIEWS = {
    "street": ("L1-D1", dict(cam=(36, -27, 5.5), tgt=(24, 22, 11.5), lens=22), "day"),
    "dusk": ("L1-D1", dict(cam=(36, -27, 5.5), tgt=(24, 22, 11.5), lens=22), "dusk"),
    "aerial": ("L1-D1", dict(cam=(98, -48, 72), tgt=(25, 52, 4), lens=30, two_point=False), "day"),
    "alley_trio": ("L2-T2", dict(cam=(40, -26, 5.5), tgt=(22, 40, 10), lens=22), "day"),
    "alley_dusk": ("L2-T2", dict(cam=(40, -26, 5.5), tgt=(22, 40, 10), lens=22), "dusk"),
}


def dusk_lights(s, fac):
    """Warm light inside every home, each floor, plus one behind each cobogó stair."""
    for h in s["homes"]:
        plan, t = h["plan"], h["t"]
        casa = not B.H.is_casita(plan)
        step = 8.0 if (casa and fac == "B") else 0.0
        spots = [(plan["W"] / 2, plan["D"] * 0.3, B.FF + 7.5), (plan["W"] / 2, plan["D"] * 0.75, B.FF + 7.5)]
        if casa:
            spots += [(plan["W"] / 2, plan["D"] * 0.3 + step, B.UP_FF + 7.0),
                      (plan["W"] / 2, plan["D"] * 0.75 + step, B.UP_FF + 7.0), (18.2, 3.0, B.FF + 6), (18.2, 3.0, B.UP_FF + 4)]
        if casa and fac in ("C", "Cplus"):   # lights in the gap behind the cobogó wash it from inside
            spots += [(x, -0.5, z) for x in (12.0, 15.5, 19.0) for z in (3.0, 9.0, 14.5, 19.5)]
        for i, (x, y, z) in enumerate(spots):
            X, Y = B.tp(t, x, y)
            ld = bpy.data.lights.new(f"{h['id']} glow {i}", "POINT")
            ld.energy = 220 if i < 4 else (140 if i < 6 else 45)
            ld.color = (1.0, 0.72, 0.45)
            ld.shadow_soft_size = 0.6
            ob = bpy.data.objects.new(ld.name, ld)
            ob.location = (X * B.M, Y * B.M, z * B.M)
            bpy.context.scene.collection.objects.link(ob)
    sw = s.get("street_wall")
    if sw and fac != "base":             # the Casita's garden: a lamp under the porch and a glow behind the cobogó
        (x0, y0), (x1, _y1) = sw
        for i, (x, y, z, e) in enumerate([(x0 + 4, y0 + 3, 9.5, 120)] +
                                         [(x, y0 + 1.2, z, 35) for x in (x0 + 9, x0 + 13, x1 - 4) for z in (2.5, 6.0)]):
            ld = bpy.data.lights.new(f"garden glow {i}", "POINT")
            ld.energy, ld.color, ld.shadow_soft_size = e, (1.0, 0.72, 0.45), 0.6
            ob = bpy.data.objects.new(ld.name, ld)
            ob.location = (x * B.M, y * B.M, z * B.M)
            bpy.context.scene.collection.objects.link(ob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--options", default="base,A,B,C")
    ap.add_argument("--res", type=int, default=1100)
    ap.add_argument("--samples", type=int, default=28)
    ap.add_argument("--views", default="street,dusk,aerial,alley_trio")
    a = ap.parse_args([x for x in sys.argv[1:] if x != "--"])
    os.makedirs(OUT, exist_ok=True)
    rx, ry = a.res, int(a.res * 9 / 16)
    for fac in a.options.split(","):
        for site_id in ("L1-D1", "L2-T2"):
            if not any(VIEWS[v][0] == site_id for v in a.views.split(",")):
                continue
            s = SITE[site_id]()
            B.R.reset()
            B._COBOGO.clear()
            L = B.MAT.build_library()
            B.build_site(s, L, fac)
            B.R.setup_render(a.samples, rx, ry)
            for name, (sid, v, light) in VIEWS.items():
                if sid != site_id or name not in a.views.split(","):
                    continue
                if light == "dusk":
                    dusk_lights(s, fac)
                    B.R.set_world("dusk", 290, 0.07)            # Casa 01's dusk settings
                    bpy.context.scene.view_settings.exposure = 0.9
                    bpy.context.scene.cycles.samples = int(a.samples * 1.5)
                else:
                    B.R.set_world("day", 215, 1.0)
                    bpy.context.scene.view_settings.exposure = -0.3
                    bpy.context.scene.cycles.samples = a.samples
                B.R.set_camera(v, rx, ry)
                bpy.context.scene.render.filepath = os.path.join(OUT, f"{fac}_{name}.png")
                bpy.ops.render.render(write_still=True)
                print(f"[study] {fac} {name}", flush=True)


if __name__ == "__main__":
    main()
