"""Phase 2 concept drawings: Casa 02 and Casita floor plans, and site plans of the winning layouts.

    python3 phase2/concepts/concepts.py
    node casa01/signoff/print_pdf.js phase2/concepts/out/concepts.html phase2/concepts/Phase2_Concepts.pdf

Homes come from homes.py (plan data in each home's own frame). A site places homes on a lot with a
transform (mirror, rotate, move), adds paving, pátios, paths, fences, trees and carts, and checks the
result against the same caps as the test-fit study (phase2/testfit).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "casa01"))
from model import homes as H  # noqa: E402
from model.sites import (SITES, HOME_RULES, T, check_site, ellipse_pts, footprint, garden_wall, screen_parts,  # noqa: E402
                         rect_pts, tp, tpoly)
import drawings as DR  # noqa: E402  (Casa 01 drawing kit: SVG class, colours, trees, north arrow)

INK, POCHE, MID, LIGHT, FAINT, GREEN = DR.INK, DR.POCHE, DR.MID, DR.LIGHT, DR.FAINT, DR.GREEN
FONT = DR.FONT
fmt_ft = DR.fmt_ft


# ---------------------------------------------------------------- plan drawing
def draw_walls(svg, plan, t, detail):
    for w in plan["walls"]:
        (ax, ay), (bx, by) = w["a"], w["b"]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        th = w["t"]
        d0, d1 = (0.0, th) if w["ext"] else (-th / 2, th / 2)

        def P(s, d):
            return tp(t, ax + ux * s + nx * d, ay + uy * s + ny * d)
        cuts = sorted(w["openings"], key=lambda o: o["off"])
        s = 0.0
        for o in cuts + [dict(off=L, w=0, kind="end")]:
            if o["off"] - s > 1e-6:
                svg.poly([P(s, d0), P(o["off"], d0), P(o["off"], d1), P(s, d1)], fill=POCHE, stroke=POCHE, sw=0.2)
            s = o["off"] + o["w"]
        for o in cuts:
            s0, s1 = o["off"], o["off"] + o["w"]
            k = o["kind"]
            if k in ("window", "slider", "bypass"):
                for s_ in (s0, s1):
                    xa, ya = P(s_, d0)
                    xb, yb = P(s_, d1)
                    svg.line(xa, ya, xb, yb, INK, 0.6)
                if k == "window":
                    for f in (0.38, 0.62):
                        xa, ya = P(s0, d0 + (d1 - d0) * f)
                        xb, yb = P(s1, d0 + (d1 - d0) * f)
                        svg.line(xa, ya, xb, yb, INK, 0.5 if detail == "full" else 0.35)
                else:
                    mid = (s0 + s1) / 2
                    for (a_, b_, f) in ((s0, mid + 0.25, 0.3), (mid - 0.25, s1, 0.7)):
                        xa, ya = P(a_, d0 + (d1 - d0) * f)
                        xb, yb = P(b_, d0 + (d1 - d0) * f)
                        svg.line(xa, ya, xb, yb, INK, 0.9 if detail == "full" else 0.6)
            elif k == "door":
                sg = 1.0 if o["side"] == "L" else -1.0
                face = d1 if sg > 0 else d0
                hs = s0 if o["hinge"] == "s" else s1
                cs = s1 if o["hinge"] == "s" else s0
                hx, hy = ax + ux * hs + nx * face, ay + uy * hs + ny * face
                ex, ey = hx + nx * sg * o["w"], hy + ny * sg * o["w"]
                cx_, cy_ = ax + ux * cs + nx * face, ay + uy * cs + ny * face
                H_, E_, C_ = tp(t, hx, hy), tp(t, ex, ey), tp(t, cx_, cy_)
                svg.line(H_[0], H_[1], E_[0], E_[1], INK, 1.0 if detail == "full" else 0.6)
                a0 = math.atan2(C_[1] - H_[1], C_[0] - H_[0])
                a1 = math.atan2(E_[1] - H_[1], E_[0] - H_[0])
                dlt = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                svg.arc(H_[0], H_[1], o["w"], a0, a0 + dlt, stroke=MID, sw=0.45, extra='stroke-dasharray="2 1.5"')


def draw_fixture(svg, f, t, detail):
    k = f["kind"]
    sw = 0.6 if detail == "full" else 0.4
    if k == "wc":
        x, y = f["at"]
        dirn = 1 if f.get("rot", 0) == 0 else -1
        svg.poly(tpoly(t, rect_pts((x - 0.85, y - 0.3, x + 0.85, y + 0.3))), fill="#fff", stroke=INK, sw=sw)
        svg.poly(tpoly(t, ellipse_pts(x, y + dirn * 1.25, 0.62, 0.92)), fill="#fff", stroke=INK, sw=sw)
        return
    r = f["rect"]
    x0, y0, x1, y1 = r
    if k == "car":
        svg.poly(tpoly(t, rect_pts(r)), fill="none", stroke=MID, sw=0.6, extra='stroke-dasharray="3 2"')
        return
    if k == "mech":
        svg.poly(tpoly(t, rect_pts(r)), fill="none", stroke=MID, sw=0.5, extra='stroke-dasharray="2 1.5"')
        for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
            a, b = tp(t, ax, ay), tp(t, bx, by)
            svg.line(a[0], a[1], b[0], b[1], MID, 0.4)
        return
    fill = {"counter": "#f1eee6", "island": "#f1eee6", "fridge": "#f1eee6", "table": "#fbf8f1", "sofa": "#efe8da",
            "bed": "#fbf8f1", "shower": "#e8eef0", "lav": "#fff", "wd": "#fff", "range": "#f1eee6",
            "sink": "#e8eef0", "tub": "#e8eef0", "desk": "#fbf8f1"}.get(k, "#fff")
    svg.poly(tpoly(t, rect_pts(r)), fill=fill, stroke=INK if detail == "full" else MID, sw=sw)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if k == "range":
        for ox in (-0.5, 0.5):
            for oy in (-0.45, 0.45):
                svg.poly(tpoly(t, ellipse_pts(cx + ox, cy + oy, 0.32, 0.32, 10)), fill="none", stroke=INK, sw=0.4)
    elif k == "sink" or k == "lav":
        svg.poly(tpoly(t, ellipse_pts(cx, cy, (x1 - x0) * 0.32, (y1 - y0) * 0.32, 14)), fill="none", stroke=INK, sw=0.4)
    elif k == "shower":
        svg.poly(tpoly(t, ellipse_pts(cx, cy, 0.18, 0.18, 8)), fill=INK, stroke="none")
        if detail == "full":
            a, b = tp(t, x0, y0), tp(t, x1, y1)
            svg.line(a[0], a[1], b[0], b[1], LIGHT, 0.4)
    elif k == "bed":
        # pillows at the head: the far end (max y) in the home's frame, or the near end with head="s"
        south = f.get("head") == "s"
        for px0 in (x0 + 0.3, cx + 0.15):
            pa, pb = (y0 + 0.3, y0 + 1.3) if south else (y1 - 1.3, y1 - 0.3)
            svg.poly(tpoly(t, rect_pts((px0, pa, px0 + (x1 - x0) / 2 - 0.45, pb))), fill="#fff", stroke=MID, sw=0.35)
        yl = y0 + 2.0 if south else y1 - 2.0
        a, b = tp(t, x0, yl), tp(t, x1, yl)
        svg.line(a[0], a[1], b[0], b[1], MID, 0.35)
    elif k == "tub":
        svg.poly(tpoly(t, rect_pts((x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3))), fill="none", stroke=INK, sw=0.4)
    elif k == "sofa":
        horiz = (x1 - x0) >= (y1 - y0)
        if horiz:
            a, b = tp(t, x0, y1 - 0.8), tp(t, x1, y1 - 0.8)
        else:
            a, b = tp(t, x1 - 0.8, y0), tp(t, x1 - 0.8, y1)
        svg.line(a[0], a[1], b[0], b[1], MID, 0.4)
    elif k == "wd":
        horiz = (x1 - x0) >= (y1 - y0)
        if horiz:
            m = (x0 + x1) / 2
            a, b = tp(t, m, y0), tp(t, m, y1)
        else:
            m = (y0 + y1) / 2
            a, b = tp(t, x0, m), tp(t, x1, m)
        svg.line(a[0], a[1], b[0], b[1], INK, 0.4)


def stair_geometry(st):
    """Foot and top of a straight stair along y, the direction of climb, the run of one tread, and the tread count.
    st: rect, top ("front" = the low-y end, or "back"), risers."""
    x0, y0, x1, y1 = st["rect"]
    top_front = st.get("top", "back") == "front"
    foot, top = (y1, y0) if top_front else (y0, y1)
    sgn = -1.0 if top_front else 1.0
    n = st.get("risers", 17) - 1
    return foot, top, sgn, abs(top - foot) / n, n


def draw_stair(svg, st, t, detail):
    """Lower floor: treads from the foot up to the cut line, a break line, the rest dashed overhead; UP arrow.
    Upper floor: the whole flight seen from above, DN arrow from the top."""
    x0, y0, x1, y1 = st["rect"]
    foot, top, sgn, run, n = stair_geometry(st)
    upper = st.get("floor") == "upper"
    cut = None if upper else st.get("cut")
    end = top if cut is None else cut
    ya, yb = sorted((foot, end))
    svg.poly(tpoly(t, rect_pts((x0, ya, x1, yb))), fill="#ffffff", stroke=INK, sw=0.6)
    for i in range(1, n):
        y = foot + sgn * i * run
        if (y - end) * sgn > 1e-6:
            break
        a, b = tp(t, x0, y), tp(t, x1, y)
        svg.line(a[0], a[1], b[0], b[1], LIGHT if upper else MID, 0.45)
    if cut is not None:
        p = [tp(t, x0, cut - sgn * 0.35), tp(t, (x0 + x1) / 2 - 0.3, cut - sgn * 0.35),
             tp(t, (x0 + x1) / 2, cut + sgn * 0.35), tp(t, x1, cut + sgn * 0.35)]
        svg.pline(p, stroke=INK, sw=0.6)
        za, zb = sorted((cut, top))
        svg.poly(tpoly(t, rect_pts((x0, za, x1, zb))), fill="none", stroke=MID, sw=0.45, extra='stroke-dasharray="3 2"')
    cx = (x0 + x1) / 2
    if upper:
        a, tip, label_at = tp(t, cx, top - sgn * 0.5), tp(t, cx, foot + sgn * 1.0), (cx, top - sgn * 1.3)
    else:
        a, tip, label_at = tp(t, cx, foot - sgn * 0.5), tp(t, cx, end - sgn * 1.0), (cx, foot - sgn * 1.4)
    svg.line(a[0], a[1], tip[0], tip[1], INK, 0.7)
    ang = math.atan2(tip[1] - a[1], tip[0] - a[0])
    L_ = 0.6
    svg.poly([tip, (tip[0] - L_ * math.cos(ang - 0.45), tip[1] - L_ * math.sin(ang - 0.45)),
              (tip[0] - L_ * math.cos(ang + 0.45), tip[1] - L_ * math.sin(ang + 0.45))], fill=INK, stroke="none")
    if detail == "full":
        lx, ly = tp(t, *label_at)
        svg.text(lx, ly, "DN" if upper else "UP", 6.2, weight=700, extra='dy="2"')


def room_label(svg, room, t, detail, fs):
    if room.get("label") is False:
        return
    x0, y0, x1, y1 = room["rect"]
    lx, ly = room.get("lab", ((x0 + x1) / 2, (y0 + y1) / 2))
    if detail != "full":
        lx, ly = (x0 + x1) / 2, (y0 + y1) / 2
    cx, cy = tp(t, lx, ly)
    if detail == "full":
        narrow = (x1 - x0) < 7.5
        name = room.get("short", room["name"]) if narrow else room["name"]
        svg.text(cx, cy, name.upper(), fs * (0.9 if narrow else 1.0), weight=700, ls=0.8, extra='dy="-2"')
        if not narrow:
            svg.text(cx, cy, f"{fmt_ft(x1 - x0)} × {fmt_ft(y1 - y0)}", fs * 0.85, fill=MID, extra=f'dy="{fs * 1.05:.1f}"')
        if room.get("note"):
            svg.text(cx, cy, room["note"], fs * 0.78, fill=MID, extra=f'dy="{fs * 2.1:.1f}"')
    else:
        svg.text(cx, cy, room.get("short", room["name"]), fs, fill=MID, ls=0.3, extra='dy="2"')


LIMESTONE = "#ddd3c2"
CALCADA, CALCADA_BAND = "#363531", "#dcd7cd"


def draw_calcada(svg, plan, t, detail):
    """Black calçada portuguesa rugs with their light concrete band."""
    for r in plan.get("calcada", []):
        svg.poly(tpoly(t, rect_pts(r)), fill=CALCADA_BAND, stroke="none")
        x0, y0, x1, y1 = r
        b = 0.3 if min(x1 - x0, y1 - y0) > 1.5 else 0.12
        svg.poly(tpoly(t, rect_pts((x0 + b, y0 + b, x1 - b, y1 - b))), fill=CALCADA, stroke="none")


def draw_stone(svg, plan, t, detail):
    """Lueders limestone ashlar: a band on the outer face of the stone walls (cut at the openings), and the piers."""
    full = detail == "full"
    for run in H.stone_runs(plan):
        (ax, ay), (ux, uy), (nx, ny), L = run["a"], run["u"], run["n"], run["L"]
        free, s0 = [], 0.0
        for h0, h1, _o in run["holes"]:
            if h0 > s0:
                free.append((s0, h0))
            s0 = max(s0, h1)
        if s0 < L:
            free.append((s0, L))
        dd = 0.34
        for q0, q1 in free:
            P = [(ax + ux * q + nx * d, ay + uy * q + ny * d) for q, d in ((q0, 0), (q1, 0), (q1, dd), (q0, dd))]
            svg.poly(tpoly(t, P), fill=LIMESTONE, stroke=INK, sw=0.45 if full else 0.3)
            if full:
                q = q0 + 0.9
                while q < q1 - 0.3:
                    a_, b_ = tp(t, ax + ux * q, ay + uy * q), tp(t, ax + ux * q + nx * dd, ay + uy * q + ny * dd)
                    svg.line(a_[0], a_[1], b_[0], b_[1], MID, 0.35)
                    q += 1.6
    for r in plan.get("stone", {}).get("piers", []):
        svg.poly(tpoly(t, rect_pts(r)), fill=LIMESTONE, stroke=INK, sw=0.7 if full else 0.5)




def cobogo_band(svg, pts_a, pts_b, n, full, t=None):
    """A cobogó screen in plan: an outlined band with one ring per 12 in block when drawn at plan scale.
    pts_a, pts_b: (x0, y0, x1, y1) of the band in the frame of t."""
    x0, y0, x1, y1 = pts_a
    svg.poly(tpoly(t, rect_pts(pts_a)), fill="#ffffff", stroke=INK, sw=0.7 if full else 0.6)
    if full:
        for i in range(n):
            cx, cy = tp(t, x0 + (x1 - x0) * (i + 0.5) / n, (y0 + y1) / 2) if t else (x0 + (x1 - x0) * (i + 0.5) / n,
                                                                                     (y0 + y1) / 2)
            svg.circle(cx, cy, 0.1, fill="none", stroke=INK, sw=0.45)
    else:
        a, b = tp(t, x0, (y0 + y1) / 2), tp(t, x1, (y0 + y1) / 2)
        svg.line(a[0], a[1], b[0], b[1], INK, 0.5, extra='stroke-dasharray="0.8 1.2"')


LANTERN_LABEL = True        # the developed plans (phase2/plans) label the screen with a leader instead


def draw_lantern(svg, plan, t, detail):
    """The two-story cobogó screen in front of the entry and stair (facade direction C)."""
    lan = plan.get("lantern")
    if not lan or lan.get("upper_only"):                     # drawn on the upper floor plan instead
        return
    (x0, x1), (y0, y1) = lan["x"], lan["y"]
    op = lan.get("opening")
    segs = [(a, b) for a, b in ([(x0, op[0]), (op[1], x1)] if op else [(x0, x1)]) if b - a > 0.01]
    for a, b in segs:
        cobogo_band(svg, (a, y0, b, y1), None, int(round(b - a)), detail == "full", t)
    if op:   # the blocks run on overhead, above the door
        svg.poly(tpoly(t, rect_pts((op[0], y0, op[1], y1))), fill="none", stroke=MID, sw=0.5,
                 extra='stroke-dasharray="3 2"')
    if detail == "full" and LANTERN_LABEL:
        cx, cy = tp(t, (x0 + x1) / 2, y0 - 1.0)
        svg.text(cx, cy, lan["note"].upper(), 5.8, fill=MID, ls=0.6, extra='dy="2"')


def draw_porch(svg, plan, t, detail, fs):
    """The Casita's covered porch: roof outline (dashed), two posts, and its size."""
    pr = plan.get("porch")
    if not pr:
        return
    if detail == "full":
        svg.poly(tpoly(t, rect_pts(pr["rect"])), fill="#f4f1ea", stroke="none")
    svg.poly(tpoly(t, rect_pts(pr["roof"])), fill="none", stroke=MID, sw=0.6, extra='stroke-dasharray="6 3"')
    for cx, cy in pr["posts"]:
        svg.poly(tpoly(t, rect_pts((cx - 0.25, cy - 0.25, cx + 0.25, cy + 0.25))), fill=INK, stroke="none")
    x0, y0, x1, y1 = pr["rect"]
    cx, cy = tp(t, (x0 + x1) / 2, (y0 + y1) / 2)
    if detail == "full":
        svg.text(cx, cy, "COVERED PORCH", fs, weight=700, ls=0.8, extra='dy="-2"')
        svg.text(cx, cy, f"{fmt_ft(x1 - x0)} × {fmt_ft(y1 - y0)}", fs * 0.85, fill=MID, extra=f'dy="{fs * 1.05:.1f}"')
        svg.text(cx, cy, "cedar ceiling", fs * 0.78, fill=MID, extra=f'dy="{fs * 2.1:.1f}"')
    else:
        svg.text(cx, cy, "Porch", fs, fill=MID, ls=0.3, extra='dy="2"')


def draw_skylights(svg, plan, t, detail):
    """Skylights overhead: dashed outline with diagonals."""
    for sk in plan.get("skylights", []):
        x0, y0, x1, y1 = sk["rect"]
        svg.poly(tpoly(t, rect_pts(sk["rect"])), fill="none", stroke=MID, sw=0.5, extra='stroke-dasharray="3 2"')
        for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
            a, b = tp(t, ax, ay), tp(t, bx, by)
            svg.line(a[0], a[1], b[0], b[1], LIGHT, 0.35, extra='stroke-dasharray="3 2"')


def draw_sunshade(svg, plan, t, detail):
    """The cedar slat sunshade over the back slider: dashed outline (overhead) with its slats."""
    sh = plan.get("sunshade")
    if not sh:
        return
    x0, y0, x1, y1 = sh["rect"]
    svg.poly(tpoly(t, rect_pts(sh["rect"])), fill="none", stroke=DR.CEDAR, sw=0.6, extra='stroke-dasharray="4 2"')
    y = y0 + 0.5
    while y < y1 - 0.2:
        a, b = tp(t, x0, y), tp(t, x1, y)
        svg.line(a[0], a[1], b[0], b[1], DR.CEDAR, 0.3, extra='stroke-dasharray="4 2"')
        y += 0.6
    if detail == "full":
        cx, cy = tp(t, (x0 + x1) / 2, y1 + 0.9)
        svg.text(cx, cy, "CEDAR SUNSHADE ABOVE", 5.8, fill="#6e5a3c", ls=0.6, extra='dy="2"')


def draw_canopy(svg, plan, t, detail):
    """A cedar canopy over a front door: dashed outline (overhead)."""
    cn = plan.get("canopy")
    if not cn:
        return
    svg.poly(tpoly(t, rect_pts(cn["rect"])), fill="none", stroke=DR.CEDAR, sw=0.6, extra='stroke-dasharray="4 2"')
    if detail == "full":
        x0, y0, x1, y1 = cn["rect"]
        cx, cy = tp(t, x0 - 1.6, (y0 + y1) / 2)
        svg.add(f'<text x="{svg.X(cx):.1f}" y="{svg.Y(cy):.1f}" font-family="{FONT}" font-size="5.8" fill="#6e5a3c" '
                f'letter-spacing="0.6" text-anchor="middle" transform="rotate(-90 {svg.X(cx):.1f} {svg.Y(cy):.1f})">'
                f'FRONT DOOR · CANOPY ABOVE</text>')


def draw_garden_wall(svg, s):
    """The Casita's street wall and any privacy screens: limestone piers, a cedar gate swinging into the garden,
    cobogó between."""
    for sc in s.get("screens", []):
        _draw_wall(svg, screen_parts(sc))
    gw = garden_wall(s)
    if gw:
        _draw_wall(svg, gw)


def _draw_wall(svg, gw):
    y = gw["y"]
    for p0, p1 in gw["piers"]:
        svg.rect(p0, y - 0.4, p1, y + 0.4, fill=LIMESTONE, stroke=INK, sw=0.6)
    for p0, p1 in gw.get("posts", []):
        svg.rect(p0, y - 0.15, p1, y + 0.15, fill=INK, stroke="none")
    c0, c1 = gw["cobogo"]
    cobogo_band(svg, (c0, y - 0.17, c1, y + 0.17), None, int(round(c1 - c0)), True)
    if gw["gate"]:
        g0, g1 = gw["gate"]
        svg.line(g0, y, g0, y + (g1 - g0), DR.CEDAR, 1.4)                  # leaf, open into the garden
        svg.arc(g0, y, g1 - g0, 0.0, math.pi / 2, stroke=MID, sw=0.45, extra='stroke-dasharray="2 1.5"')
        svg.text((g0 + g1) / 2, y - 2.1, "CEDAR GATE", 5.0, fill="#6e5a3c", ls=0.4, extra='dy="2"')
    svg.text((c0 + c1) / 2, y - 2.1, "COBOGÓ", 5.0, fill=MID, ls=0.4, extra='dy="2"')


def draw_plan(svg, plan, t=None, detail="full", fs=8.5, labels=True):
    """Draw one floor plan into svg. t maps the home's frame to the drawing; detail: full | site."""
    fp = rect_pts((0, 0, plan["W"], plan["D"]))
    # interior floor tone, then the outdoor bay
    walls_pts = [w["a"] for w in plan["walls"] if w["ext"]]
    svg.poly(tpoly(t, walls_pts), fill="#fbfaf6", stroke="none")
    for room in plan["rooms"]:
        if room.get("outdoor"):
            svg.poly(tpoly(t, rect_pts(room["rect"])), fill="#ecebe6", stroke="none")
    if "void" in plan:
        pass
    draw_calcada(svg, plan, t, detail)
    for f in plan.get("fixtures", []):
        if detail == "site" and f["kind"] in ("table", "sofa", "range", "sink", "lav", "wd", "island"):
            continue
        draw_fixture(svg, f, t, detail)
    if plan.get("stair"):
        draw_stair(svg, plan["stair"], t, detail)
    draw_walls(svg, plan, t, detail)
    # the upper floor over an open bay, and the columns that carry it
    if any(r.get("outdoor") for r in plan["rooms"]):
        svg.poly(tpoly(t, fp), fill="none", stroke=MID, sw=0.6, extra='stroke-dasharray="6 3"')
    draw_stone(svg, plan, t, detail)
    for cx, cy in plan.get("columns", []):
        svg.poly(tpoly(t, rect_pts((cx - 0.3, cy - 0.3, cx + 0.3, cy + 0.3))), fill=INK, stroke="none")
    if plan.get("gate"):
        (gx0, gy0), (gx1, gy1) = plan["gate"]
        vert = abs(gx1 - gx0) < 1e-6                          # a side gate (side-drive plan) runs along y
        a, b = (tp(t, gx0 + 0.25, gy0), tp(t, gx1 + 0.25, gy1)) if vert else (tp(t, gx0, gy0 + 0.25), tp(t, gx1, gy1 + 0.25))
        svg.line(a[0], a[1], b[0], b[1], DR.CEDAR, 1.6 if detail == "full" else 1.0, extra='stroke-dasharray="1.5 1.5"')
    for (ax, ay), (bx, by) in plan.get("slats", []):            # cedar slats beside the stair
        a, b = tp(t, ax, ay), tp(t, bx, by)
        svg.line(a[0], a[1], b[0], b[1], DR.CEDAR, 1.5 if detail == "full" else 0.9, extra='stroke-dasharray="0.8 1"')
    draw_lantern(svg, plan, t, detail)
    draw_porch(svg, plan, t, detail, fs)
    draw_skylights(svg, plan, t, detail)
    draw_sunshade(svg, plan, t, detail)
    draw_canopy(svg, plan, t, detail)
    if labels:
        for room in plan["rooms"]:
            room_label(svg, room, t, detail, fs)


# ---------------------------------------------------------------- floor plan sheets
def svg_str(svg):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg.w:.0f} {svg.h:.0f}" '
            f'preserveAspectRatio="xMidYMid meet"><defs>{"".join(svg.defs)}</defs>'
            f'<rect width="100%" height="100%" fill="#ffffff"/>{"".join(svg.items)}</svg>')


def plan_svg(plan, scale=13.0, note_front="FRONT: STREET, ALLEY OR SIDE STREET"):
    W, Dd = plan["W"], plan["D"]
    xr = plan["porch"]["roof"][2] if plan.get("porch") else W        # the Casita's porch sits off the right side
    svg = DR.SVG(-5.5, -7.5, xr + 5.5, Dd + (5.0 if plan.get("sunshade") else 4.0), scale=scale, pad=14)
    draw_plan(svg, plan, None, "full", fs=8.2)
    svg.dim(0, 0, W, 0, -4.2, size=8.5)
    if plan.get("porch"):
        svg.dim(0, 0, 0, Dd, -3.0, horizontal=False, size=8.5)
    else:
        svg.dim(W, 0, W, Dd, 3.0, horizontal=False, size=8.5)
    svg.text(W / 2, -6.6, note_front, 7.2, fill=MID, ls=1.2)
    return svg_str(svg)


# ---------------------------------------------------------------- sites
def fence(svg, pts, color="#8a6a4a"):
    svg.pline(pts, stroke=color, sw=1.1)


def stepping(svg, pts, step=2.2):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        for i in range(n):
            f = (i + 0.5) / n
            x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            svg.rect(x - 0.8, y - 0.55, x + 0.8, y + 0.55, fill="#e2ddd2", stroke=LIGHT, sw=0.3)


def site_svg(s):
    W, L = s["lot"]["W"], s["lot"]["L"]
    lot = s["lot"]
    svg = DR.SVG(-6, -14, W + (13 if lot.get("corner") else 6), L + (13 if lot.get("alley") else 6), scale=6.6, pad=10)
    # street, sidewalk, alley, side street
    svg.rect(-6, -14, W + (13 if lot.get("corner") else 6), -6, fill="#e4e1d9", stroke="none")
    svg.rect(-6, -5, W + (13 if lot.get("corner") else 6), -1, fill="#efede7", stroke="none")
    svg.text(W / 2, -10, "STREET", 8, fill=MID, ls=2, extra='dy="3"')
    if lot.get("alley"):
        svg.rect(-6, L + 1, W + 6, L + 13, fill="#e4e1d9", stroke="none")
        svg.text(W / 2, L + 7, "ALLEY", 8, fill=MID, ls=2, extra='dy="3"')
    if lot.get("corner"):
        svg.rect(W + 1, -14, W + 13, L + 6, fill="#e4e1d9", stroke="none")
        cx, cy = svg.X(W + 7), svg.Y(L / 2)
        svg.add(f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="8" fill="{MID}" letter-spacing="2" '
                f'text-anchor="middle" transform="rotate(-90 {cx:.1f} {cy:.1f})">SIDE STREET</text>')
    # lot, ground, setbacks
    svg.rect(0, 0, W, L, fill="#f3f1ea", stroke="none")
    svg.rect(0, 0, W, HOME_RULES["front"], fill="#eceee2", stroke="none")
    for p in s["patios"]:
        svg.rect(*p, fill="#e1ead6", stroke="none")
    east = W - HOME_RULES["side"]
    svg.rect(HOME_RULES["side"], HOME_RULES["front"], east, L - HOME_RULES["rear"], fill="none", stroke=LIGHT, sw=0.6,
             extra='stroke-dasharray="4 3"')
    for k, r in s["pave"]:
        col = {"Terrace": "#e6e0d2", "Walk": "#e6e0d2", "Carts": "#d9cdb8"}.get(k, "#d8d4ca")
        svg.rect(*r, fill=col, stroke="none")
        if k in ("Drive", "Parking") and (r[3] - r[1]) > 12:
            cx, cy = svg.X((r[0] + r[2]) / 2), svg.Y((r[1] + r[3]) / 2)
            rot = -90 if (r[2] - r[0]) < (r[3] - r[1]) else 0
            svg.add(f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="7" fill="{MID}" text-anchor="middle" '
                    f'letter-spacing="1" transform="rotate({rot} {cx:.1f} {cy:.1f})">{k.upper()}</text>')
        if k == "Carts":
            svg.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, f"{3 * len(s['homes'])} CARTS", 5.5, fill="#6e5a3c",
                     extra='dy="2"')
    if s.get("drive_walk"):                                               # limestone walk along the drive, lit
        dw = s["drive_walk"]
        svg.rect(*dw, fill="#ebe5d6", stroke=LIGHT, sw=0.3)
        yb = dw[1] + 6.0
        while yb < dw[3] - 2:
            svg.circle(dw[0] + 0.5, yb, 0.35, fill=INK, stroke="none")         # bollard lights
            yb += 14.0
        cx, cy = svg.X((dw[0] + dw[2]) / 2), svg.Y((dw[1] + dw[3]) / 2)
        svg.add(f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="5.2" fill="{MID}" text-anchor="middle" '
                f'letter-spacing="0.8" transform="rotate(-90 {cx:.1f} {cy:.1f})">LIT WALK</text>')
    for pts in s.get("paths", []):
        stepping(svg, pts)
    for x, y, rr in s["trees"]:
        DR.tree_canopy(svg, x, y, rr, int(x * 7 + y), fill="rgba(95,116,88,0.10)", stroke=GREEN, sw=0.7)
    for pts in s.get("fence", []):
        fence(svg, pts)
    for pts in s.get("walls", []):
        svg.pline(pts, stroke=INK, sw=1.6)
    draw_calcada(svg, dict(calcada=s.get("calcada", [])), None, "site")
    for r in s.get("address_walls", []):          # low limestone walls at the walks: mailbox, number, light
        svg.rect(*r, fill=LIMESTONE, stroke=INK, sw=0.5)
    draw_garden_wall(svg, s)
    svg.rect(0, 0, W, L, fill="none", stroke=INK, sw=0.9, extra='stroke-dasharray="10 3 2 3"')
    # homes
    for h in s["homes"]:
        draw_plan(svg, h["plan"], h["t"], "site", fs=5.2, labels=True)
    for h in s["homes"]:
        x0, y0, x1, y1 = footprint(h["t"])
        tag_y = y0 - 2.2 if y0 > 18 else y1 + 2.6
        tx = (x0 + x1) / 2
        if h.get("tag"):
            tx, tag_y = h["tag"]
        fa = h["plan"]["enclosed"] + (H.CASA02_UPPER["enclosed"] if not H.is_casita(h["plan"]) else 0)
        svg.text(tx, tag_y, f"{h['id']} · {h['kind'].upper()}", 7, weight=700, ls=0.8)
        svg.text(tx, tag_y, f"{h['beds']} · {fa:,.0f} sf", 6.2, fill=MID, extra='dy="8"')
    svg.dim(0, L, W, L, 3.2 + (12 if lot.get("alley") else 0), size=7.5)
    svg.dim(0, 0, 0, L, -3.2, horizontal=False, size=7.5)
    DR.north_arrow(svg, svg.X(W) - 12, svg.Y(L) + 20, 16)
    return svg_str(svg)


# ---------------------------------------------------------------- sheets
CSS = open(os.path.join(ROOT, "casa01", "signoff", "signoff_v2.py")).read().split('CSS = """')[1].split('"""')[0]
CSS += """
.trip{display:grid;grid-template-columns:repeat(3,1fr);gap:.12in;min-height:0;height:7.7in}
.pp{display:grid;grid-template-rows:auto 1fr auto;min-height:0;gap:4px}
.pp .s{min-height:0;display:flex;align-items:center;justify-content:center}
.pp .s svg{height:100%;width:100%}
.pp h3,.sp h3{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase}
.pp small{font-size:10px;color:#5b625b}
.sp{display:grid;grid-template-columns:auto 1fr;gap:.25in;min-height:0}
.sp .s{height:9.2in;display:flex;align-items:flex-start}
.sp .s svg{height:100%;width:auto}
.kv2{font-size:10.5px;border-collapse:collapse;width:100%}
.kv2 td{border-bottom:1px solid #ebe6da;padding:3px 4px}
.kv2 td.x{color:#a3361f;font-weight:700}
.lead{font-size:12px;line-height:1.45;margin:0}
.leg{display:flex;gap:14px;flex-wrap:wrap;font-size:9.5px;color:#5b625b}
.leg i{display:inline-block;width:12px;height:9px;margin-right:4px;vertical-align:-1px;border:1px solid #bbb}
"""


SC_PLAN, SC_CASITA, SC_SITE = "Plans to scale", "Plan to scale", "Site to scale"


def title_block(sheet, title, scale="As noted"):
    return (f'<aside class="tb"><div class="brand">Brazilian Modern Homes<small>Residential design · Austin</small></div>'
            f'<div class="proj">Phase 2<br>Casa 02 + Casita<small>Concept design</small></div>'
            f'<div class="grow"></div><div class="kv"><span>Sheet title</span><b>{title}</b><span>Scale</span><b>{scale}</b>'
            f'<span>Date / phase</span><b>Nov 2026 · Concept</b></div><div class="sheet">{sheet}</div>'
            f'<div class="warn">Concept design. Not for construction.</div></aside>')


def floor_sheet():
    a = H.area_summary()
    gfc = plan_svg(H.CASA02_GF_CARPORT)
    gfs = plan_svg(H.CASA02_GF_SUITE)
    up = plan_svg(H.CASA02_UPPER, note_front="FRONT")
    notes = [
        f"One house, one upper floor, two ground floors. With the carport: {a['carport_total']:,.0f} sf, 3 bed / 2.5 bath. "
        f"With the bay enclosed as a suite: {a['suite_total']:,.0f} sf, 3 bed + den / 3.5 bath (the upstairs Bed 3 "
        "becomes the den).",
        "20 × 39 ft footprint from the test-fit. Mirror it so the bay and the bedrooms are always on the outside wall; "
        "stairs, closets and baths then line the shared wall of a side-by-side pair.",
        "Facade (direction C): a cobogó screen rises both floors 1 ft in front of the entry and stair, open at the "
        "front door; cedar gates close the carport. It lights up at night like Casa 01's screen.",
        "The Casa 01 staples, once per home: a Lueders limestone ashlar base on the outer side (a corner pier "
        "carries the upper floor), about 50 sf of black calçada at the entries, São Tomé limestone pavers outside.",
        "A gallery hall runs from the front door and the carport door to the kitchen. The open-riser oak stair "
        "rises from the kitchen behind cedar slats to a landing behind the cobogó: the house's signature.",
        "Upstairs side windows are high, or fluted below 5 ft where a bedroom needs an egress window.",
        "Ground floor meets Austin's visitability rules: a half bath, and a no-step entry from the carport or the front.",
        "Glass to the pátio on the back wall. The shared wall of a pair is a 1-hour fire wall with no openings; on "
        "a detached site the suite version takes an 8 ft slider on its outer long wall.",
        "Developed plans with dimensions, door and window schedules: Phase2_Casa02_Plans.pdf (sheets A-101 to A-103).",
    ]
    li = "".join(f"<li>{t}</li>" for t in notes)
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr auto">'
            f'<h1>Casa 02 · concept floor plans</h1>'
            f'<div class="trip"><div class="pp"><h3>Ground floor, carport</h3><div class="s">{gfc}</div>'
            f'<small>{a["carport_gf"]:,.0f} sf inside · carport {210:,.0f} sf (not floor area)</small></div>'
            f'<div class="pp"><h3>Ground floor, suite</h3><div class="s">{gfs}</div>'
            f'<small>{a["suite_gf"]:,.0f} sf inside · the car parks on a pad outside</small></div>'
            f'<div class="pp"><h3>Upper floor, both versions</h3><div class="s">{up}</div>'
            f'<small>{a["upper"]:,.0f} sf · Bed 3 is the den when the suite is downstairs</small></div></div>'
            f'<ul>{li}</ul></div>{title_block("C-1", "Casa 02 plans", SC_PLAN)}</section>')


def casita_sheet():
    cs = plan_svg(H.CASITA, scale=15.0, note_front="FRONT: PATH, STREET OR SIDE STREET")
    notes = [
        "640 sf, one story: living and kitchen across the front, a flex room (desk or guest bed) open to living, "
        "bedroom, bath, laundry and a walk-in closet at the back.",
        "The living room opens to its own pátio through a 10 ft slider on the long wall; mirror the plan to put the "
        "pátio on the other side.",
        "A covered porch, 7'-9\" × 22', runs along the living room and flex room on the pátio side, under a cedar ceiling.",
        "At the street its garden wall is cobogó between limestone piers, with a 4 ft cedar slat gate into the pátio.",
        "Same frames, stucco, cedar and thin roof edge as Casa 01 and Casa 02.",
        "Works with or without its own parking: on a plain 50-ft lot it has none, on corners and wide lots it does.",
        "As a backyard home for an existing house it is the Pátio Casita (tracker P2-18).",
    ]
    li = "".join(f"<li>{t}</li>" for t in notes)
    return (f'<section class="page"><div class="main" style="grid-template-columns:1.1fr 1fr;grid-template-rows:auto 1fr">'
            f'<h1 style="grid-column:1/3">Casita · concept floor plan</h1>'
            f'<div class="pp"><h3>Floor plan</h3><div class="s">{cs}</div><small>640 sf · 1 bed + flex / 1 bath</small></div>'
            f'<div><h2>Notes</h2><ul>{li}</ul></div></div>{title_block("C-2", "Casita plan", SC_CASITA)}'
            f'</section>')


def views_html(s):
    """The site's two massing renders (phase2/render), if they have been made."""
    imgs = []
    for v in ("aerial", "street"):           # rendered in the chosen facade direction (render/build.py --fac)
        f = os.path.join(os.path.dirname(HERE), "render", "out", f"{s['id']}_{v}.png")
        if os.path.exists(f):
            imgs.append(f'<img src="../../render/out/{s["id"]}_{v}.png" style="width:100%;border:1px solid #dcd6c8">')
    if not imgs:
        return ""
    return ('<div><h2>3D massing (low detail)</h2><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'
            + "".join(imgs) + "</div></div>")


def site_sheet(s, i):
    m = check_site(s)
    rows = [("Homes", ", ".join(f"{h['id']}: {h['kind']}" for h in s["homes"]), True),
            ("Floor area", f"{m['fa']:,.0f} of {m['fa_cap']:,.0f} sf", m["fa"] <= m["fa_cap"]),
            ("Footprint", f"{m['bc']:,.0f} of {m['bc_cap']:,.0f} sf", m["bc"] <= m["bc_cap"]),
            ("Impervious", f"{m['ic']:,.0f} of {m['ic_cap']:,.0f} sf ({m['ic_cap'] - m['ic']:,.0f} left)",
             m["ic"] <= m["ic_cap"]),
            ("Front-yard paving", f"{m['fy']:,.0f} of {m['fy_cap']:,.0f} sf", m["fy"] <= m["fy_cap"] + 0.5),
            ("Parking on site", f"{m['parking']} of {m['n']} homes", True),
            ("Carts at the curb", f"{m['carts']} (trash, recycling, compost)", True)]
    tr = "".join(f'<tr><td>{k}</td><td class="{"" if ok else "x"}">{v}</td></tr>' for k, v, ok in rows)
    li = "".join(f"<li>{t}</li>" for t in s["notes"])
    leg = ('<div class="leg"><span><i style="background:#f3f1ea"></i>Garden</span><span><i style="background:#e1ead6"></i>'
           'Pátio</span><span><i style="background:#d8d4ca"></i>Drive, apron, parking</span><span><i style="background:'
           '#e6e0d2"></i>Terrace, walk</span><span><i style="border-color:#8a6a4a;background:#fff"></i>Cedar fence</span>'
           '<span><i style="background:#2b2e31"></i>Pátio wall</span><span><i style="background:#fff;border-color:'
           '#23262a;border-style:dotted"></i>Cobogó screen</span><span><i style="background:#ddd3c2"></i>Lueders '
           'limestone</span><span><i style="background:#363531"></i>Calçada</span></div>')
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr">'
            f'<h1>{s["id"]} · {s["name"]}, {s["lot"]["W"]:.0f} × {s["lot"]["L"]:.0f} ft</h1>'
            f'<div class="sp"><div class="s">{site_svg(s)}</div><div style="display:grid;gap:.18in;align-content:start">'
            f'<div><h2>Checks (2–3 homes on one lot)</h2><table class="kv2">{tr}</table></div>'
            f'<div><h2>How it works</h2><ul>{li}</ul></div>{leg}{views_html(s)}'
            f'<p class="lead" style="font-size:10px;color:#5b625b">Ground-floor plans shown. Dashed outline over a '
            f'carport: the upper floor above it; beside a Casita: its porch roof. Paved terraces and walks are counted in the impervious total; '
            f'stepping stones set in planting are not.</p></div></div></div>'
            f'{title_block(f"C-{i}", "Site plan concept", SC_SITE)}</section>')


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = [floor_sheet(), casita_sheet()]
    for i, fn in enumerate(SITES):
        s = fn()
        pages.append(site_sheet(s, i + 3))
        m = check_site(s)
        print(s["id"], {k: round(v) if isinstance(v, float) else v for k, v in m.items()})
    for name, plan in (("casa02_gf_carport", H.CASA02_GF_CARPORT), ("casa02_gf_suite", H.CASA02_GF_SUITE),
                       ("casa02_upper", H.CASA02_UPPER), ("casita", H.CASITA)):
        open(os.path.join(OUT, f"{name}.svg"), "w").write(plan_svg(plan))
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Phase 2 concepts</title>'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(os.path.join(OUT, "concepts.html"), "w").write(html)
    print("wrote", os.path.join(OUT, "concepts.html"))


if __name__ == "__main__":
    main()
