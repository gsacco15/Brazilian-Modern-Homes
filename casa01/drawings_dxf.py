"""Export the construction floor plan to DXF for AutoCAD (real size, inches, named layers).

    pip install ezdxf
    python3 casa01/drawings_dxf.py            ->  casa01/drawings/dxf/A-101_Floor_Plan.dxf

Reads drawings/30_floor_plan_cd.svg, which drawings_cd.py writes with a CAD layer on every
element (data-layer) and its feet-to-pixel mapping on the root. Open the DXF in AutoCAD and
SAVEAS to get a DWG.
"""
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

import ezdxf
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "drawings", "30_floor_plan_cd.svg")
OUT = os.path.join(HERE, "drawings", "dxf", "A-101_Floor_Plan.dxf")
NS = "{http://www.w3.org/2000/svg}"

# layer: (AutoCAD color index, linetype, lineweight in 1/100 mm, description)
LAYERS = {
    "A-WALL": (7, "Continuous", 50, "Exterior walls"),
    "A-WALL-INTR": (7, "Continuous", 35, "Interior partitions"),
    "A-WALL-STONE": (41, "Continuous", 35, "Lueders limestone veneer"),
    "A-WALL-COBO": (9, "Continuous", 18, "Concrete cobogo screen"),
    "A-DOOR": (3, "Continuous", 25, "Doors, swings, gate"),
    "A-GLAZ": (4, "Continuous", 18, "Windows and glass"),
    "A-SCRN": (30, "Continuous", 18, "Cedar slat screen"),
    "S-COLS": (7, "Continuous", 35, "Steel posts"),
    "A-FLOR-CASE": (6, "Continuous", 18, "Casework and built-ins"),
    "A-FLOR-APPL": (6, "Continuous", 18, "Appliances"),
    "P-FIXT": (5, "Continuous", 18, "Plumbing fixtures"),
    "A-FLOR-PATT": (8, "Continuous", 9, "Floor tile pattern"),
    "L-PAVE": (8, "Continuous", 13, "Paving, entry calcada"),
    "L-PLNT": (94, "DASHED", 13, "Planting bed"),
    "A-ROOF-OTLN": (1, "PHANTOM", 18, "Roof edge above"),
    "A-GRID": (8, "CENTER", 13, "Column grid"),
    "A-ANNO-DIMS": (2, "Continuous", 13, "Dimensions"),
    "A-ANNO-ROOM": (7, "Continuous", 13, "Room names and areas"),
    "A-DOOR-IDEN": (3, "Continuous", 13, "Door tags"),
    "A-GLAZ-IDEN": (4, "Continuous", 13, "Window tags"),
    "A-ANNO-KEYN": (2, "Continuous", 13, "Keynotes"),
    "A-ANNO-SYMB": (7, "Continuous", 13, "North arrow, markers, scale bar"),
    "A-ROOF-SKYL": (6, "DASHED", 18, "Skylights above"),
    "M-HVAC": (140, "Continuous", 13, "AC pad, air handlers, dropped-ceiling zones"),
}
PATTERNS = {"wallh": ("ANSI31", 12), "stoneh": ("ANSI33", 12), "paverh": ("NET", 192),
            "cdmosaic": ("GRAVEL", 6), "tileh": ("NET", 24)}
DARK = {"#111315", "#23262a", "#2b2e31", "#000000", "#1d2520"}
DASHES = {"14 4 3 4": "CENTER", "10 4 2 4": "PHANTOM"}


# ---------------------------------------------------------------- 2D affine helpers
def mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def parse_transform(s):
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(t) for t in re.split(r"[\s,]+", args.strip()) if t]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            a = math.radians(v[0])
            r = (math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            if len(v) == 3:
                t = mul(mul((1, 0, 0, 1, v[1], v[2]), r), (1, 0, 0, 1, -v[1], -v[2]))
            else:
                t = r
        elif name == "matrix":
            t = tuple(v)
        else:
            continue
        m = mul(m, t)
    return m


def apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def nums(s):
    return [float(t) for t in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", s or "")]


# ---------------------------------------------------------------- SVG path -> polylines
def path_polylines(d):
    toks = re.findall(r"[MmLlHhVvZzAaCcQqSsTt]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cur, pos, start, i, cmd = [], [], (0.0, 0.0), (0.0, 0.0), 0, None

    def take(n):
        nonlocal i
        v = [float(t) for t in toks[i:i + n]]
        i += n
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append(start)
                    out.append(cur)
                cur, pos = [], start
                continue
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = pos if rel else (0.0, 0.0)
        if C == "M":
            x, y = take(2)
            if cur:
                out.append(cur)
            pos = start = (ox + x, oy + y)
            cur = [pos]
            cmd = "l" if rel else "L"
        elif C == "L":
            x, y = take(2)
            pos = (ox + x, oy + y)
            cur.append(pos)
        elif C == "H":
            (x,) = take(1)
            pos = ((pos[0] if rel else 0) + x, pos[1])
            cur.append(pos)
        elif C == "V":
            (y,) = take(1)
            pos = (pos[0], (pos[1] if rel else 0) + y)
            cur.append(pos)
        elif C == "A":
            rx, ry, rot, large, sweep, x, y = take(7)
            end = (ox + x, oy + y)
            cur.extend(arc_points(pos, end, rx, ry, rot, int(large), int(sweep)))
            pos = end
        elif C in "CSQT":   # not used by these drawings: straight to the end point
            n = {"C": 6, "S": 4, "Q": 4, "T": 2}[C]
            v = take(n)
            pos = (ox + v[-2], oy + v[-1])
            cur.append(pos)
        else:
            i += 1
    if cur:
        out.append(cur)
    return [p for p in out if len(p) > 1]


def arc_points(p0, p1, rx, ry, rot, large, sweep):
    """SVG endpoint arc -> points (spec F.6.5), excluding p0."""
    if rx == 0 or ry == 0:
        return [p1]
    phi = math.radians(rot)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1 ** 2 / rx ** 2 + y1 ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1 ** 2 - ry ** 2 * x1 ** 2
    den = rx ** 2 * y1 ** 2 + ry ** 2 * x1 ** 2
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(4, int(abs(dt) / math.radians(6)))
    pts = []
    for k in range(1, n + 1):
        t = t1 + dt * k / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cp * x - sp * y + cx, sp * x + cp * y + cy))
    return pts


# ---------------------------------------------------------------- converter
class Converter:
    def __init__(self, root):
        g = lambda k, d: float(root.get(k, d))
        self.x0, self.y0, self.y1 = g("data-x0", 0), g("data-y0", 0), g("data-y1", 0)
        self.pad, self.s = g("data-pad", 0), g("data-scale", 1)
        self.flip = root.get("data-flip", "1") == "1"
        self.doc = ezdxf.new("R2010", setup=True)
        self.doc.units = ezdxf.units.IN
        h = self.doc.header
        h["$MEASUREMENT"] = 0
        h["$LUNITS"] = 4          # architectural
        h["$LUPREC"] = 4
        h["$LTSCALE"] = 24.0
        self.doc.styles.add("ARCH", font="arial.ttf")
        for name, (color, lt, lw, desc) in LAYERS.items():
            lay = self.doc.layers.add(name, color=color, linetype=lt)
            lay.dxf.lineweight = lw
            lay.description = desc
        self.msp = self.doc.modelspace()
        self.count = {}

    def P(self, m, x, y):
        X, Y = apply(m, x, y)
        fx = self.x0 + (X - self.pad) / self.s
        fy = (self.y1 - (Y - self.pad) / self.s) if self.flip else (self.y0 + (Y - self.pad) / self.s)
        return (fx * 12.0, fy * 12.0)

    def layer(self, name):
        if name and name not in self.doc.layers:
            self.doc.layers.add(name, color=8)
        return name or "0"

    def attrs(self, el, layer):
        a = {"layer": self.layer(layer)}
        dash = (el.get("stroke-dasharray") or "").strip()
        if dash:
            a["linetype"] = DASHES.get(dash, "DASHED")
        return a

    def hatch(self, el, layer, boundary=None, circle=None):
        fill = (el.get("fill") or "").strip().lower()
        if not fill or fill in ("none", "#ffffff", "#fff", "white") or fill.startswith("#f"):
            return
        m = re.match(r"url\(#([\w-]+)\)", fill)
        if m:
            name, scale = PATTERNS.get(m.group(1), ("ANSI31", 12))
            h = self.msp.add_hatch(dxfattribs={"layer": self.layer(layer if layer.endswith("-PATT") else layer + "-PATT")})
            try:
                h.set_pattern_fill(name, color=256, scale=scale)
            except Exception:
                h.set_pattern_fill("ANSI31", color=256, scale=12)
        elif fill in DARK:
            h = self.msp.add_hatch(color=256, dxfattribs={"layer": self.layer(layer)})
        else:   # light gray poché (partitions)
            h = self.msp.add_hatch(color=9, dxfattribs={"layer": self.layer(layer + "-PATT")})
        if circle:
            ep = h.paths.add_edge_path()
            ep.add_arc(circle[0], circle[1], 0, 360)
        else:
            h.paths.add_polyline_path(boundary, is_closed=True)

    def stroked(self, el):
        st = (el.get("stroke") or "").strip().lower()
        return bool(st) and st != "none"

    def walk(self, el, m, layer):
        tag = el.tag.replace(NS, "")
        if tag in ("defs", "pattern", "clipPath", "mask", "style", "title"):
            return
        m = mul(m, parse_transform(el.get("transform")))
        layer = el.get("data-layer") or layer
        if tag == "rect":
            w, h = el.get("width", "0"), el.get("height", "0")
            if "%" in w or "%" in h or not layer:
                return
            x, y, w, h = float(el.get("x", 0)), float(el.get("y", 0)), float(w), float(h)
            pts = [self.P(m, x, y), self.P(m, x + w, y), self.P(m, x + w, y + h), self.P(m, x, y + h)]
            self.hatch(el, layer, boundary=pts)
            if self.stroked(el):
                self.msp.add_lwpolyline(pts, close=True, dxfattribs=self.attrs(el, layer))
        elif tag == "line":
            a = self.P(m, float(el.get("x1", 0)), float(el.get("y1", 0)))
            b = self.P(m, float(el.get("x2", 0)), float(el.get("y2", 0)))
            self.msp.add_line(a, b, dxfattribs=self.attrs(el, layer))
        elif tag in ("polygon", "polyline"):
            v = nums(el.get("points"))
            pts = [self.P(m, v[k], v[k + 1]) for k in range(0, len(v) - 1, 2)]
            if tag == "polygon":
                self.hatch(el, layer, boundary=pts)
            if self.stroked(el) or tag == "polyline":
                self.msp.add_lwpolyline(pts, close=(tag == "polygon"), dxfattribs=self.attrs(el, layer))
        elif tag == "circle":
            c = self.P(m, float(el.get("cx", 0)), float(el.get("cy", 0)))
            r = float(el.get("r", 0)) * math.sqrt(abs(m[0] * m[3] - m[1] * m[2])) / self.s * 12.0
            self.hatch(el, layer, circle=(c, r))
            if self.stroked(el):
                self.msp.add_circle(c, r, dxfattribs=self.attrs(el, layer))
        elif tag == "path":
            for poly in path_polylines(el.get("d", "")):
                pts = [self.P(m, x, y) for x, y in poly]
                closed = len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1e-6
                if closed:
                    self.hatch(el, layer, boundary=pts[:-1])
                if self.stroked(el) or not closed:
                    self.msp.add_lwpolyline(pts[:-1] if closed else pts, close=closed, dxfattribs=self.attrs(el, layer))
        elif tag == "text":
            txt = "".join(el.itertext()).strip()
            if not txt:
                return
            size = float(re.findall(r"[\d.]+", el.get("font-size", "10"))[0])
            x, y = float(el.get("x", 0)), float(el.get("y", 0)) + float(nums(el.get("dy", "0"))[0] if el.get("dy") else 0)
            p = self.P(m, x, y)
            sc = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
            height = size * 0.70 * sc / self.s * 12.0
            rot = math.degrees(math.atan2(-m[1], m[0]))
            align = {"middle": TextEntityAlignment.CENTER, "end": TextEntityAlignment.RIGHT}.get(
                el.get("text-anchor", "start"), TextEntityAlignment.LEFT)   # SVG y is the baseline
            t = self.msp.add_text(txt, height=height, rotation=rot,
                                  dxfattribs={"layer": self.layer(layer), "style": "ARCH"})
            t.set_placement(p, align=align)
        for child in el:
            self.walk(child, m, layer)
        self.count[layer] = self.count.get(layer, 0) + 1

    def save(self, path):
        zoom.extents(self.msp, factor=1.05)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.doc.saveas(path)


def main(src=SRC, out=OUT):
    root = ET.parse(src).getroot()
    if root.get("data-scale") is None:
        sys.exit(f"{src} has no world mapping; regenerate it with drawings_cd.py")
    conv = Converter(root)
    conv.walk(root, (1, 0, 0, 1, 0, 0), None)
    conv.save(out)
    auditor = conv.doc.audit()
    by_layer = {}
    for e in conv.msp:
        by_layer[e.dxf.layer] = by_layer.get(e.dxf.layer, 0) + 1
    print(f"wrote {out}: {sum(by_layer.values())} entities, audit errors {len(auditor.errors)}")
    for k in sorted(by_layer):
        print(f"  {k:16s} {by_layer[k]}")


if __name__ == "__main__":
    main()
