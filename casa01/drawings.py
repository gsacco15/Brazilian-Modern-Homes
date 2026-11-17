"""Architectural drawings for Casa 01, generated as SVG from design.py.

    python3 casa01/drawings.py      ->  casa01/drawings/*.svg

Site plan, furnished floor plan, four elevations, section A-A (with Austin
solstice sun angles) and the cobogó block detail. Same numbers as the 3D
model, so drawings and renders always agree.
"""
import math
import re
import os
import random

import design as D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drawings")

INK = "#23262a"
POCHE = "#2b2e31"
MID = "#6b6f73"
LIGHT = "#a7aaad"
FAINT = "#d4d2cc"
GREEN = "#5f7458"
GOLD = "#b8955a"
STONE = "#e6dcc6"
CEDAR = "#c4885a"
FONT = "Lato, 'Helvetica Neue', Arial, sans-serif"


def fmt_ft(v):
    ft = int(v + 1e-6)
    inch = round((v - ft) * 12)
    if inch == 12:
        ft, inch = ft + 1, 0
    return f"{ft}'-{inch}\""


class SVG:
    def __init__(self, x0, y0, x1, y1, scale, pad=40, flip=True, extra_bottom=0):
        """World window (ft) -> px. flip=True: +y is up (plans/elevations)."""
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.s = scale
        self.pad = pad
        self.flip = flip
        self.w = (x1 - x0) * scale + 2 * pad
        self.h = (y1 - y0) * scale + 2 * pad + extra_bottom
        self.items = []
        self.defs = []
        self.layer = None   # CAD layer name stamped on elements (data-layer) for the DXF export

    def X(self, x):
        return self.pad + (x - self.x0) * self.s

    def Y(self, y):
        if self.flip:
            return self.pad + (self.y1 - y) * self.s
        return self.pad + (y - self.y0) * self.s

    def P(self, x, y):
        return f"{self.X(x):.2f},{self.Y(y):.2f}"

    def add(self, s):
        if self.layer:
            s = re.sub(r"<([a-zA-Z]+)(?=[\s/>])", lambda m: f'<{m.group(1)} data-layer="{self.layer}"', s)
        self.items.append(s)

    def rect(self, x0, y0, x1, y1, fill="none", stroke=INK, sw=1.0, extra=""):
        xa, xb = sorted((self.X(x0), self.X(x1)))
        ya, yb = sorted((self.Y(y0), self.Y(y1)))
        self.add(f'<rect x="{xa:.2f}" y="{ya:.2f}" width="{xb - xa:.2f}" height="{yb - ya:.2f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def poly(self, pts, fill="none", stroke=INK, sw=1.0, extra=""):
        d = " ".join(self.P(x, y) for x, y in pts)
        self.add(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, x0, y0, x1, y1, stroke=INK, sw=1.0, extra=""):
        self.add(f'<line x1="{self.X(x0):.2f}" y1="{self.Y(y0):.2f}" x2="{self.X(x1):.2f}" y2="{self.Y(y1):.2f}" '
                 f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def pline(self, pts, stroke=INK, sw=1.0, fill="none", extra=""):
        d = " ".join(self.P(x, y) for x, y in pts)
        self.add(f'<polyline points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circle(self, x, y, r, fill="none", stroke=INK, sw=1.0, extra=""):
        self.add(f'<circle cx="{self.X(x):.2f}" cy="{self.Y(y):.2f}" r="{r * self.s:.2f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def path(self, d, fill="none", stroke=INK, sw=1.0, extra=""):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def text(self, x, y, s, size=10, anchor="middle", fill=INK, weight=400, ls=0.6, extra="", px=False):
        X = x if px else self.X(x)
        Y = y if px else self.Y(y)
        s = s.replace("&", "&amp;")
        self.add(f'<text x="{X:.2f}" y="{Y:.2f}" font-family="{FONT}" font-size="{size}" text-anchor="{anchor}" '
                 f'fill="{fill}" font-weight="{weight}" letter-spacing="{ls}" {extra}>{s}</text>')

    def arc(self, cx, cy, r, a0, a1, stroke=INK, sw=0.8, extra=""):
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        sweep = 0 if self.flip else 1
        if (a1 - a0) < 0:
            sweep = 1 - sweep
        self.path(f"M {self.P(x0, y0)} A {r * self.s:.2f} {r * self.s:.2f} 0 0 {sweep} {self.P(x1, y1)}",
                  stroke=stroke, sw=sw, extra=extra)

    def dim(self, x0, y0, x1, y1, off, label=None, size=9, horizontal=True):
        """Dimension string between two points, offset perpendicular (ft)."""
        tick = lambda X, Y: self.add(f'<line x1="{X - 3:.2f}" y1="{Y + 3:.2f}" x2="{X + 3:.2f}" y2="{Y - 3:.2f}" '
                                     f'stroke="{INK}" stroke-width="1.1"/>')
        if horizontal:
            yy = y0 + off
            Yd = self.Y(yy)
            self.line(x0, yy, x1, yy, MID, 0.6)
            sgn = 1 if self.Y(y0) > Yd else -1
            for x in (x0, x1):
                X = self.X(x)
                self.add(f'<line x1="{X:.2f}" y1="{self.Y(y0) - sgn * 4:.2f}" x2="{X:.2f}" y2="{Yd - sgn * 4:.2f}" '
                         f'stroke="{MID}" stroke-width="0.5"/>')
                tick(X, Yd)
            self.text((x0 + x1) / 2, yy, label or fmt_ft(abs(x1 - x0)), size, extra='dy="-3"')
        else:
            xx = x0 + off
            Xd = self.X(xx)
            self.line(xx, y0, xx, y1, MID, 0.6)
            sgn = 1 if self.X(x0) > Xd else -1
            for y in (y0, y1):
                Y = self.Y(y)
                self.add(f'<line x1="{self.X(x0) - sgn * 4:.2f}" y1="{Y:.2f}" x2="{Xd - sgn * 4:.2f}" y2="{Y:.2f}" '
                         f'stroke="{MID}" stroke-width="0.5"/>')
                tick(Xd, Y)
            cx, cy = Xd, self.Y((y0 + y1) / 2)
            self.add(f'<text x="{cx:.2f}" y="{cy:.2f}" font-family="{FONT}" font-size="{size}" text-anchor="middle" '
                     f'fill="{INK}" letter-spacing="0.6" transform="rotate(-90 {cx:.2f} {cy:.2f})" dy="-3">'
                     f'{label or fmt_ft(abs(y1 - y0))}</text>')

    def leader(self, x0, y0, x1, y1, label, size=8.5, anchor="start", px_offset=0):
        self.line(x0, y0, x1, y1, MID, 0.6)
        self.add(f'<circle cx="{self.X(x0):.2f}" cy="{self.Y(y0):.2f}" r="2.6" fill="{INK}"/>')
        self.text(x1, y1, label, size, anchor=anchor, extra=f'dx="{4 if anchor == "start" else -4}" dy="3"')

    def save(self, name, title=None):
        os.makedirs(OUT, exist_ok=True)
        body = "\n".join(self.items)
        defs = "\n".join(self.defs)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w:.0f} {self.h:.0f}" '
               f'width="{self.w:.0f}" height="{self.h:.0f}" data-x0="{self.x0}" data-y0="{self.y0}" data-y1="{self.y1}" '
               f'data-pad="{self.pad}" data-scale="{self.s}" data-flip="{int(self.flip)}">\n'
               f'<defs>{defs}</defs>\n<rect width="100%" height="100%" fill="#ffffff"/>\n{body}\n</svg>\n')
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg)
        return os.path.join(OUT, name)


def hatch_defs(svg):
    svg.defs.append(
        '<pattern id="pavers" width="18" height="12" patternUnits="userSpaceOnUse">'
        '<rect width="18" height="12" fill="#f3efe6"/><path d="M0 0 H18 M0 0 V12 M9 6 V12 M0 6 H18" '
        'stroke="#d2c9b6" stroke-width="0.6"/></pattern>')
    svg.defs.append(
        '<pattern id="dg" width="7" height="7" patternUnits="userSpaceOnUse">'
        '<rect width="7" height="7" fill="#f6f1e7"/><circle cx="2" cy="2" r="0.6" fill="#d6c7ad"/>'
        '<circle cx="5.5" cy="5" r="0.5" fill="#d6c7ad"/></pattern>')
    svg.defs.append(
        '<pattern id="mosaic" width="7" height="7" patternUnits="userSpaceOnUse">'
        '<rect width="7" height="7" fill="#2a2a29"/><path d="M0 2 L3 0 L7 3 M2 7 L4 4 L7 6 M0 5 L3 4" '
        'stroke="#8b847a" stroke-width="0.5" fill="none"/></pattern>')
    svg.defs.append(
        '<pattern id="planting" width="9" height="9" patternUnits="userSpaceOnUse">'
        '<rect width="9" height="9" fill="#eef1e8"/><circle cx="2.5" cy="2.5" r="1.1" fill="none" stroke="#a9b89a" '
        'stroke-width="0.5"/><circle cx="7" cy="6.5" r="0.8" fill="none" stroke="#a9b89a" stroke-width="0.5"/></pattern>')
    svg.defs.append(
        '<pattern id="lawn" width="6" height="6" patternUnits="userSpaceOnUse">'
        '<rect width="6" height="6" fill="#eef1e6"/><path d="M1 5 l1 -2 M4 2 l1 -2" stroke="#b9c4a3" '
        'stroke-width="0.6"/></pattern>')
    svg.defs.append(
        '<pattern id="stone" width="16" height="8" patternUnits="userSpaceOnUse">'
        '<rect width="16" height="8" fill="#efe6d2"/><path d="M0 0 H16 M0 4 H16 M5 0 V4 M12 4 V8" '
        'stroke="#c9b993" stroke-width="0.5"/></pattern>')
    svg.defs.append(
        '<pattern id="diag" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="5" height="5" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="5" stroke="#9a9a9a" '
        'stroke-width="0.6"/></pattern>')
    svg.defs.append(
        '<pattern id="earth" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="8" height="8" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="8" stroke="#8a8a8a" '
        'stroke-width="0.7"/></pattern>')


# ------------------------------------------------------------------ geometry helpers
def wall_rects(w, t):
    """Solid pieces of an exterior wall (x0,y0,x1,y1) + opening spans."""
    ax, ay = w["a"]
    bx, by = w["b"]
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux
    pieces, spans = [], []
    s = 0.0
    for o in sorted(w["openings"], key=lambda o: o["off"]):
        pieces.append((s, o["off"]))
        spans.append(o)
        s = o["off"] + o["w"]
    pieces.append((s, L))

    def rect(s0, s1, d0, d1):
        xs = [ax + ux * s0 + nx * d0, ax + ux * s1 + nx * d1]
        ys = [ay + uy * s0 + ny * d0, ay + uy * s1 + ny * d1]
        return min(xs), min(ys), max(xs), max(ys)

    return [rect(a, b, 0, t) for a, b in pieces if b - a > 1e-6], spans, rect, (ux, uy, nx, ny)


def tree_canopy(svg, x, y, r, seed, fill="none", stroke=GREEN, sw=0.8, dash=None):
    rng = random.Random(seed)
    pts = []
    n = 26
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (0.93 + 0.05 * math.sin(a * 7 + seed) + rng.uniform(-0.02, 0.02))
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d = "M " + " L ".join(svg.P(px, py) for px, py in pts) + " Z"
    extra = f'stroke-dasharray="{dash}"' if dash else ""
    svg.path(d, fill=fill, stroke=stroke, sw=sw, extra=extra + ' stroke-linejoin="round"')
    svg.circle(x, y, 0.35, fill=stroke, stroke="none")


def north_arrow(svg, px, py, size=26):
    svg.add(f'<g transform="translate({px},{py})">'
            f'<circle r="{size * 0.62}" fill="none" stroke="{INK}" stroke-width="0.8"/>'
            f'<path d="M0 {-size * 0.55} L{size * 0.22} {size * 0.35} L0 {size * 0.18} L{-size * 0.22} {size * 0.35} Z" '
            f'fill="{INK}"/><text y="{-size * 0.72}" font-family="{FONT}" font-size="10" text-anchor="middle" '
            f'font-weight="700" fill="{INK}">N</text></g>')


def scale_bar(svg, px, py, ft_marks=(0, 4, 8, 16)):
    s = svg.s
    out = [f'<g transform="translate({px},{py})">']
    for i in range(len(ft_marks) - 1):
        a, b = ft_marks[i], ft_marks[i + 1]
        fill = INK if i % 2 == 0 else "#ffffff"
        out.append(f'<rect x="{a * s:.1f}" y="0" width="{(b - a) * s:.1f}" height="5" fill="{fill}" '
                   f'stroke="{INK}" stroke-width="0.7"/>')
    for m in ft_marks:
        out.append(f'<text x="{m * s:.1f}" y="16" font-family="{FONT}" font-size="8.5" text-anchor="middle" '
                   f'fill="{INK}">{m}\'</text>')
    out.append("</g>")
    svg.add("".join(out))


def human(svg, x, z0, h=5.8, stroke=MID):
    """simple scale figure in elevation, standing at (x, z0)."""
    s = h / 5.8
    svg.circle(x, z0 + 5.35 * s, 0.38 * s, fill="none", stroke=stroke, sw=0.8)
    svg.pline([(x - 0.75 * s, z0), (x - 0.5 * s, z0 + 2.6 * s), (x - 0.65 * s, z0 + 4.8 * s),
               (x + 0.65 * s, z0 + 4.8 * s), (x + 0.5 * s, z0 + 2.6 * s), (x + 0.75 * s, z0)],
              stroke=stroke, sw=0.8)


# ------------------------------------------------------------------ floor plan
def furniture_plan(svg):
    st = dict(stroke=LIGHT, sw=0.7)
    for it in D.FURNITURE:
        t = it["t"]
        x, y = it["x"], it["y"]
        if y > 95:
            continue
        w, d = it.get("w", 2), it.get("d", 2)
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - d / 2, y + d / 2
        if t in ("counter", "tall", "credenza"):
            svg.rect(x0, y0, x1, y1, fill="#f4f1ea", stroke=MID, sw=0.7)
            if t == "tall":
                svg.line(x0, y0, x1, y1, LIGHT, 0.5); svg.line(x0, y1, x1, y0, LIGHT, 0.5)
            if t == "counter" and w > d:
                svg.rect(x - 1.4, y - 0.7, x + 1.4, y + 0.7, **st)       # sink
            if t == "counter" and d > w:
                for cy in (y + 1.0, y + 2.2):
                    for cx in (x - 0.45, x + 0.45):
                        svg.circle(cx, cy, 0.32, **st)
        elif t == "island":
            svg.rect(x0, y0, x1, y1, fill="#e9e6df", stroke=MID, sw=0.8)
        elif t == "stool":
            svg.circle(x, y, 0.6, **st)
        elif t in ("dining_table", "outdoor_table"):
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.8)
            per = it.get("chairs", 6) // 2
            for k in range(per):
                cx = x0 + (k + 0.5) * w / per
                svg.rect(cx - 0.8, y0 - 1.6, cx + 0.8, y0 - 0.2, **st)
                svg.rect(cx - 0.8, y1 + 0.2, cx + 0.8, y1 + 1.6, **st)
        elif t == "rug":
            svg.rect(x0, y0, x1, y1, fill="none", stroke=FAINT, sw=0.7, extra='stroke-dasharray="3 2"')
        elif t == "sofa":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.8)
            svg.rect(x1 - 0.8, y0, x1, y1, **st)
            for k in range(1, 3):
                yy = y0 + k * d / 3
                svg.line(x0, yy, x1 - 0.8, yy, LIGHT, 0.5)
        elif t == "coffee_table":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.7)
        elif t == "lounge_chair":
            svg.rect(x - 1.3, y - 1.3, x + 1.3, y + 1.3, fill="#ffffff", **st)
        elif t == "bed":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.8)
            svg.line(x0 + 1.6, y0, x0 + 1.6, y1, LIGHT, 0.5)
            pw = d / 2 - 0.4
            svg.rect(x1 - 1.6, y0 + 0.25, x1 - 0.3, y0 + 0.25 + pw, **st)
            svg.rect(x1 - 1.6, y1 - 0.25 - pw, x1 - 0.3, y1 - 0.25, **st)
        elif t == "nightstand":
            svg.rect(x - 0.9, y - 0.9, x + 0.9, y + 0.9, **st)
        elif t == "vanity":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.7)
            if w > d:
                for cx in (x - w / 4, x + w / 4):
                    svg.circle(cx, y, 0.45, **st)
            else:
                svg.circle(x, y, 0.5, **st)
        elif t == "shower":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.7)
            svg.line(x0, y0, x1, y1, LIGHT, 0.5); svg.line(x0, y1, x1, y0, LIGHT, 0.5)
        elif t == "tub":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=MID, sw=0.7)
            svg.rect(x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, **st)
        elif t in ("wc", "wc_wall"):
            svg.rect(x - 0.9, y - 0.35, x + 0.9, y + 0.35, **st) if it.get("face") in ("e", "w") else \
                svg.rect(x - 0.35, y - 0.9, x + 0.35, y + 0.9, **st)
            svg.circle(x, y, 0.65, **st)
        elif t == "desk":
            svg.rect(x0, y0, x1, y1, fill="#ffffff", **st)
        elif t in ("washer", "dryer"):
            svg.rect(x - 1.2, y - 1.2, x + 1.2, y + 1.2, fill="#ffffff", **st)
            svg.circle(x, y, 0.75, **st)
        elif t == "grill_counter":
            svg.rect(x0, y0, x1, y1, fill="url(#stone)", stroke=MID, sw=0.8)
        elif t == "fan":
            svg.circle(x, y, 2.3, fill="none", stroke=FAINT, sw=0.6, extra='stroke-dasharray="2 2"')
        elif t == "planter":
            svg.circle(x, y, 0.9, fill="#ffffff", **st)
        elif t == "side_table":
            svg.circle(x, y, 0.7, fill="#ffffff", **st)


def bath_symbols(svg, labels=False):
    """Primary bath fixtures from design.PRIMARY_BATH (plan symbols)."""
    B = D.PRIMARY_BATH
    rx0, ry0, rx1, ry1 = B["room"]
    sx0, sy0, sx1, sy1 = B["shower"]
    svg.rect(sx0, sy0, sx1, sy1, fill="url(#tile)", stroke="none")
    gx0, gx1, gy = B["glass"]
    svg.line(gx0, gy, gx1, gy, "#5d8fa0", 2.2)
    svg.line(gx1, gy - 0.06, gx1, gy + 0.06, INK, 2)
    bx0, by0, bx1, by1 = B["bench"]
    svg.rect(bx0, by0, bx1, by1, fill="#efe6d2", stroke=MID, sw=0.7)
    hx, hy = B["rain_head"]
    svg.circle(hx, hy, 0.42, fill="none", stroke=MID, sw=0.8)
    svg.circle(hx, hy, 0.06, fill=MID, stroke="none")
    if "drain" in B:
        dx0, dy, dx1 = B["drain"]
        svg.rect(dx0, dy - 0.06, dx1, dy + 0.06, fill="#c9b27a", stroke=MID, sw=0.5)
    for k in getattr(D, "SKYLIGHTS", []):
        if k["name"] == "Primary shower":
            x0, y0, x1, y1 = k["rect"]
            svg.rect(x0, y0, x1, y1, fill="none", stroke=MID, sw=0.7, extra='stroke-dasharray="5 3"')
            svg.line(x0, y0, x1, y1, LIGHT, 0.5, extra='stroke-dasharray="5 3"')
            svg.line(x0, y1, x1, y0, LIGHT, 0.5, extra='stroke-dasharray="5 3"')
    vx0, vy0, vx1, vy1 = B["vanity"]
    svg.rect(vx0, vy0, vx1, vy1, fill="#f4f1ea", stroke=MID, sw=0.8)
    sx, sy = B["sink"]
    svg.circle(sx, sy, 0.62, fill="#ffffff", stroke=MID, sw=0.8)
    my, md = B["mirror"]
    svg.line(rx0 + 0.05, my - md / 2, rx0 + 0.05, my + md / 2, GOLD, 2.4)
    wcs = [f for f in D.FURNITURE if f["t"] == "wc_wall"]
    wcy = wcs[0]["y"] if wcs else ry0 + 1.5
    svg.rect(rx1 - 1.75, wcy - 0.6, rx1 - 0.35, wcy + 0.6, fill="#ffffff", stroke=MID, sw=0.8)
    svg.circle(rx1 - 1.2, wcy, 0.42, fill="none", stroke=MID, sw=0.7)
    if labels:
        cx = (sx0 + sx1) / 2
        svg.text(cx + 0.6, sy0 + 1.95, "CURBLESS WALK-IN SHOWER", 8.5, weight=700, ls=1.2)
        svg.text(cx + 0.6, sy0 + 1.95, "GREEN ZELLIGE-LOOK TO CEILING", 6.5, fill=MID, extra='dy="10"')
        svg.text(bx0 + 0.5, (by0 + by1) / 2, "BENCH", 6.5, fill=MID,
                 extra=f'transform="rotate(-90 {svg.X(bx0 + 0.5):.1f} {svg.Y((by0 + by1) / 2):.1f})"')
        svg.text((vx1 + rx1) / 2 - 0.4, ry0 + 1.3, "HONED CONCRETE FLOOR", 7.5, weight=700, ls=1.0)
        svg.text((vx1 + rx1) / 2 - 0.4, ry0 + 1.3, "SAME SLAB AS THE HOUSE", 6.5, fill=MID, extra='dy="10"')


def hall_bath_symbols(svg, labels=False):
    """Hall bath (design.HALL_BATH): tub alcove in terracotta tile, glass panel, niche, shelves."""
    B = getattr(D, "HALL_BATH", None)
    if not B:
        return
    rx0, ry0, rx1, ry1 = B["room"]
    tx0, ty0, tx1, ty1 = B["tub"]
    sh = B["shelf"]
    svg.rect(tx0, ty0, tx1, ty1, fill="url(#tiletc)", stroke="none")
    svg.rect(sh[0], sh[1], sh[2], sh[1] + D.INT_T, fill="#575b5f", stroke="#575b5f", sw=0.3)   # tub-foot wall
    svg.rect(tx0 + 0.3, ty0 + 0.05, tx1 - 0.12, ty1 - 0.05, fill="#ffffff", stroke=MID, sw=0.8)
    svg.rect(tx0 + 0.55, ty0 + 0.35, tx1 - 0.4, ty1 - 0.35, fill="none", stroke=LIGHT, sw=0.7,
             extra='rx="6" ry="6"')
    gx, gy0, gy1 = B["glass"]
    svg.line(gx - 0.1, gy0 + 0.05, gx - 0.1, gy1, "#5d8fa0", 2.2)
    svg.line(gx - 0.16, gy1, gx - 0.04, gy1, INK, 2)
    cx = (tx0 + 0.3 + tx1) / 2
    svg.circle(cx, ty0 + 0.75, 0.3, fill="none", stroke=MID, sw=0.7)
    nx, ny0, ny1, _z0, _z1 = B["niche"]
    svg.rect(nx, ny0, nx + 0.28, ny1, fill="#ffffff", stroke=MID, sw=0.6, extra='stroke-dasharray="3 2"')
    for k in getattr(D, "SKYLIGHTS", []):
        if k["name"] == "Bath 2":
            x0, y0, x1, y1 = k["rect"]
            svg.rect(x0, y0, x1, y1, fill="none", stroke=MID, sw=0.7, extra='stroke-dasharray="5 3"')
            svg.line(x0, y0, x1, y1, LIGHT, 0.5, extra='stroke-dasharray="5 3"')
            svg.line(x0, y1, x1, y0, LIGHT, 0.5, extra='stroke-dasharray="5 3"')
    y0s = sh[1] + D.INT_T
    svg.rect(sh[0], y0s, sh[2], sh[3], fill="#efe2cc", stroke=MID, sw=0.6)
    vx0, vy0, vx1, vy1 = B["vanity"]
    svg.rect(vx0, vy0, vx1, vy1, fill="#f4f1ea", stroke=MID, sw=0.8)
    sx, sy = B["sink"]
    svg.rect(sx - 0.75, sy - 0.48, sx + 0.75, sy + 0.42, fill="#ffffff", stroke=MID, sw=0.8, extra='rx="3" ry="3"')
    mx, mw, _mh = B["mirror"]
    svg.line(mx - mw / 2, ry1 - 0.05, mx + mw / 2, ry1 - 0.05, GOLD, 2.4)
    wx, wy = B["wc"]
    svg.rect(wx - 0.6, ry0 + 0.35, wx + 0.6, ry0 + 1.75, fill="#ffffff", stroke=MID, sw=0.8)
    svg.circle(wx, ry0 + 1.2, 0.42, fill="none", stroke=MID, sw=0.7)
    if labels:
        svg.text((tx0 + tx1) / 2 + 0.1, ty1 - 0.9, "TUB", 8.5, weight=700, ls=1.2)
        svg.text((vx0 + rx1) / 2 + 0.3, (ry0 + ry1) / 2 - 0.3, "HONED CONCRETE FLOOR", 7.0, weight=700, ls=0.8)


def _bath_walls(svg, door_names):
    for w in D.EXT_WALLS:
        rects, spans, rect, (ux, uy, nx, ny) = wall_rects(w, D.EXT_T)
        for r in rects:
            svg.rect(*r, fill=POCHE, stroke=POCHE, sw=0.3)
        for o in spans:
            x0, y0, x1, y1 = rect(o["off"], o["off"] + o["w"], 0, D.EXT_T)
            svg.rect(x0, y0, x1, y1, fill="#dfe9ec", stroke=INK, sw=0.8)
    for p in D.PARTITIONS:
        (ax, ay), (bx, by) = p["a"], p["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        t = D.INT_T / 2
        s = 0.0
        for o in sorted(p["openings"], key=lambda o: o["off"]) + [None]:
            e = o["off"] if o else L
            if e - s > 1e-6:
                xs = [ax + ux * s + nx * t, ax + ux * e - nx * t]
                ys = [ay + uy * s + ny * t, ay + uy * e - ny * t]
                svg.rect(min(xs), min(ys), max(xs), max(ys), fill="#575b5f", stroke="#575b5f", sw=0.3)
            if o:
                if o.get("name") in door_names:
                    sw_ = o.get("swing", 1)
                    hx, hy = ax + ux * o["off"], ay + uy * o["off"]
                    lx, ly = hx + nx * o["w"] * sw_, hy + ny * o["w"] * sw_
                    svg.line(hx, hy, lx, ly, INK, 1.4)
                    a0 = math.atan2(uy, ux)
                    a1 = math.atan2(ly - hy, lx - hx)
                    svg.arc(hx, hy, o["w"], min(a0, a1), max(a0, a1), LIGHT, 0.8)
                s = o["off"] + o["w"]


def _bath_defs(svg):
    hatch_defs(svg)
    svg.defs.append('<pattern id="tile" width="9.4" height="9.4" patternUnits="userSpaceOnUse">'
                    '<rect width="9.4" height="9.4" fill="#e3ece7"/><path d="M0 0 H9.4 M0 0 V9.4" stroke="#a9c2b6" '
                    'stroke-width="0.6"/></pattern>')
    svg.defs.append('<pattern id="tiletc" width="3.2" height="10" patternUnits="userSpaceOnUse">'
                    '<rect width="3.2" height="10" fill="#efd6c6"/><path d="M0 0 H3.2 M0 0 V10" stroke="#c99478" '
                    'stroke-width="0.5"/></pattern>')


def bath_plan():
    """Enlarged plan of the primary bath (about 1/2" = 1'-0")."""
    B = D.PRIMARY_BATH
    rx0, ry0, rx1, ry1 = B["room"]
    svg = SVG(rx0 - 7.5, ry0 - 2.4, rx1 + 7.5, ry1 + 3.0, scale=40, pad=24)
    _bath_defs(svg)
    svg.rect(rx0, ry0, rx1, ry1, fill="#f1ede6", stroke="none")
    bath_symbols(svg, labels=True)
    _bath_walls(svg, ("Primary bath",))
    svg.dim(rx0, ry1, rx1, ry1, 1.6, size=11)
    svg.dim(rx1, ry0, rx1, ry1, 1.8, horizontal=False, size=11)
    svg.dim(rx1, B["shower"][1], rx1, ry1, 0.9, horizontal=False, size=10)
    svg.dim(rx0, ry0, rx0, B["vanity"][3], -1.2, horizontal=False, size=10)
    ew = [w for w in D.EXT_WALLS if w["id"] == "E-bar"][0]
    gw = [o for o in ew["openings"] if "garden" in o.get("name", "").lower()]
    if gw:
        gyc = ew["a"][1] + gw[0]["off"] + gw[0]["w"] / 2
        svg.leader(rx1 + 0.25, gyc, rx1 + 2.0, ry1 + 1.6, "GARDEN WINDOW, FROSTED BELOW 5'", size=9)
    sk = [k for k in getattr(D, "SKYLIGHTS", []) if k["name"] == "Primary shower"]
    if sk:
        x0, y0, x1, y1 = sk[0]["rect"]
        svg.leader((x0 + x1) / 2, (y0 + y1) / 2, (x0 + x1) / 2 + 0.6, ry1 + 2.3, "SKYLIGHT ABOVE, 2' x 3'", size=9)
    svg.leader(rx0 + 2.2, ry1 + 0.25, rx0 - 0.6, ry1 + 1.6, "CLERESTORY ABOVE", size=9, anchor="end")
    my, md = B["mirror"]
    svg.leader(rx0 + 0.05, my, rx0 - 1.6, my - 1.2, "ROUND BRASS MIRROR", size=9, anchor="end")
    gx0, gx1, gy = B["glass"]
    svg.leader(gx0 + 1.4, gy, rx0 - 1.6, gy - 0.4, "FIXED GLASS PANEL", size=9, anchor="end")
    vx0, vy0, vx1, vy1 = B["vanity"]
    svg.leader(vx1 - 0.3, vy0 + 0.5, rx0 - 1.6, ry0 - 1.3, "FLOATING OAK VANITY, LIMESTONE TOP", size=9, anchor="end")
    if "drain" in B:
        dx0, dy, dx1 = B["drain"]
        svg.leader(dx1 - 0.4, dy, rx1 + 2.0, ry1 + 0.5, "SLOT DRAIN", size=9)
    wcs = [f for f in D.FURNITURE if f["t"] == "wc_wall"]
    wcy = wcs[0]["y"] if wcs else ry0 + 1.5
    svg.leader(rx1 - 1.0, wcy, rx1 + 2.0, wcy - 0.9, "WALL-HUNG WC", size=9)
    north_arrow(svg, svg.w - 40, 46, 20)
    return svg.save("09_bath_plan.svg")


def hall_bath_plan():
    """Enlarged plan of the hall bath (about 1/2" = 1'-0")."""
    B = getattr(D, "HALL_BATH", None)
    if not B:
        return None
    rx0, ry0, rx1, ry1 = B["room"]
    svg = SVG(rx0 - 9.0, ry0 - 2.4, rx1 + 8.6, ry1 + 2.8, scale=38, pad=24)
    _bath_defs(svg)
    svg.rect(rx0, ry0, rx1, ry1, fill="#f1ede6", stroke="none")
    hall_bath_symbols(svg, labels=True)
    _bath_walls(svg, ("Bath",))
    svg.dim(rx0, ry1, rx1, ry1, 1.4, size=11)
    svg.dim(rx1, ry0, rx1, ry1, 1.6, horizontal=False, size=11)
    tx0, ty0, tx1, ty1 = B["tub"]
    svg.dim(tx0, ty0, tx1, ty0, -1.3, size=10)
    svg.dim(tx0, ty0, tx0, ty1, -1.2, horizontal=False, size=10)
    gx, gy0, gy1 = B["glass"]
    svg.leader(gx - 0.1, (gy0 + gy1) / 2, rx1 + 1.6, ry0 - 1.2, "FIXED GLASS PANEL (NO CURTAIN)", size=9)
    nx, ny0, ny1, _z0, _z1 = B["niche"]
    svg.leader(nx + 0.14, (ny0 + ny1) / 2, rx0 - 1.8, (ny0 + ny1) / 2 + 1.0, "TILED NICHE", size=9, anchor="end")
    svg.leader(tx0 + 0.15, ty0 + 0.6, rx0 - 1.8, ty0 - 0.6, "TERRACOTTA ZELLIGE-LOOK TO CEILING", size=9, anchor="end")
    sk = [k for k in getattr(D, "SKYLIGHTS", []) if k["name"] == "Bath 2"]
    if sk:
        x0, y0, x1, y1 = sk[0]["rect"]
        svg.leader((x0 + x1) / 2, y1 - 0.4, rx0 - 1.8, y1 + 0.6, "SKYLIGHT ABOVE, 2' x 4'", size=9, anchor="end")
    sh = B["shelf"]
    svg.leader((sh[0] + sh[2]) / 2, (sh[1] + D.INT_T + sh[3]) / 2, rx0 - 1.8, ry1 + 1.6, "OPEN OAK SHELVES", size=9,
               anchor="end")
    mx, mw, _mh = B["mirror"]
    svg.leader(mx + mw / 2 - 0.2, ry1 - 0.05, rx1 + 1.6, ry1 + 1.6, "PILL MIRROR, BRASS SCONCES", size=9)
    vx0, vy0, vx1, vy1 = B["vanity"]
    svg.leader(vx1 - 0.2, vy0 + 0.4, rx1 + 1.6, vy0 - 0.3, "OAK VANITY, LIMESTONE TOP, RECTANGULAR VESSEL", size=9)
    wx, wy = B["wc"]
    svg.leader(wx + 0.5, ry0 + 1.2, rx1 + 1.6, ry0 + 0.6, "WALL-HUNG WC", size=9)
    north_arrow(svg, svg.w - 40, 46, 20)
    return svg.save("10_hall_bath_plan.svg")


def floor_plan():
    svg = SVG(-7, 20, 80, 97, scale=10.0, pad=30)
    hatch_defs(svg)
    # outdoor surfaces (from design: paving, courtyard planting, carport slab)
    for pl in D.PLANTING:
        if pl["name"] == "Courtyard garden":
            svg.poly(pl["poly"], fill="url(#planting)", stroke="none")
    for pz in D.PAVING:
        svg.rect(*pz["rect"], fill="url(#pavers)", stroke="none")
    em = D.ENTRY_MOSAIC
    svg.rect(em["x0"], em["y0"], em["x1"], em["y1"], fill="#ddd8cf", stroke="none")
    svg.rect(em["x0"] + em["band"], em["y0"] + em["band"], em["x1"] - em["band"], em["y1"] - em["band"],
             fill="url(#mosaic)", stroke=INK, sw=0.5)
    cp = getattr(D, "CARPORT", None)
    if cp:
        svg.rect(cp["x0"], cp["y0"], cp["x1"], cp["y1"], fill="#e7e4de", stroke=LIGHT, sw=0.6)
    # interior floor tone
    svg.poly(D.FOOTPRINT, fill="#fbfaf7", stroke="none")
    furniture_plan(svg)
    svg.defs.append('<pattern id="tile" width="5" height="5" patternUnits="userSpaceOnUse">'
                    '<rect width="5" height="5" fill="#e3ece7"/><path d="M0 0 H5 M0 0 V5" stroke="#a9c2b6" '
                    'stroke-width="0.5"/></pattern>')
    bath_symbols(svg)
    svg.defs.append('<pattern id="tiletc" width="2.4" height="7" patternUnits="userSpaceOnUse">'
                    '<rect width="2.4" height="7" fill="#efd6c6"/><path d="M0 0 H2.4 M0 0 V7" stroke="#c99478" '
                    'stroke-width="0.4"/></pattern>')
    hall_bath_symbols(svg)
    # roof outline overhead
    svg.poly(D.ROOF, fill="none", stroke=MID, sw=0.8, extra='stroke-dasharray="7 4"')
    # courtyard tree canopy
    t = D.TREES[1]
    tree_canopy(svg, t["x"], t["y"], t["spread"] / 2, 3, stroke=GREEN, sw=0.8, dash="4 2")
    # exterior walls (poché)
    for w in D.EXT_WALLS:
        rects, spans, rect, (ux, uy, nx, ny) = wall_rects(w, D.EXT_T)
        for r in rects:
            svg.rect(*r, fill=POCHE, stroke=POCHE, sw=0.3)
        for o in spans:
            s0, s1 = o["off"], o["off"] + o["w"]
            x0, y0, x1, y1 = rect(s0, s1, 0, D.EXT_T)
            svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke="none")
            if o["kind"] == "pivot":
                # cedar pivot door drawn open 90°
                piv = s0 + o["w"] * 0.25
                ax, ay = w["a"]
                px, py = ax + ux * piv + nx * 0.25, ay + uy * piv + ny * 0.25
                svg.line(px, py, px + nx * 3.0, py + ny * 3.0, INK, 1.4)
                svg.line(px, py, px - nx * 1.0, py - ny * 1.0, INK, 1.4)
                continue
            # frame lines + glass
            for d in (0.06, D.EXT_T - 0.06):
                xa, ya, xb, yb = rect(s0, s1, d, d)
                svg.line(xa, ya, xb, yb, INK, 0.7)
            xa, ya, xb, yb = rect(s0, s1, D.EXT_T / 2, D.EXT_T / 2)
            svg.line(xa, ya, xb, yb, INK, 0.5)
            n = o.get("panels", 1)
            for k in range(1, n):
                xa, ya, xb, yb = rect(s0 + k * o["w"] / n, s0 + k * o["w"] / n, 0, D.EXT_T)
                svg.line(xa, ya, xb, yb, INK, 0.9)
            if o["sill"] > 0:   # sill line beyond
                xa, ya, xb, yb = rect(s0, s1, -0.25, -0.25)
                svg.line(xa, ya, xb, yb, LIGHT, 0.5)
    # limestone veneer + fin
    lw = D.LIMESTONE_WALL
    hole = D.EXT_WALLS[0]["openings"][0]
    hx0 = D.EXT_WALLS[0]["a"][0] + hole["off"]
    hx1 = hx0 + hole["w"]
    for (a, b) in ((lw["x0"], hx0), (hx1, lw["x1"])):
        svg.rect(a, lw["y_face"], b, lw["y_back"], fill="url(#stone)", stroke=INK, sw=0.6)
    # interior partitions
    for p in D.PARTITIONS:
        (ax, ay), (bx, by) = p["a"], p["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        t = D.INT_T / 2
        s = 0.0
        ops = sorted(p["openings"], key=lambda o: o["off"])
        for o in ops + [None]:
            e = o["off"] if o else L
            if e - s > 1e-6:
                xs = [ax + ux * s + nx * t, ax + ux * e - nx * t]
                ys = [ay + uy * s + ny * t, ay + uy * e - ny * t]
                svg.rect(min(xs), min(ys), max(xs), max(ys), fill="#575b5f", stroke="#575b5f", sw=0.3)
            if o:
                s0, s1 = o["off"], o["off"] + o["w"]
                if o["kind"] == "closet":
                    for k, dd in enumerate((-0.08, 0.08)):
                        a0 = s0 + k * o["w"] / 2 - 0.05
                        a1 = a0 + o["w"] / 2 + 0.1
                        svg.line(ax + ux * a0 + nx * dd, ay + uy * a0 + ny * dd,
                                 ax + ux * a1 + nx * dd, ay + uy * a1 + ny * dd, INK, 0.9)
                else:
                    sw_ = o.get("swing", 1)
                    if p["a"] == (39.0, 60.5):
                        sw_ = -1
                    hx, hy = ax + ux * s0, ay + uy * s0
                    lx, ly = hx + nx * o["w"] * sw_, hy + ny * o["w"] * sw_
                    svg.line(hx, hy, lx, ly, INK, 1.0)
                    a0 = math.atan2(ly - hy, lx - hx)
                    a1 = math.atan2(uy, ux)
                    if abs(((a1 - a0 + math.pi) % (2 * math.pi)) - math.pi) > 0:
                        da = ((a1 - a0 + math.pi) % (2 * math.pi)) - math.pi
                        svg.arc(hx, hy, o["w"], a0, a0 + da, LIGHT, 0.6)
                s = s1
    # cobogó (plan): row of blocks with circle voids
    c = D.COBOGO
    for i in range(int(c["x1"] - c["x0"])):
        x = c["x0"] + i
        svg.rect(x + 0.02, c["y"], x + 0.98, c["y"] + c["t"], fill="#ffffff", stroke=INK, sw=0.6)
        svg.line(x + 0.2, c["y"] + c["t"] / 2, x + 0.8, c["y"] + c["t"] / 2, LIGHT, 0.4)
    svg.rect(c["x0"] - 0.5, c["y"] - 0.05, c["x0"], c["y"] + 0.38, fill=INK, stroke=INK, sw=0.3)
    # gate
    g = D.ENTRY_GATE
    svg.rect(g["x0"] - 0.33, g["y"], g["x0"], g["y"] + 0.33, fill=INK, stroke=INK, sw=0.3)
    svg.line(g["x0"] + 0.1, g["y"] + 0.15, g["x0"] + 0.1 + 3.5 * math.cos(math.radians(55)),
             g["y"] + 0.15 + 3.5 * math.sin(math.radians(55)), INK, 1.3)
    svg.arc(g["x0"] + 0.1, g["y"] + 0.15, 3.8, math.radians(0), math.radians(55), LIGHT, 0.6)
    # cedar screen
    s_ = D.CEDAR_SCREEN
    y = s_["y0"]
    while y < s_["y1"]:
        if not any(a - 0.05 < y < b for (a, b) in s_.get("openings", [])):
            svg.rect(s_["x"] - s_["slat_d"], y, s_["x"], y + s_["slat_w"], fill=CEDAR, stroke="none")
        y += s_["slat_w"] + s_["gap"]
    for sc in getattr(D, "SLAT_SCREENS", []):
        if sc["axis"] == "x":
            x = sc["x0"] + 0.3
            while x < sc["x1"] - 0.2:
                svg.rect(x, sc["y"], x + s_["slat_w"], sc["y"] + s_["slat_d"], fill=CEDAR, stroke="none")
                x += s_["slat_w"] + s_["gap"]
        else:
            y = sc["y0"] + 0.1
            while y < sc["y1"] - 0.1:
                svg.rect(sc["x"] - s_["slat_d"], y, sc["x"], y + s_["slat_w"], fill=CEDAR, stroke="none")
                y += s_["slat_w"] + s_["gap"]
    sl = getattr(D, "CARPORT_SLIDER", None)
    if sl and sl.get("installed", True):   # sliding gate shown closed; parked position dashed
        svg.rect(sl["x0"] + 0.1, sl["y"] - 0.14, sl["x1"] - 0.1, sl["y"] + 0.14, fill=CEDAR, stroke="none")
        w_ = sl["x1"] - sl["x0"]
        svg.rect(sl["park_x0"], sl["y"] - 0.14, sl["park_x0"] + w_, sl["y"] + 0.14, fill="none", stroke=CEDAR, sw=0.7,
                 extra='stroke-dasharray="4 2"')
    # posts
    for (x, y) in D.POSTS:
        svg.rect(x - 0.17, y - 0.17, x + 0.17, y + 0.17, fill=INK, stroke=INK, sw=0.3)
    # room labels
    for r in D.ROOMS:
        lx, ly = r["label"]
        xs = [p[0] for p in r["poly"]]
        ys = [p[1] for p in r["poly"]]
        size = 7.0 if r.get("small") else 9.5
        if r.get("vertical"):
            X, Y = svg.X(lx), svg.Y(ly)
            svg.add(f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{FONT}" font-size="8.5" text-anchor="middle" '
                    f'fill="{INK}" letter-spacing="1.5" font-weight="700" transform="rotate(-90 {X:.1f} {Y:.1f})">'
                    f'GALLERY</text>')
            continue
        svg.text(lx, ly, r["name"].upper(), size, weight=700, ls=1.0)
        if r.get("show_area", True) and not r.get("small"):
            wft, dft = max(xs) - min(xs), max(ys) - min(ys)
            svg.text(lx, ly, f"{fmt_ft(wft)} x {fmt_ft(dft)}", 7.5, fill=MID, extra='dy="11"')
    for o in D.OUTDOOR:
        lx, ly = o["label"]
        svg.text(lx, ly, o["name"].upper(), 9, weight=700, fill=GREEN, ls=1.2)
    # tags for signature elements
    svg.leader(44.0, 30.15, 47.0, 24.6, "COBOGÓ SCREEN — 12x12 PRECAST BLOCK")
    svg.leader(15.0, 29.8, 11.0, 24.6, "LUEDERS LIMESTONE WALL", anchor="end")
    svg.leader(30.5, 30.2, 27.2, 22.4, "CEDAR PIVOT GATE", anchor="end")
    svg.leader(36.0, 33.0, 36.0, 21.2, "BLACK CALÇADA PORTUGUESA, 50 SF", anchor="start")
    if cp:
        svg.leader(D.CEDAR_SCREEN["x"], 44.0, cp["x1"] + 3.0, 44.0, "CEDAR SLAT SCREENS", size=7.5)
        sl = getattr(D, "CARPORT_SLIDER", None)
        if sl:
            svg.leader((sl["x0"] + sl["x1"]) / 2, sl["y"], cp["x1"] + 3.0, 26.0, "SLIDING CEDAR GATE (OPTION)", size=7.5)
    svg.leader(43.0, 90.0, 47.0, 90.0, "ROOF EDGE ABOVE")
    svg.text(30.5, 18.8, "ENTER FROM STREET ↑", 8, fill=MID, ls=1.0)
    # dimension strings
    bx0, bx1 = D.BAR["x0"], D.BAR["x1"]
    svg.dim(bx0, 80, bx1, 80, 15.2, fmt_ft(bx1 - bx0), size=9)
    svg.dim(bx0, 30, D.WING["x1"], 30, -7.2, size=8.5)
    svg.dim(D.WING["x1"], 30, cp["x0"] if cp else bx1, 30, -7.2, size=8.5)
    if cp:
        svg.dim(cp["x0"], 30, cp["x1"], 30, -7.2, size=8.5)
    svg.dim(bx0, 30, bx0, 60, -5.6, horizontal=False, size=8.5)
    svg.dim(bx0, 60, bx0, 80, -5.6, horizontal=False, size=8.5)
    svg.dim(bx1, 60, bx1, 80, 6.2, horizontal=False, size=8.5)
    svg.dim(18, 80, 18, 92, -3.6, horizontal=False, size=8)
    svg.dim(6, 30, 6, 80, -9.6, fmt_ft(50), horizontal=False, size=9)
    # section mark A-A (cut at x = 34, looking west)
    for (yy, rot) in ((24.0, 0), (96.5, 0)):
        svg.line(34, yy, 34, yy + (3 if yy < 50 else -3), INK, 1.6)
        svg.circle(34, yy + (-0.9 if yy < 50 else 0.9), 0.95, fill="#ffffff", stroke=INK, sw=1.0)
        svg.text(34, yy + (-0.9 if yy < 50 else 0.9), "A", 8, weight=700, extra='dy="3"')
        svg.add(f'<path d="M {svg.P(33.0, yy + (-0.9 if yy < 50 else 0.9))} l -6 0 l 3 -3 z" fill="{INK}"/>')
    north_arrow(svg, svg.w - 60, 70)
    scale_bar(svg, svg.w - 230, svg.h - 30)
    return svg.save("02_floor_plan.svg")


# ------------------------------------------------------------------ site plan
def site_plan():
    svg = SVG(-14, -16, 79, 131, scale=4.6, pad=26)
    hatch_defs(svg)
    svg.rect(-14, -16, 79, -11.5, fill="#e6e4df", stroke="none")     # street
    svg.text(32.5, -14.6, "STREET", 8, fill=MID, ls=3)
    svg.rect(-14, -5, 79, -0.5, fill="#f2f0eb", stroke=LIGHT, sw=0.4)  # sidewalk
    svg.rect(-14, -11, 79, -5, fill="url(#lawn)", stroke="none")
    svg.rect(0, 0, D.LOT_W, D.LOT_D, fill="url(#dg)", stroke="none")
    svg.rect(0.3, 93.8, 64.7, 124.7, fill="url(#lawn)", stroke="none")
    svg.rect(0, 0, D.LOT_W, D.LOT_D, fill="none", stroke=INK, sw=1.4, extra='stroke-dasharray="10 3 2 3"')
    # setbacks
    svg.rect(D.SETBACK_SIDE, D.SETBACK_FRONT, D.LOT_W - D.SETBACK_SIDE, D.LOT_D - D.SETBACK_REAR,
             stroke=GOLD, sw=0.8, extra='stroke-dasharray="4 3"')
    svg.text(D.SETBACK_SIDE + 1, D.SETBACK_FRONT + 1.0, "SETBACK LINE", 6.5, anchor="start", fill=GOLD, ls=1.0)
    # driveway ribbons + front path
    for (a, b) in D.DRIVEWAY["strips"]:
        svg.rect(a, D.DRIVEWAY["y0"], b, D.DRIVEWAY["y1"], fill="#dad6cf", stroke=MID, sw=0.5)
    pth = D.PATHS[0]
    y = 0.4
    while y + 1.5 < 27.3:
        svg.rect(pth["x"] - pth["w"] / 2, y, pth["x"] + pth["w"] / 2, y + 1.5, fill="#efe6d2", stroke=MID, sw=0.4)
        y += 2.5
    # fences
    for (a, b) in D.FENCES:
        svg.line(a[0], a[1], b[0], b[1], CEDAR, 1.6)
    # roof (as the building reads from above)
    svg.poly(D.ROOF, fill="#ffffff", stroke=INK, sw=1.6)    # notches in the plate = courtyard + gardens open to sky
    svg.rect(D.COBOGO["x0"], 30, D.COBOGO["x1"], 30.33, fill=INK, stroke="none")
    svg.text(24.0, 64.0, "CASA 01", 11, weight=700, ls=2)
    svg.text(24.0, 64.0, f"{D.conditioned_area():,.0f} SF CONDITIONED", 7.5, fill=MID, extra='dy="12"')
    svg.text((D.COURTYARD["x0"] + D.COURTYARD["x1"]) / 2 + 1.5, 44, "PÁTIO", 8, weight=700, fill=GREEN, ls=1.5)
    cp = getattr(D, "CARPORT", None)
    if cp:   # carport under the roof plate (dashed = below the roof)
        svg.rect(cp["x0"], cp["y0"], cp["x1"], cp["y1"], fill="none", stroke=INK, sw=0.8, extra='stroke-dasharray="5 3"')
        svg.text((cp["x0"] + cp["x1"]) / 2, (cp["y0"] + cp["y1"]) / 2 + 2, "CARPORT", 6.5, weight=700, fill=MID, ls=1.0)
        svg.text((cp["x0"] + cp["x1"]) / 2, (cp["y0"] + cp["y1"]) / 2 + 2, "UNDER ROOF", 5.5, fill=MID, extra='dy="8"')
    hv = getattr(D, "HVAC", None)
    if hv:
        x0, y0, x1, y1 = hv["pad"]
        svg.rect(x0, y0, x1, y1, fill="#ffffff", stroke=INK, sw=0.8)
        svg.leader((x0 + x1) / 2, (y0 + y1) / 2, -9.0, 72.0, "AC PAD", size=6, anchor="end")
    svg.text(29.5, 88.2, "VERANDA", 7, weight=700, fill=GREEN, ls=1.2)
    # trees
    for i, t in enumerate(D.TREES):
        tree_canopy(svg, t["x"], t["y"], t["spread"] / 2, t["seed"], fill="rgba(95,116,88,0.10)",
                    stroke=GREEN, sw=0.9)
    svg.leader(31.0, 110.0, 44.0, 119.0, "HERITAGE LIVE OAK (PROTECTED)", size=6.5)
    svg.text(15.0, 13.0, "NATIVE MEADOW", 6.5, fill=GREEN, weight=700, ls=1.2)
    svg.text(15.0, 13.0, "DG + AGAVE + GRASSES", 6, fill=MID, extra='dy="9"')
    dx = (D.DRIVEWAY["strips"][0][0] + D.DRIVEWAY["strips"][-1][1]) / 2
    svg.text(dx, 13.0, "DRIVE", 6, fill=MID, ls=1.0, extra='transform="rotate(-90 ' + f"{svg.X(dx):.1f} {svg.Y(13.0):.1f}" + ')"')
    svg.text(32.5, 108.0, "LAWN / BUFFALO GRASS", 6, fill=MID, ls=1.0)
    # dims
    svg.dim(0, 125, 65, 125, 4.0, fmt_ft(65) + " LOT", size=7.5)
    svg.dim(0, 0, 0, 125, -7.5, fmt_ft(125) + " LOT", horizontal=False, size=7.5)
    svg.dim(60, 0, 60, 30, 0, fmt_ft(30), horizontal=False, size=7)
    north_arrow(svg, svg.w - 40, 46, 22)
    scale_bar(svg, 30, svg.h - 22, (0, 10, 20, 40))
    return svg.save("01_site_plan.svg")


# ------------------------------------------------------------------ elevations
def limestone_courses(x0, x1, z0, z1, hole=None):
    rng = random.Random(42)
    pattern = [0.667, 0.333, 1.0, 0.333, 0.667, 0.667, 1.0, 0.333]
    stones = []
    z, i = z0, 0
    while z < z1 - 0.05:
        h = pattern[i % len(pattern)] if i else 0.667
        h = min(h, z1 - z)
        x = x0 - rng.uniform(0, 1.5)
        while x < x1:
            ln = rng.uniform(1.4, 3.6) if h < 0.9 else rng.uniform(1.8, 4.2)
            sx0, sx1 = max(x, x0), min(x + ln, x1)
            x += ln
            if sx1 - sx0 < 0.25:
                continue
            rng.random()
            stones.append((sx0, sx1, z, z + h))
            rng.uniform(-0.012, 0.012)
        z += h
        i += 1
    return stones


def cobogo_elev(svg, x0, x1, z0, z1, flip_x=False, stroke=INK):
    n = int(round(x1 - x0))
    m = int(round(z1 - z0))
    svg.rect(x0, z0, x1, z1, fill="#f7f5f0", stroke=stroke, sw=0.9)
    for i in range(n):
        for k in range(m):
            cx, cz = x0 + i + 0.5, z0 + k + 0.5
            svg.circle(cx, cz, 0.30, fill="#ffffff", stroke=stroke, sw=0.55)
    for i in range(n + 1):
        for k in range(m + 1):
            xx, zz = x0 + i, z0 + k
            # corner circles (clipped to the panel)
            for (qa, qb, sa, sb) in ((0, 0, 0, 90), (1, 0, 90, 180), (1, 1, 180, 270), (0, 1, 270, 360)):
                pass
            if 0 < i < n and 0 < k < m:
                svg.circle(xx, zz, 0.24, fill="#ffffff", stroke=stroke, sw=0.55)
    for i in range(n):
        for k in range(m + 1):
            if 0 < k < m:
                svg.circle(x0 + i + 0.5, z0 + k, 0.085, fill="#ffffff", stroke=stroke, sw=0.45)
    for i in range(n + 1):
        for k in range(m):
            if 0 < i < n:
                svg.circle(x0 + i, z0 + k + 0.5, 0.085, fill="#ffffff", stroke=stroke, sw=0.45)


def ground(svg, x0, x1, z=0.0):
    svg.rect(x0, z - 1.4, x1, z, fill="url(#earth)", stroke="none")
    svg.line(x0, z, x1, z, INK, 1.8)


def level_marks(svg, x, marks):
    for z, label in marks:
        svg.line(x - 1.2, z, x + 1.0, z, MID, 0.6)
        svg.add(f'<path d="M {svg.P(x - 0.2, z)} l -5 -7 l 10 0 z" fill="none" stroke="{INK}" stroke-width="0.8"/>')
        # grade sits on the ground line: drop its label below so the hatch doesn't strike it
        svg.text(x + 1.4, z, label, 7.5, anchor="start", extra='dy="12"' if z <= 0 else 'dy="3"')


def elev_tree(svg, x, z0, h, spread, seed, stroke=LIGHT, trunk=True):
    """Scalloped canopy outline (architectural entourage). Skipped if outside the window."""
    if x + spread / 2 < svg.x0 or x - spread / 2 > svg.x1:
        return
    rng = random.Random(seed)
    r = spread / 2
    cz = z0 + h * 0.6
    rz = h * 0.4
    base = z0 + h * 0.32
    pts = []
    n = 22
    for k in range(n + 1):
        a = math.pi * k / n
        rr = 1.0 + rng.uniform(-0.05, 0.05)
        pts.append((x + math.cos(a) * r * rr, max(base, cz + math.sin(a) * rz * rr)))
    d = f"M {svg.P(*pts[0])}"
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        nx, nz = mx - x, mz - cz
        L = math.hypot(nx, nz) or 1
        bulge = 0.18 * math.hypot(bx - ax, bz - az) + 0.25
        d += f" Q {svg.P(mx + nx / L * bulge, mz + nz / L * bulge)} {svg.P(bx, bz)}"
    # flat-ish underside with a few lobes
    d += f" Q {svg.P(x - r * 0.5, base - 1.2)} {svg.P(x, base + 0.3)} Q {svg.P(x + r * 0.5, base - 1.2)} {svg.P(*pts[0])} Z"
    svg.path(d, fill="rgba(95,116,88,0.07)", stroke=stroke, sw=0.8, extra='stroke-linejoin="round"')
    if trunk:
        svg.pline([(x - 0.6, z0), (x - 0.45, base - 0.5), (x - r * 0.35, base + 0.4)], stroke=stroke, sw=0.9)
        svg.pline([(x + 0.6, z0), (x + 0.45, base - 0.5), (x + r * 0.4, base + 0.6)], stroke=stroke, sw=0.9)
        svg.pline([(x, base - 0.3), (x + 0.3, base + 1.5)], stroke=stroke, sw=0.7)


def window_elev(svg, x0, x1, z0, z1, panels=1, fill="#dfe3e2"):
    svg.rect(x0, z0, x1, z1, fill=fill, stroke=INK, sw=1.1)
    for k in range(1, panels):
        xx = x0 + k * (x1 - x0) / panels
        svg.line(xx, z0, xx, z1, INK, 0.9)
    # reflection diagonal
    svg.line(x0 + (x1 - x0) * 0.15, z0 + (z1 - z0) * 0.25, x0 + (x1 - x0) * 0.32, z0 + (z1 - z0) * 0.55, "#ffffff", 1.6)


def car_rear(svg, cx, zb):
    """A plain car seen from behind, ghosted (for scale in the open carport)."""
    for sx in (-1, 1):
        svg.rect(cx + sx * 2.1, zb, cx + sx * 2.85, zb + 0.8, fill="#55595d", stroke="none")
    body = [(cx - 3.05, zb + 0.55), (cx + 3.05, zb + 0.55), (cx + 3.1, zb + 2.7), (cx + 2.8, zb + 3.05),
            (cx - 2.8, zb + 3.05), (cx - 3.1, zb + 2.7)]
    svg.poly(body, fill="#eceae5", stroke=MID, sw=0.8)
    svg.poly([(cx - 2.6, zb + 3.05), (cx + 2.6, zb + 3.05), (cx + 2.05, zb + 4.6), (cx - 2.05, zb + 4.6)],
             fill="#eceae5", stroke=MID, sw=0.8)
    svg.poly([(cx - 2.2, zb + 3.25), (cx + 2.2, zb + 3.25), (cx + 1.8, zb + 4.4), (cx - 1.8, zb + 4.4)],
             fill="#c9ccce", stroke=MID, sw=0.5)
    for sx in (-1, 1):
        svg.rect(cx + sx * 2.95, zb + 2.25, cx + sx * 2.1, zb + 2.55, fill="#8b3a33", stroke="none")
    svg.rect(cx - 0.55, zb + 1.2, cx + 0.55, zb + 1.7, fill="#ffffff", stroke=MID, sw=0.5)


def south_elevation(ztop=40, notes=True):
    svg = SVG(-6, -2, 74, ztop, scale=12, pad=30)
    hatch_defs(svg)
    FF, C, FT = D.FF, D.CEIL, D.FASCIA_TOP
    elev_tree(svg, 31.0, 0, 38, 58, 7, stroke=FAINT, trunk=False)          # heritage oak behind
    elev_tree(svg, 44.0, D.HARDSCAPE, 24, 22, 3, stroke=LIGHT, trunk=False)  # courtyard tree
    ground(svg, -6, 74)
    # limestone wall with coursing (same seed as the 3D model)
    lw = D.LIMESTONE_WALL
    svg.rect(lw["x0"], 0, lw["x1"], C, fill=STONE, stroke=INK, sw=1.1)
    hole = D.EXT_WALLS[0]["openings"][0]
    hx0 = D.EXT_WALLS[0]["a"][0] + hole["off"]
    for (a, b, z0, z1) in limestone_courses(lw["x0"], lw["x1"], 0, C):
        if a < hx0 + hole["w"] and b > hx0 and z1 > FF + hole["sill"] and z0 < FF + hole["head"]:
            continue
        svg.rect(a + 0.015, z0 + 0.015, b - 0.015, z1 - 0.015, fill="none", stroke="#bfae8a", sw=0.45)
    window_elev(svg, hx0, hx0 + hole["w"], FF + hole["sill"], FF + hole["head"])
    # gate + jambs
    g = D.ENTRY_GATE
    svg.rect(g["x0"] - 0.33, 0, g["x0"], C, fill=INK, stroke=INK, sw=0.5)
    svg.rect(g["x1"], 0, g["x1"] + 0.5, C, fill=INK, stroke=INK, sw=0.5)
    svg.rect(g["x0"], g["z0"], g["x1"], C, fill="#e8c7a6", stroke=INK, sw=0.9)
    x = g["x0"] + 0.06
    while x + 0.125 < g["x1"]:
        svg.rect(x, g["z0"] + 0.15, x + 0.125, C - 0.15, fill=CEDAR, stroke="none")
        x += 0.29
    # cobogó
    c = D.COBOGO
    svg.rect(c["x0"] - 0.5, 0, c["x1"] + 0.3, c["z0"], fill="#e7e3da", stroke=INK, sw=0.8)
    cobogo_elev(svg, c["x0"], c["x1"], c["z0"], c["z1"])
    rx0, rx1 = min(p[0] for p in D.ROOF), max(p[0] for p in D.ROOF)
    sl = getattr(D, "CARPORT_SLIDER", None)
    gate_in = bool(sl) and sl.get("installed", True)
    if sl and not gate_in:   # open carport: back slat screen, the car, then the posts in front
        svg.rect(sl["x0"], D.HARDSCAPE, sl["x1"], C, fill="#f3ebe1", stroke=MID, sw=0.5)
        x = sl["x0"] + 0.15
        while x + 0.125 < sl["x1"]:
            svg.rect(x, D.HARDSCAPE + 0.1, x + 0.125, C - 0.1, fill="#dcb592", stroke="none")
            x += 0.29
        car_rear(svg, (sl["x0"] + sl["x1"]) / 2, D.HARDSCAPE * 0.5)
    if sl:   # carport: bronze posts (+ the full-height sliding cedar gate, shown closed)
        for px in (sl["x0"] + 0.25, sl["x1"] - 0.25):
            svg.rect(px - 0.17, 0, px + 0.17, C, fill=POCHE, stroke=POCHE, sw=0.4)
    if gate_in:
        svg.rect(sl["x0"] + 0.45, sl["z0"], sl["x1"] - 0.45, C - 0.05, fill="#e8c7a6", stroke=INK, sw=0.9)
        x = sl["x0"] + 0.5
        while x + 0.125 < sl["x1"] - 0.45:
            svg.rect(x, sl["z0"] + 0.15, x + 0.125, C - 0.2, fill=CEDAR, stroke="none")
            x += 0.29
    if sl:
        svg.rect(sl["x0"], 0, sl["x1"], D.HARDSCAPE * 0.5, fill="#dad6cf", stroke=INK, sw=0.5)   # drive apron
    else:    # cedar screen end (edge-on) + side yard
        sx = D.CEDAR_SCREEN["x"]
        svg.rect(sx - 0.3, D.HARDSCAPE, sx, C, fill=CEDAR, stroke=INK, sw=0.5)
    # roof plate: one continuous fascia
    svg.rect(rx0, C, rx1, FT, fill=POCHE, stroke=POCHE, sw=0.5)
    svg.rect(rx0, C - 0.12, rx1, C, fill="#d9a77d", stroke="none")   # cedar soffit edge
    # entry step
    svg.rect(g["x0"] - 0.3, 0, g["x1"] + 0.3, D.HARDSCAPE * 0.5, fill="#efe6d2", stroke=INK, sw=0.6)
    human(svg, g["x1"] + 4.5, 0)
    if not notes:   # clean view (comparison sheets): no leaders or level marks
        return svg.save("03_elevation_south.svg")
    level_marks(svg, rx1 + 3.5, [(FT, "T.O. ROOF  +12'-3\""), (C, "SOFFIT / CLG  +11'-0\""),
                                 (FF, "F.F.  +1'-0\""), (0, "GRADE  0'-0\"")])
    svg.leader(14.0, 6.0, 14.0, 17.5, "LUEDERS LIMESTONE ASHLAR, 3 COURSE HEIGHTS")
    cxm = (c["x0"] + c["x1"]) / 2 + 2
    svg.leader(cxm, 7.0, cxm, 17.5, "12x12x4 CONCRETE COBOGÓ, CIRCLE PATTERN")
    gxm = (g["x0"] + g["x1"]) / 2
    svg.leader(gxm, 8.0, gxm - 3.5, 15.0, "CEDAR SLAT PIVOT GATE", anchor="end")
    if gate_in:
        smx = (sl["x0"] + sl["x1"]) / 2
        svg.leader(smx, 6.0, smx + 1.5, 15.8, "SLIDING CEDAR CARPORT GATE")
    if sl:
        svg.leader(rx0 + 8.0, 11.6, rx0 + 8.0, 21.0, "15\" DARK BRONZE FASCIA")
    else:
        svg.leader(rx1 - 6.0, 11.6, rx1 - 2.0, 14.0, "15\" DARK BRONZE FASCIA")
    svg.leader(9.5, 5.0, 4.0, 15.0, "SLOT WINDOW", anchor="end")
    return svg.save("03_elevation_south.svg")


def north_elevation(ztop=30):
    # looking south: east on the left. map x' = 60 - x
    svg = SVG(-6, -2, 74, ztop, scale=12, pad=30)
    hatch_defs(svg)
    FF, C, FT = D.FF, D.CEIL, D.FASCIA_TOP
    X = lambda x: 60 - x
    ground(svg, -6, 74)
    w = [w for w in D.EXT_WALLS if w["id"] == "N-bar"][0]
    ax = w["a"][0]
    svg.rect(X(ax), 0, X(w["b"][0]), C, fill="#fbfaf6", stroke=INK, sw=1.1)
    centers = {}
    for o in w["openings"]:
        xa = ax - o["off"]
        xb = xa - o["w"]
        window_elev(svg, X(xa), X(xb), FF + o["sill"], FF + o["head"], panels=o.get("panels", 1))
        centers[o["kind"] if o["kind"] == "slider" else o.get("name", "")] = ((xa + xb) / 2, o)
    vp = [p for p in D.PAVING if p["name"] == "Veranda"]
    vx0, vy0, vx1, vy1 = vp[0]["rect"] if vp else (16.5, 80, 42.5, 92.5)
    svg.rect(X(vx1), 0, X(vx0), D.HARDSCAPE, fill="#efe6d2", stroke=INK, sw=0.6)
    gc = [f for f in D.FURNITURE if f["t"] == "grill_counter"]
    if gc:
        gx = gc[0]["x"]
        svg.rect(X(gx + gc[0]["w"] / 2), D.HARDSCAPE, X(gx - gc[0]["w"] / 2), D.HARDSCAPE + 3.05, fill=STONE, stroke=INK, sw=0.8)
    for (x, y) in D.POSTS:
        if y > 80:
            svg.rect(X(x + 0.17), D.HARDSCAPE, X(x - 0.17), C, fill=INK, stroke=INK, sw=0.3)
    rx0, rx1 = min(p[0] for p in D.ROOF), max(p[0] for p in D.ROOF)
    svg.rect(X(rx1), C, X(rx0), FT, fill=POCHE, stroke=POCHE, sw=0.5)
    ver = [z for z in D.CEDAR_SOFFITS if z["name"] == "Veranda"]
    if ver:
        svg.rect(X(ver[0]["x1"]), C - 0.12, X(ver[0]["x0"]), C, fill="#d9a77d", stroke="none")
    human(svg, X((vx0 + vx1) / 2 + 1.0), D.HARDSCAPE)
    level_marks(svg, X(rx0) + 3.0, [(FT, "T.O. ROOF  +12'-3\""), (C, "SOFFIT / CLG  +11'-0\""), (FF, "F.F.  +1'-0\"")])
    if "slider" in centers:
        cxs, o = centers["slider"]
        svg.leader(X(cxs), 5.0, X(cxs), 18.5, f"{fmt_ft(o['w'])} SLIDING GLASS WALL TO VERANDA", anchor="end")
    for name, (cxw, o) in centers.items():
        if "Kitchen" in name:
            svg.leader(X(cxw), 7.0, X(cxw), 15.5, "KITCHEN WINDOW")
        if "clerestory" in name.lower():
            svg.leader(X(cxw), 8.5, X(cxw), 15.5, "PRIMARY BATH CLERESTORY")
    if gc:
        svg.leader(X(gx), 3.0, X(gx), 21.5, "LIMESTONE GRILL COUNTER (CHURRASQUEIRA)")
    svg.leader(X(8), 3.0, X(4.5), -1.0 + 0.0, "SMOOTH WARM-WHITE STUCCO", anchor="start")
    return svg.save("04_elevation_north.svg")


def east_elevation(ztop=30):
    # looking west: south (street) on the left -> horizontal = y
    svg = SVG(20, -2, 106, ztop, scale=10.2, pad=30)
    hatch_defs(svg)
    FF, C, FT, H = D.FF, D.CEIL, D.FASCIA_TOP, D.HARDSCAPE
    elev_tree(svg, 46.5, H, 24, 22, 3, stroke=LIGHT, trunk=False)
    ground(svg, 20, 102)
    s = D.CEDAR_SCREEN
    cp = getattr(D, "CARPORT", None)
    if cp:
        # open carport side: slab edge, the cedar screen beyond (lighter), the gate edge-on, posts
        svg.rect(cp["y0"], 0, cp["y1"], H, fill="#e7e3da", stroke=INK, sw=0.7)
        svg.rect(s["y0"], H, s["y1"], C, fill="#f3e6d8", stroke=LIGHT, sw=0.6)
        y = s["y0"] + 0.05
        while y < s["y1"]:
            if not any(a0 - 0.05 < y < b0 for (a0, b0) in s.get("openings", [])):
                svg.rect(y, H + 0.1, y + s["slat_w"], C - 0.02, fill="#d8ab86", stroke="none")
            y += s["slat_w"] + s["gap"]
        sl = getattr(D, "CARPORT_SLIDER", None)
        if sl and sl.get("installed", True):
            svg.rect(sl["y"] - 0.15, sl["z0"], sl["y"] + 0.15, sl["z1"] - 0.15, fill=CEDAR, stroke=INK, sw=0.6)
        for (x, y) in D.POSTS:
            if x > cp["x1"] - 1.0 and cp["y0"] <= y <= cp["y1"]:
                svg.rect(y - 0.17, H, y + 0.17, C, fill=INK, stroke=INK, sw=0.3)
    for sc in getattr(D, "SLAT_SCREENS", []):
        if sc["axis"] == "y":   # courtyard east screen, in line with the house wall
            svg.rect(sc["y0"], 0, sc["y1"], H, fill="#e7e3da", stroke=INK, sw=0.7)
            svg.rect(sc["y0"], H, sc["y1"], C, fill="#efd9c4", stroke=INK, sw=0.9)
            y = sc["y0"] + 0.1
            while y < sc["y1"] - 0.1:
                svg.rect(y, H + 0.1, y + s["slat_w"], C - 0.02, fill=CEDAR, stroke="none")
                y += s["slat_w"] + s["gap"]
    # bar east wall + its windows
    w = [w for w in D.EXT_WALLS if w["id"] == "E-bar"][0]
    ya, yb = w["a"][1], w["b"][1]
    svg.rect(ya, 0, yb, C, fill="#fbfaf6", stroke=INK, sw=1.1)
    wins = {}
    for o in w["openings"]:
        window_elev(svg, ya + o["off"], ya + o["off"] + o["w"], FF + o["sill"], FF + o["head"])
        wins[o.get("name", "")] = ya + o["off"] + o["w"] / 2
    # veranda (set back at its own east edge) + post
    vp = [p for p in D.PAVING if p["name"] == "Veranda"]
    vx0, vy0, vx1, vy1 = vp[0]["rect"] if vp else (16.5, 80, 42.5, 92.5)
    svg.rect(vy0, 0, vy1, H, fill="#efe6d2", stroke=INK, sw=0.6)
    for (x, y) in D.POSTS:
        if y > 80 and x > 30:
            svg.rect(y - 0.17, H, y + 0.17, C, fill=INK, stroke=INK, sw=0.3)
    # roof: the plate at the east edge (carport + bar), the wing eave beyond over the open courtyard
    ys = sorted(set(p[1] for p in D.ROOF))
    ry0, ry1 = min(ys), max(ys)
    east = [p for p in D.ROOF if p[0] >= max(q[0] for q in D.ROOF) - 0.01]
    svg.rect(ry0, C, ry1, FT, fill=POCHE, stroke=POCHE, sw=0.5)
    if len(east) >= 4:
        gaps = sorted(p[1] for p in east)
        g0, g1 = gaps[1], gaps[2]
        svg.rect(g0, C, g1, FT, fill="#8a8d90", stroke=POCHE, sw=0.5)
    level_marks(svg, ry1 + 3.5, [(FT, "T.O. ROOF"), (C, "SOFFIT"), (FF, "F.F.")])
    if cp:
        svg.leader((cp["y0"] + cp["y1"]) / 2, 6.0, cp["y0"] + 1.0, 16.5, "OPEN CARPORT SIDE, CEDAR SCREEN BEYOND")
    for sc in getattr(D, "SLAT_SCREENS", []):
        if sc["axis"] == "y":
            svg.leader((sc["y0"] + sc["y1"]) / 2, 7.0, (sc["y0"] + sc["y1"]) / 2, 19.0,
                       "CEDAR SLAT SCREEN: MORNING LIGHT INTO THE PÁTIO")
    for name, yc in wins.items():
        if "bedroom" in name.lower():
            svg.leader(yc, 6.0, yc + 3.5, 17.5, "PRIMARY BEDROOM WINDOW")
        if "garden" in name.lower():
            svg.leader(yc, 6.5, yc + 4.0, 14.6, "SHOWER GARDEN WINDOW, FROSTED BELOW 5'")
    human(svg, 33.0, 0)
    return svg.save("05_elevation_east.svg")


def west_elevation(ztop=30):
    # looking east: north on the left -> horizontal = 125 - y
    svg = SVG(20, -2, 106, ztop, scale=10.2, pad=30)
    hatch_defs(svg)
    FF, C, FT = D.FF, D.CEIL, D.FASCIA_TOP
    Y = lambda y: 122 - y
    ground(svg, 20, 102)
    svg.rect(Y(80), 0, Y(30), C, fill="#fbfaf6", stroke=INK, sw=1.1)
    w = D.EXT_WALLS[5]
    for o in w["openings"]:
        ya = 80 - o["off"]
        yb = ya - o["w"]
        window_elev(svg, Y(ya), Y(yb), FF + o["sill"], FF + o["head"], panels=2)
    # limestone fin edge-on at the south end
    svg.rect(Y(30.0), 0, Y(29.67), C, fill=STONE, stroke=INK, sw=0.8)
    # veranda beyond (north)
    svg.rect(Y(92.5), 0, Y(80), D.HARDSCAPE, fill="#efe6d2", stroke=INK, sw=0.6)
    svg.rect(Y(91.8), D.HARDSCAPE, Y(91.45), C, fill=INK, stroke=INK, sw=0.3)
    svg.rect(Y(92.5), C, Y(27), FT, fill=POCHE, stroke=POCHE, sw=0.5)
    level_marks(svg, 96.0, [(FT, "T.O. ROOF"), (C, "SOFFIT"), (FF, "F.F.")])
    svg.leader(Y(54), 6.0, Y(54), 19.5, "BEDROOM 3 — EGRESS CASEMENT", anchor="end")
    svg.leader(Y(36), 6.0, Y(36), 16.5, "BEDROOM 2 — EGRESS CASEMENT", anchor="end")
    svg.leader(Y(29.8), 9.0, Y(29.8), 22.5, "LIMESTONE FIN", anchor="end")
    svg.leader(Y(70), 4.0, Y(70), 15.0, "QUIET SIDE: SOLID WALL AGAINST WEST SUN")
    human(svg, Y(40), 0)
    return svg.save("06_elevation_west.svg")


# ------------------------------------------------------------------ section
def section_aa():
    """Cut at x = 34 looking west. Horizontal = y (street on the left)."""
    svg = SVG(14, -4, 126, 42, scale=9.6, pad=30)
    hatch_defs(svg)
    FF, C, FT, H = D.FF, D.CEIL, D.FASCIA_TOP, D.HARDSCAPE
    # beyond (light): heritage oak, gallery facade, kitchen, wing eave
    elev_tree(svg, 110.0, 0, 38, 58, 7, stroke=LIGHT)
    svg.rect(30.33, H, 60, C, fill="#fbfbf9", stroke=FAINT, sw=0.6)              # gallery wall beyond
    for k in range(5):
        y0 = 35.75 + k * 23.75 / 5
        svg.rect(y0 + 0.08, FF, y0 + 23.75 / 5 - 0.08, FF + 9, fill="#f1f4f3", stroke=FAINT, sw=0.6)
    svg.rect(31.25, FF, 35.25, FF + 9, fill="#f3e3d3", stroke=FAINT, sw=0.6)         # pivot door
    svg.rect(36, C - 0.12, 56, C, fill="#d9a77d", stroke="none")                      # wing eave soffit
    svg.rect(36, C, 56, FT, fill="#b9bbbd", stroke="none")                            # wing fascia beyond
    svg.rect(69, FF, 79.5, FF + 3.05, fill="#f4f1ea", stroke=LIGHT, sw=0.6)           # kitchen run beyond
    svg.rect(69.85, FF, 73.35, FF + 3.05, fill="#e9e6df", stroke=LIGHT, sw=0.6)       # island
    svg.rect(70.3, FF, 73.7, FF + 2.6, fill="none", stroke=LIGHT, sw=0.6)             # dining table
    svg.rect(81.5, H, 89.0, H + 3.05, fill=STONE, stroke=LIGHT, sw=0.6)               # grill counter beyond
    svg.rect(91.45, H, 91.8, C, fill="#8b8d8f", stroke="none")                         # veranda post beyond
    # ground + cut slab / courtyard platform / veranda
    ground(svg, 14, 126)
    svg.rect(30.33, 0, 60, H - 0.12, fill="url(#earth)", stroke=INK, sw=0.8)
    svg.rect(30.33, H - 0.12, 36, H, fill=POCHE, stroke=POCHE, sw=0.3)
    svg.rect(52, H - 0.12, 60, H, fill=POCHE, stroke=POCHE, sw=0.3)
    svg.rect(60, 0, 80, FF, fill=POCHE, stroke=POCHE, sw=0.3)
    svg.rect(80, 0, 92.5, H, fill=POCHE, stroke=POCHE, sw=0.3)
    svg.rect(92.5, 0, 93.8, H * 0.5, fill=POCHE, stroke=POCHE, sw=0.3)
    # cobogó cut + curb
    svg.rect(29.95, 0, 30.38, FF, fill=POCHE, stroke=POCHE)
    for k in range(10):
        svg.rect(30.0, FF + k + 0.18, 30.33, FF + k + 0.82, fill=POCHE, stroke=POCHE, sw=0.3)
    # roof slabs (cut)
    svg.rect(27, C, 36, FT, fill=POCHE, stroke=POCHE)
    svg.rect(56, C, 92.5, FT, fill=POCHE, stroke=POCHE)
    svg.rect(27, C - 0.06, 36, C, fill=CEDAR, stroke="none")
    svg.rect(56, C - 0.06, 92.5, C, fill=CEDAR, stroke="none")
    # walls cut at y=60 (glass) and y=80 (glass) - slider heads
    for yy in (60.0, 79.5):
        svg.rect(yy, FF + 9, yy + 0.5, C, fill=POCHE, stroke=POCHE)
        svg.rect(yy + 0.2, FF, yy + 0.28, FF + 9, fill="#7fa7b5", stroke="none")
        svg.rect(yy + 0.06, FF, yy + 0.44, FF + 0.15, fill=INK, stroke="none")
    # sun angles, Austin 30.3°N: summer noon 83°, winter noon 36°
    for (alt, col, lab) in ((83.1, GOLD, "JUNE 21 NOON 83°"), (36.3, "#7f9fb0", "DEC 21 NOON 36°")):
        tx, tz = 60.25, FF + 0.5 if alt < 50 else 0
        ex, ez = 56.0, C
        # ray hitting the eave edge and continuing to the floor
        L = 22
        a = math.radians(alt)
        sx, sz = ex - L * math.cos(a), ez + L * math.sin(a)
        fx = ex + (ez - FF) / math.tan(a)
        svg.line(sx, sz, ex, ez, col, 1.1, extra='stroke-dasharray="5 3"')
        svg.line(ex, ez, fx, FF, col, 1.1, extra='stroke-dasharray="5 3"')
        svg.text(sx, sz, lab, 7.5, anchor="start", fill=col, weight=700, extra='dy="-4"')
    # labels
    for (y, z, s_) in ((33.1, 7.0, "COVERED ENTRY"), (46.0, 3.2, "PÁTIO"), (70.0, 7.5, "GREAT ROOM"),
                       (86.3, 7.5, "VERANDA"), (110.0, 2.0, "HERITAGE LIVE OAK")):
        svg.text(y, z, s_, 9, weight=700, fill=GREEN if s_ in ("PÁTIO", "VERANDA", "COVERED ENTRY") else INK, ls=1.2)
    svg.leader(60.0, 10.8, 63.0, 16.5, "CEDAR T&G CEILING CONTINUES OUTSIDE AS SOFFIT")
    svg.leader(70.0, 12.0, 74.0, 19.5, "LOW-SLOPE ROOF 1/4\":12\", R-38 INSULATION")
    svg.leader(70.0, 0.6, 76.0, -2.4, "POLISHED CONCRETE SLAB ON GRADE")
    svg.leader(30.1, 6.0, 24.5, 15.5, "COBOGÓ SCREEN", anchor="end")
    svg.leader(58.0, 11.4, 52.0, 19.5, "4' EAVE: SHADES SUMMER SUN, ADMITS WINTER SUN", anchor="end")
    level_marks(svg, 118.0, [(FT, "T.O. ROOF  +12'-3\""), (C, "CLG  +11'-0\""), (FF, "F.F.  +1'-0\""), (0, "GRADE")])
    human(svg, 44.0, H)
    human(svg, 66.0, FF)
    return svg.save("07_section_aa.svg")


# ------------------------------------------------------------------ cobogó detail
def cobogo_detail():
    svg = SVG(0, -0.6, 7.6, 3.6, scale=110, pad=30, flip=True)
    # single block elevation at large scale (0..1 ft) offset at x=0.3
    bx, bz = 0.3, 0.9
    svg.rect(bx, bz, bx + 1, bz + 1, fill="#f3f0e9", stroke=INK, sw=1.4)
    svg.add(f'<clipPath id="blk"><rect x="{svg.X(bx)}" y="{svg.Y(bz + 1)}" width="{svg.s}" height="{svg.s}"/></clipPath>')
    g = []
    for (cx, cz, r) in ([(bx + 0.5, bz + 0.5, 0.30)] + [(bx + i, bz + k, 0.24) for i in (0, 1) for k in (0, 1)] +
                        [(bx + 0.5, bz, 0.085), (bx + 0.5, bz + 1, 0.085), (bx, bz + 0.5, 0.085), (bx + 1, bz + 0.5, 0.085)]):
        g.append(f'<circle cx="{svg.X(cx):.1f}" cy="{svg.Y(cz):.1f}" r="{r * svg.s:.1f}" fill="#ffffff" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
    svg.add(f'<g clip-path="url(#blk)">{"".join(g)}</g>')
    svg.rect(bx, bz, bx + 1, bz + 1, fill="none", stroke=INK, sw=1.4)
    svg.dim(bx, bz, bx + 1, bz, -0.32, "12\"", size=10)
    svg.dim(bx, bz, bx, bz + 1, -0.3, "12\"", horizontal=False, size=10)
    svg.text(bx + 0.5, bz + 1.32, "BLOCK FACE", 10, weight=700, ls=1.5)
    for (lx, lz, t_) in ((bx + 0.5, bz + 0.5, "Ø 7.2\""), (bx + 0.12, bz + 0.12, "R 2.9\""),):
        svg.text(lx, lz, t_, 8.5, fill=MID, extra='dy="3"')
    # block section
    sx = 1.75
    svg.rect(sx, bz, sx + 0.333, bz + 1, fill="url(#diag)", stroke=INK, sw=1.4)
    svg.rect(sx - 0.01, bz + 0.2, sx + 0.343, bz + 0.8, fill="#ffffff", stroke=INK, sw=0.9)
    svg.dim(sx, bz, sx + 0.333, bz, -0.32, "4\"", size=10)
    svg.text(sx + 0.17, bz + 1.32, "SECTION", 10, weight=700, ls=1.5)
    # 4x3 tiled field
    fx, fz = 2.75, 0.4
    svg.defs.append("")
    cobogo_elev(svg, fx, fx + 4, fz, fz + 3)
    for i in range(1, 4):
        svg.line(fx + i, fz, fx + i, fz + 3, "#c9c2b4", 0.6, extra='stroke-dasharray="3 3"')
    for k in range(1, 3):
        svg.line(fx, fz + k, fx + 4, fz + k, "#c9c2b4", 0.6, extra='stroke-dasharray="3 3"')
    svg.text(fx + 2, fz + 3.32, "TILED FIELD — CIRCLES COMPLETE ACROSS JOINTS", 10, weight=700, ls=1.2)
    svg.text(bx + 0.5, -0.35, "Precast concrete breeze block, white cement. Laid stack-bond with 3/8\" joints, "
             "#4 rebar every 2nd course into steel jambs; top course tight to the canopy soffit.",
             9, anchor="start", fill=MID, extra=f'dx="{-0.5 * svg.s}"')
    return svg.save("08_cobogo_detail.svg")


def main():
    hatch = None
    outs = [site_plan(), floor_plan(), south_elevation(), north_elevation(), east_elevation(),
            west_elevation(), section_aa(), cobogo_detail(), bath_plan(), hall_bath_plan()]
    for o in outs:
        print(o)


if __name__ == "__main__":
    main()
