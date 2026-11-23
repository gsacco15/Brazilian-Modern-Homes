"""Phase 2 AutoCAD file: every home plan as a block, every site built from those blocks, one sheet per layout.

    PYTHONPATH=<ezdxf> python3 phase2/cad/export_dxf.py      ->  phase2/cad/Phase2_Concepts.dxf

Units are inches (architectural). Model space holds:
  - the four plans side by side (blocks C02-GC, C02-GS, C02-UP, CS) with room names and dimensions;
  - the five sites to the right, each built by inserting those blocks (mirrored or rotated as the site needs).
Edit a block once and every site that uses it updates.
Paper space has one layout per sheet: C-1 Casa 02, C-2 Casita, C-3..C-7 one per site, each with a title block
and a viewport at a standard architectural scale.
"""
import math
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from model import homes as H  # noqa: E402
from model.sites import SITES, HOME_RULES, footprint, tp  # noqa: E402

OUT = os.path.join(HERE, "Phase2_Concepts.dxf")
IN = 12.0  # inches per foot

LAYERS = [  # name, colour, lineweight (1/100 mm), linetype
    ("A-WALL", 7, 50, "Continuous"), ("A-WALL-INTR", 7, 35, "Continuous"), ("A-WALL-PATT", 8, 0, "Continuous"),
    ("A-DOOR", 3, 18, "Continuous"), ("A-GLAZ", 4, 18, "Continuous"), ("A-FLOR-FIXT", 8, 13, "Continuous"),
    ("A-FURN", 9, 13, "Continuous"), ("A-FLOR-STRS", 7, 18, "Continuous"), ("A-COLS", 7, 35, "Continuous"),
    ("A-GATE", 30, 25, "DASHED"), ("A-OVHD", 8, 18, "DASHED"), ("A-AREA-IDEN", 7, 18, "Continuous"),
    ("A-ANNO-DIMS", 7, 13, "Continuous"), ("A-ANNO-TEXT", 7, 18, "Continuous"),
    ("C-PROP", 1, 35, "PHANTOM"), ("C-SETB", 8, 13, "DASHED"), ("C-ROAD", 8, 13, "Continuous"),
    ("C-PAVE", 8, 13, "Continuous"), ("L-PLNT", 3, 13, "Continuous"), ("L-TREE", 3, 18, "Continuous"),
    ("L-FENC", 30, 25, "Continuous"), ("L-WALL", 7, 35, "Continuous"), ("L-PATH", 8, 13, "Continuous"),
    ("G-TTLB", 7, 35, "Continuous"), ("G-TTLB-TEXT", 7, 18, "Continuous"), ("G-VPRT", 8, 13, "Continuous"),
]

PLANS = [("C02-GC", H.CASA02_GF_CARPORT, "CASA 02 - GROUND FLOOR, CARPORT"),
         ("C02-GS", H.CASA02_GF_SUITE, "CASA 02 - GROUND FLOOR, SUITE"),
         ("C02-UP", H.CASA02_UPPER, "CASA 02 - UPPER FLOOR (BOTH VERSIONS)"),
         ("CS", H.CASITA, "CASITA")]
BLOCK_OF = {id(p): name for name, p, _ in PLANS}


def ft_in(v):
    f = int(v + 1e-6)
    i = round((v - f) * 12)
    if i == 12:
        f, i = f + 1, 0
    return f"{f}'-{i}\""


# ---------------------------------------------------------------- plan geometry into a block
def pts_in(pts):
    return [(x * IN, y * IN) for x, y in pts]


def ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def build_block(doc, name, plan):
    blk = doc.blocks.new(name=name)

    def poly(pts, layer, closed=True, hatch=False):
        p = pts_in(pts)
        blk.add_lwpolyline(p, close=closed, dxfattribs={"layer": layer})
        if hatch:
            h = blk.add_hatch(color=7, dxfattribs={"layer": "A-WALL-PATT"})
            h.paths.add_polyline_path(p, is_closed=True)

    def line(a, b, layer):
        blk.add_line((a[0] * IN, a[1] * IN), (b[0] * IN, b[1] * IN), dxfattribs={"layer": layer})

    for w in plan["walls"]:
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        th = w["t"]
        d0, d1 = (0.0, th) if w["ext"] else (-th / 2, th / 2)
        layer = "A-WALL" if w["ext"] else "A-WALL-INTR"

        def P(s, d):
            return (ax + ux * s + nx * d, ay + uy * s + ny * d)
        cuts = sorted(w["openings"], key=lambda o: o["off"])
        s = 0.0
        for o in cuts + [dict(off=L, w=0, kind="end")]:
            if o["off"] - s > 1e-6:
                poly([P(s, d0), P(o["off"], d0), P(o["off"], d1), P(s, d1)], layer, hatch=True)
            s = o["off"] + o["w"]
        for o in cuts:
            s0, s1 = o["off"], o["off"] + o["w"]
            if o["kind"] in ("window", "slider"):
                line(P(s0, d0), P(s0, d1), "A-GLAZ")
                line(P(s1, d0), P(s1, d1), "A-GLAZ")
                if o["kind"] == "window":
                    for f in (0.38, 0.62):
                        line(P(s0, d0 + (d1 - d0) * f), P(s1, d0 + (d1 - d0) * f), "A-GLAZ")
                else:
                    mid = (s0 + s1) / 2
                    line(P(s0, d0 + (d1 - d0) * 0.3), P(mid + 0.25, d0 + (d1 - d0) * 0.3), "A-GLAZ")
                    line(P(mid - 0.25, d0 + (d1 - d0) * 0.7), P(s1, d0 + (d1 - d0) * 0.7), "A-GLAZ")
            elif o["kind"] == "door":
                sg = 1.0 if o["side"] == "L" else -1.0
                face = d1 if sg > 0 else d0
                hs, cs = (s0, s1) if o["hinge"] == "s" else (s1, s0)
                hx, hy = P(hs, face)
                cx_, cy_ = P(cs, face)
                ex, ey = hx + nx * sg * o["w"], hy + ny * sg * o["w"]
                line((hx, hy), (ex, ey), "A-DOOR")
                a0 = math.degrees(math.atan2(cy_ - hy, cx_ - hx))
                a1 = math.degrees(math.atan2(ey - hy, ex - hx))
                d = (a1 - a0 + 180) % 360 - 180
                start, end = (a0, a1) if d > 0 else (a1, a0)
                blk.add_arc((hx * IN, hy * IN), o["w"] * IN, start, end, dxfattribs={"layer": "A-DOOR"})
    for f in plan.get("fixtures", []):
        k = f["kind"]
        lay = "A-FURN" if k in ("bed", "sofa", "table", "car") else "A-FLOR-FIXT"
        if k == "wc":
            x, y = f["at"]
            dirn = 1 if f.get("rot", 0) == 0 else -1
            poly([(x - 0.85, y - 0.3), (x + 0.85, y - 0.3), (x + 0.85, y + 0.3), (x - 0.85, y + 0.3)], lay)
            poly(ellipse(x, y + dirn * 1.25, 0.62, 0.92), lay)
            continue
        x0, y0, x1, y1 = f["rect"]
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if k == "range":
            for ox in (-0.5, 0.5):
                for oy in (-0.45, 0.45):
                    blk.add_circle(((cx + ox) * IN, (cy + oy) * IN), 0.32 * IN, dxfattribs={"layer": lay})
        elif k in ("sink", "lav"):
            poly(ellipse(cx, cy, (x1 - x0) * 0.32, (y1 - y0) * 0.32), lay)
        elif k == "shower":
            blk.add_circle((cx * IN, cy * IN), 0.18 * IN, dxfattribs={"layer": lay})
            line((x0, y0), (x1, y1), lay)
        elif k == "bed":
            for px0 in (x0 + 0.3, cx + 0.15):
                poly([(px0, y1 - 1.3), (px0 + (x1 - x0) / 2 - 0.45, y1 - 1.3), (px0 + (x1 - x0) / 2 - 0.45, y1 - 0.3),
                      (px0, y1 - 0.3)], lay)
            line((x0, y1 - 2.0), (x1, y1 - 2.0), lay)
        elif k == "wd":
            if (x1 - x0) >= (y1 - y0):
                line(((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), lay)
            else:
                line((x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2), lay)
        elif k == "car":
            pass
    st = plan.get("stair")
    if st:
        x0, y0, x1, y1 = st["rect"]
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "A-FLOR-STRS")
        n = int((y1 - y0) / 0.8333)
        for i in range(1, n + 1):
            y = y0 + i * (y1 - y0) / (n + 1)
            line((x0, y), (x1, y), "A-FLOR-STRS")
        cx = (x0 + x1) / 2
        line((cx, y0 + 0.6), (cx, y1 - 0.6), "A-FLOR-STRS")
        tip = (cx, y1 - 0.3) if st["up"] else (cx, y0 + 0.3)
        back = -0.6 if st["up"] else 0.6
        poly([tip, (cx - 0.3, tip[1] + back), (cx + 0.3, tip[1] + back)], "A-FLOR-STRS")
    if any(r.get("outdoor") for r in plan["rooms"]):
        poly([(0, 0), (plan["W"], 0), (plan["W"], plan["D"]), (0, plan["D"])], "A-OVHD")
    for cx, cy in plan.get("columns", []):
        poly([(cx - 0.3, cy - 0.3), (cx + 0.3, cy - 0.3), (cx + 0.3, cy + 0.3), (cx - 0.3, cy + 0.3)], "A-COLS", hatch=True)
    if plan.get("gate"):
        (gx0, gy0), (gx1, gy1) = plan["gate"]
        line((gx0, gy0 + 0.25), (gx1, gy1 + 0.25), "A-GATE")
    return blk


# ---------------------------------------------------------------- model space helpers
def text(msp, x, y, s, h, layer="A-ANNO-TEXT", align=TextEntityAlignment.MIDDLE_CENTER):
    t = msp.add_text(s, height=h, dxfattribs={"layer": layer, "style": "LATO"})
    t.set_placement((x, y), align=align)
    return t


def rect(msp, x0, y0, x1, y1, layer, hatch=None, color=None):
    p = [(x0 * IN, y0 * IN), (x1 * IN, y0 * IN), (x1 * IN, y1 * IN), (x0 * IN, y1 * IN)]
    msp.add_lwpolyline(p, close=True, dxfattribs={"layer": layer})
    if hatch:
        h = msp.add_hatch(color=color or 8, dxfattribs={"layer": layer})
        if hatch == "SOLID":
            h.set_solid_fill(color=color or 254)
        else:
            h.set_pattern_fill(hatch, scale=hatch_scale(hatch))
        h.paths.add_polyline_path(p, is_closed=True)


def hatch_scale(name):
    return {"GRASS": 14.0, "AR-SAND": 3.0, "AR-CONC": 1.5, "ANSI31": 12.0, "DOTS": 8.0}.get(name, 6.0)


def dim(msp, a, b, base, angle=0):
    length = abs(b[1] - a[1]) if angle == 90 else abs(b[0] - a[0])
    d = msp.add_linear_dim(base=(base[0] * IN, base[1] * IN), p1=(a[0] * IN, a[1] * IN), p2=(b[0] * IN, b[1] * IN),
                           angle=angle, text=ft_in(length), dimstyle="ARCH", dxfattribs={"layer": "A-ANNO-DIMS"})
    d.render()


def insert(msp, block, t, origin):
    """Insert a home block where transform t puts it, shifted by the site's origin (ft)."""
    x, y = tp(t, 0.0, 0.0)
    return msp.add_blockref(block, ((x + origin[0]) * IN, (y + origin[1]) * IN),
                            dxfattribs={"rotation": t["rot"], "xscale": -1 if t["mirror"] else 1, "layer": "0"})


def room_labels(msp, plan, t, origin, h, dims=True):
    for room in plan["rooms"]:
        if room.get("label") is False:
            continue
        x0, y0, x1, y1 = room["rect"]
        lx, ly = room.get("lab", ((x0 + x1) / 2, (y0 + y1) / 2)) if dims else ((x0 + x1) / 2, (y0 + y1) / 2)
        X, Y = tp(t, lx, ly) if t else (lx, ly)
        X, Y = (X + origin[0]) * IN, (Y + origin[1]) * IN
        narrow = (x1 - x0) < 7.5
        name = room.get("short", room["name"]) if (narrow or not dims) else room["name"]
        text(msp, X, Y + (h * 0.6 if dims and not narrow else 0), name.upper(), h, "A-AREA-IDEN")
        if dims and not narrow:
            text(msp, X, Y - h * 0.8, f"{ft_in(x1 - x0)} x {ft_in(y1 - y0)}", h * 0.75, "A-AREA-IDEN")


# ---------------------------------------------------------------- sites in model space
def draw_site(msp, s, origin):
    ox, oy = origin
    W, L = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    # street, alley, side street
    rect(msp, ox - 6, oy - 14, ox + W + (13 if lot.get("corner") else 6), oy - 6, "C-ROAD")
    text(msp, (ox + W / 2) * IN, (oy - 10) * IN, "STREET", 18, "C-ROAD")
    if lot.get("alley"):
        rect(msp, ox - 6, oy + L + 1, ox + W + 6, oy + L + 13, "C-ROAD")
        text(msp, (ox + W / 2) * IN, (oy + L + 7) * IN, "ALLEY", 18, "C-ROAD")
    if lot.get("corner"):
        rect(msp, ox + W + 1, oy - 14, ox + W + 13, oy + L + 6, "C-ROAD")
        t = text(msp, (ox + W + 7) * IN, (oy + L / 2) * IN, "SIDE STREET", 18, "C-ROAD")
        t.dxf.rotation = 90
    # lot line and setbacks
    rect(msp, ox, oy, ox + W, oy + L, "C-PROP")
    rect(msp, ox + HOME_RULES["side"], oy + HOME_RULES["front"], ox + W - HOME_RULES["side"],
         oy + L - HOME_RULES["rear"], "C-SETB")
    for p in s["patios"]:
        rect(msp, ox + p[0], oy + p[1], ox + p[2], oy + p[3], "L-PLNT", hatch="GRASS", color=3)
    for k, r in s["pave"]:
        rect(msp, ox + r[0], oy + r[1], ox + r[2], oy + r[3], "C-PAVE", hatch="AR-CONC" if k != "Terrace" else "AR-SAND",
             color=8)
        if k in ("Drive", "Parking") and (r[3] - r[1]) > 12:
            t = text(msp, (ox + (r[0] + r[2]) / 2) * IN, (oy + (r[1] + r[3]) / 2) * IN, k.upper(), 14, "C-PAVE")
            if (r[2] - r[0]) < (r[3] - r[1]):
                t.dxf.rotation = 90
    for pts in s.get("paths", []):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 2.2))
            for i in range(n):
                f = (i + 0.5) / n
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                rect(msp, ox + x - 0.8, oy + y - 0.55, ox + x + 0.8, oy + y + 0.55, "L-PATH")
    for x, y, r in s["trees"]:
        msp.add_circle(((ox + x) * IN, (oy + y) * IN), r * IN, dxfattribs={"layer": "L-TREE"})
        msp.add_circle(((ox + x) * IN, (oy + y) * IN), 0.4 * IN, dxfattribs={"layer": "L-TREE"})
    for pts in s.get("fence", []):
        msp.add_lwpolyline([((ox + x) * IN, (oy + y) * IN) for x, y in pts], dxfattribs={"layer": "L-FENC"})
    for pts in s.get("walls", []) + ([s["street_wall"]] if s.get("street_wall") else []):
        msp.add_lwpolyline([((ox + x) * IN, (oy + y) * IN) for x, y in pts], dxfattribs={"layer": "L-WALL",
                                                                                         "const_width": 6})
    for h in s["homes"]:
        insert(msp, BLOCK_OF[id(h["plan"])], h["t"], origin)
        room_labels(msp, h["plan"], h["t"], origin, 9, dims=False)
        x0, y0, x1, y1 = footprint(h["t"])
        tx, ty = h.get("tag") or ((x0 + x1) / 2, (y0 - 2.4 if y0 > 18 else y1 + 3.2))
        fa = h["plan"]["enclosed"] + (H.CASA02_UPPER["enclosed"] if h["plan"] is not H.CASITA else 0)
        text(msp, (ox + tx) * IN, (oy + ty) * IN, f"{h['id']} - {h['kind'].upper()}", 15)
        text(msp, (ox + tx) * IN, (oy + ty - 1.6) * IN, f"{h['beds']} - {fa:,.0f} SF", 11)
    dim(msp, (ox, oy + L), (ox + W, oy + L), (ox, oy + L + (16 if lot.get("alley") else 4)))
    dim(msp, (ox, oy), (ox, oy + L), (ox - 4, oy), angle=90)
    text(msp, (ox + W / 2) * IN, (oy - 20) * IN, f"{s['id']}  {s['name'].upper()}", 24)


# ---------------------------------------------------------------- paper space
def title_block(lay, sheet, title, scale):
    """17 x 11 in sheet: border, a 2.3 in title strip on the right."""
    def r(x0, y0, x1, y1):
        lay.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "G-TTLB"})

    def t(x, y, s, h, align=TextEntityAlignment.LEFT):
        e = lay.add_text(s, height=h, dxfattribs={"layer": "G-TTLB-TEXT", "style": "LATO"})
        e.set_placement((x, y), align=align)
    r(0.35, 0.35, 14.15, 10.65)
    r(14.35, 0.35, 16.65, 10.65)
    t(14.5, 10.3, "BRAZILIAN MODERN HOMES", 0.11)
    t(14.5, 10.08, "RESIDENTIAL DESIGN - AUSTIN", 0.08)
    t(14.5, 9.6, "PHASE 2", 0.16)
    t(14.5, 9.35, "CASA 02 + CASITA", 0.16)
    t(14.5, 9.05, "CONCEPT DESIGN", 0.08)
    t(14.5, 2.75, "SHEET TITLE", 0.07)
    t(14.5, 2.55, title, 0.12)
    t(14.5, 2.25, "SCALE", 0.07)
    t(14.5, 2.05, scale, 0.12)
    t(14.5, 1.75, "DATE / PHASE", 0.07)
    t(14.5, 1.55, "NOV 2026 - CONCEPT", 0.12)
    t(14.5, 0.85, sheet, 0.5)
    t(14.5, 0.5, "CONCEPT. NOT FOR CONSTRUCTION.", 0.07)


def sheet(doc, name, sheet_no, title, scale_txt, scale, center_ft, size_in=(13.4, 9.9)):
    lay = doc.layouts.new(name)
    lay.page_setup(size=(17, 11), margins=(0, 0, 0, 0), units="inch")
    title_block(lay, sheet_no, title, scale_txt)
    cx, cy = 0.35 + 0.4 + size_in[0] / 2, 0.35 + 0.35 + size_in[1] / 2
    vp = lay.add_viewport(center=(cx, cy), size=size_in, view_center_point=(center_ft[0] * IN, center_ft[1] * IN),
                          view_height=size_in[1] * scale, dxfattribs={"layer": "G-VPRT"})
    vp.dxf.status = 1
    return lay


def main():
    doc = ezdxf.new("R2018", setup=True, units=ezdxf.units.IN)
    doc.header["$MEASUREMENT"] = 0
    doc.header["$LUNITS"] = 4          # architectural
    doc.header["$INSUNITS"] = 1        # inches
    doc.styles.new("LATO", dxfattribs={"font": "arial.ttf"})
    for name, color, lw, lt in LAYERS:
        doc.layers.add(name, color=color, lineweight=lw, linetype=lt)
    ds = doc.dimstyles.new("ARCH")
    ds.dxf.dimlunit = 4
    ds.dxf.dimtxt = 9
    ds.dxf.dimasz = 0
    ds.dxf.dimtsz = 4
    ds.dxf.dimexe = 4
    ds.dxf.dimexo = 4
    ds.dxf.dimgap = 3
    ds.dxf.dimdec = 0
    ds.dxf.dimtad = 1
    ds.dxf.dimtxsty = "LATO"
    for name, plan, _ in PLANS:
        build_block(doc, name, plan)
    msp = doc.modelspace()

    # plans, side by side, 32 ft apart
    plan_x = {}
    for i, (name, plan, title) in enumerate(PLANS):
        ox = i * 32.0
        plan_x[name] = ox
        msp.add_blockref(name, (ox * IN, 0), dxfattribs={"layer": "0"})
        room_labels(msp, plan, None, (ox, 0), 9)
        dim(msp, (ox, 0), (ox + plan["W"], 0), (ox, -4))
        dim(msp, (ox + plan["W"], 0), (ox + plan["W"], plan["D"]), (ox + plan["W"] + 4, 0), angle=90)
        text(msp, (ox + plan["W"] / 2) * IN, -9 * IN, title, 12)

    # sites, to the right of the plans
    site_origin = {}
    x = 150.0
    for fn in SITES:
        s = fn()
        site_origin[s["id"]] = (x, 0.0)
        draw_site(msp, s, (x, 0.0))
        x += 250.0          # wider than a sheet's viewport, so each sheet shows one site

    # sheets
    sheet(doc, "C-1 Casa 02", "C-1", "CASA 02 PLANS", '1/8" = 1\'-0"', 96, (plan_x["C02-UP"] / 2 + 10, 18))
    sheet(doc, "C-2 Casita", "C-2", "CASITA PLAN", '1/4" = 1\'-0"', 48, (plan_x["CS"] + 10, 14))
    for i, fn in enumerate(SITES):
        s = fn()
        ox, oy = site_origin[s["id"]]
        sheet(doc, f"C-{i + 3} {s['id']}", f"C-{i + 3}", f"SITE {s['id']}", '1/16" = 1\'-0"', 192,
              (ox + s["lot"]["W"] / 2, oy + s["lot"]["L"] / 2 - 8))
    if "Layout1" in doc.layouts:
        doc.layouts.delete("Layout1")
    doc.saveas(OUT)
    print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB", "blocks:", [p[0] for p in PLANS],
          "layouts:", [l.name for l in doc.layouts if l.name != "Model"])


if __name__ == "__main__":
    main()
