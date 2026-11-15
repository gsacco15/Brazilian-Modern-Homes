"""Download the CC0 scanned assets used by the renders (Poly Haven + ambientCG).

    python3 casa01/render/fetch_assets.py

Everything lands in casa01/render/assets/ (git-ignored, ~0.6 GB). All assets are
CC0 (public domain): free for commercial use, no attribution required.
"""
import io
import json
import os
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
UA = {"User-Agent": "casa01-render/1.0"}

PH_TEXTURES = {  # poly haven id -> our name
    "white_stucco": "stucco",
    "beige_wall_002": "limestone",
    "gravel_floor": "dg",
    "gravel": "mulch",
    "jolcham_oak_bark_01": "bark",
    "fabric_leather_02": "leather",
    "rough_linen": "linen",
    "clean_asphalt": "asphalt",
    "sparse_grass": "grass_ground",
}
ACG_TEXTURES = {  # ambientCG id -> our name
    "Wood052": "cedar",
    "Wood026": "cedar_red",
    "Wood058": "oak",
    "Wood066": "walnut",
    "Concrete034": "concrete",
}
HDRIS = {
    "kloofendal_48d_partly_cloudy_puresky": "day",
    "qwantani_late_afternoon_puresky": "afternoon",
    "kloppenheim_06_puresky": "golden",
    "qwantani_dusk_2_puresky": "dusk",
}
MODELS = [
    "mid_century_lounge_chair", "modern_arm_chair_01", "dining_chair_02",
    "potted_plant_02", "potted_plant_04", "ceramic_vase_01", "ceramic_vase_03",
    "fern_02", "grass_medium_01", "grass_medium_02", "searsia_lucida",
    "modern_ceiling_lamp_01", "side_table_01", "boulder_01",
]
RES = "2k"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def ph_files(asset):
    return json.loads(get(f"https://api.polyhaven.com/files/{asset}"))


def fetch_ph_texture(asset, name):
    out = os.path.join(ROOT, "textures", name)
    if os.path.isdir(out) and len(os.listdir(out)) >= 3:
        return name, "cached"
    files = ph_files(asset)
    want = {"Diffuse": "color", "nor_gl": "normal", "Rough": "rough", "Displacement": "disp"}
    for k, short in want.items():
        if k in files and RES in files[k]:
            fmt = "jpg" if "jpg" in files[k][RES] else list(files[k][RES])[0]
            save(os.path.join(out, f"{short}.{fmt}"), get(files[k][RES][fmt]["url"]))
    return name, "ok"


def fetch_acg_texture(asset, name):
    out = os.path.join(ROOT, "textures", name)
    if os.path.isdir(out) and len(os.listdir(out)) >= 3:
        return name, "cached"
    z = zipfile.ZipFile(io.BytesIO(get(f"https://ambientcg.com/get?file={asset}_2K-JPG.zip")))
    for n in z.namelist():
        for key, short in (("_Color", "color"), ("_NormalGL", "normal"), ("_Roughness", "rough"),
                           ("_Displacement", "disp")):
            if key in n:
                save(os.path.join(out, f"{short}.jpg"), z.read(n))
    return name, "ok"


def fetch_hdri(asset, name):
    out = os.path.join(ROOT, "hdri", f"{name}.hdr")
    if os.path.exists(out):
        return name, "cached"
    files = ph_files(asset)
    save(out, get(files["hdri"]["4k"]["hdr"]["url"]))
    return name, "ok"


def fetch_model(asset):
    out = os.path.join(ROOT, "models", asset)
    blend = os.path.join(out, f"{asset}.blend")
    if os.path.exists(blend):
        return asset, "cached"
    files = ph_files(asset)
    b = files["blend"][RES]["blend"]
    save(blend, get(b["url"]))
    for rel, info in b.get("include", {}).items():
        save(os.path.join(out, rel), get(info["url"]))
    return asset, "ok"


def prepare():
    """Make square tiles from non-square maps and 90° rotated copies of wood
    so box-projected grain can run vertically (slats) or along soffit boards."""
    from PIL import Image
    tex = os.path.join(ROOT, "textures")
    for name in os.listdir(tex):
        d = os.path.join(tex, name)
        for f in os.listdir(d):
            if f.startswith(("sq_", "rot_")):
                continue
            p = os.path.join(d, f)
            im = Image.open(p)
            w, h = im.size
            out = os.path.join(d, "sq_" + f)
            if not os.path.exists(out):
                if w > h and w % h == 0:       # stack copies (maps are tileable)
                    sq = Image.new(im.mode, (w, w))
                    for k in range(w // h):
                        sq.paste(im, (0, k * h))
                    im2 = sq
                elif h > w and h % w == 0:
                    sq = Image.new(im.mode, (h, h))
                    for k in range(h // w):
                        sq.paste(im, (k * w, 0))
                    im2 = sq
                else:
                    im2 = im.resize((max(w, h), max(w, h)))
                im2.save(out, quality=92)
            if name in ("cedar", "cedar_red", "walnut", "oak"):
                rout = os.path.join(d, "rot_" + f)
                if not os.path.exists(rout):
                    Image.open(out).transpose(Image.Transpose.ROTATE_90).save(rout, quality=92)


def main():
    jobs = []
    with ThreadPoolExecutor(6) as ex:
        jobs += [ex.submit(fetch_ph_texture, a, n) for a, n in PH_TEXTURES.items()]
        jobs += [ex.submit(fetch_acg_texture, a, n) for a, n in ACG_TEXTURES.items()]
        jobs += [ex.submit(fetch_hdri, a, n) for a, n in HDRIS.items()]
        jobs += [ex.submit(fetch_model, a) for a in MODELS]
        for j in jobs:
            try:
                print(*j.result())
            except Exception as e:  # keep going; renders fall back to procedural
                print("FAILED", e, file=sys.stderr)
    prepare()
    print("prepared textures")


if __name__ == "__main__":
    main()
