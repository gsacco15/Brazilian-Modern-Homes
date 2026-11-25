"""Phase 2 model: where each home sits on each lot.

One source of truth for every output (concept sheets, AutoCAD, Blender).
IDs: a site uses its test-fit layout ID (L1-D1, L1-T1, ...); a home uses A, B, C on its lot.
Plans (homes.py): CASA02_GF_CARPORT, CASA02_GF_SUITE, CASA02_UPPER, CASITA.

A transform T places a home plan on a lot: mirror (left-right), then rotate 0/90/180/270 deg
counter-clockwise, then move by (dx, dy). Lot coordinates: x east from the west lot line, y north
from the street lot line, in feet.
"""
import math

from . import homes as H


HOME_RULES = dict(front=15.0, side=5.0, rear=5.0, bc=0.40, ic=0.45, fy=0.40,
                  far2=(0.55, 3200.0), far3=(0.65, 4350.0))



# ---------------------------------------------------------------- transforms
def T(plan, dx=0.0, dy=0.0, mirror=False, rot=0):
    return dict(W=plan["W"], D=plan["D"], dx=dx, dy=dy, mirror=mirror, rot=rot)


def tp(t, x, y):
    if t is None:
        return x, y
    W, Dd = t["W"], t["D"]
    if t["mirror"]:
        x = W - x
    r = t["rot"]
    if r == 90:
        x, y = Dd - y, x
    elif r == 180:
        x, y = W - x, Dd - y
    elif r == 270:
        x, y = y, W - x
    return x + t["dx"], y + t["dy"]


def footprint(t):
    w, d = (t["W"], t["D"]) if t["rot"] in (0, 180) else (t["D"], t["W"])
    return (t["dx"], t["dy"], t["dx"] + w, t["dy"] + d)


def tpoly(t, pts):
    return [tp(t, x, y) for x, y in pts]


def rect_pts(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def ellipse_pts(cx, cy, rx, ry, n=18):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


SITES = []


def site(fn):
    SITES.append(fn)
    return fn


@site
def s1_duo_side():
    W, L = 50.0, 125.0
    gf = H.CASA02_GF_CARPORT
    homes = [dict(id="A", plan=gf, t=T(gf, 5, 15), park=True, kind="Casa 02", beds="3 bed / 2.5 bath"),
             dict(id="B", plan=gf, t=T(gf, 25, 15, mirror=True), park=True, kind="Casa 02", beds="3 bed / 2.5 bath")]
    return dict(id="L1-D1", name="Duo, side by side", lot=dict(W=W, L=L), homes=homes,
                patios=[(5, 54, 25, 78), (25, 54, 45, 78)],
                pave=[("Apron", (5.25, 0, 15.25, 15)), ("Apron", (34.75, 0, 44.75, 15)),
                      ("Terrace", (7, 54, 23, 62)), ("Terrace", (27, 54, 43, 62))],
                paths=[[(18.0, 0.5), (18.0, 14.5)], [(32.0, 0.5), (32.0, 14.5)]],
                address_walls=[(19.2, 1.0, 19.87, 7.0), (30.13, 1.0, 30.8, 7.0)],
                walls=[[(25, 54), (25, 120)]], trees=[(12, 72, 11), (38, 72, 11), (14, 104, 13), (38, 108, 12)],
                fence=[[(0, 15), (0, 125), (50, 125), (50, 15)]],
                notes=["Bays on the outside, so every bedroom has an outside wall and stairs, closets and the "
                       "carports buffer the shared wall.",
                       "Two 10-ft curb cuts at the outer edges use exactly the 40% front-yard limit. If the city allows "
                       "only one, use the small-lot split or a front-and-back duo instead.",
                       "Front walks are stepping stones in planting, and carts live in each carport: the front "
                       "yard has no paving to spare. The step-free route is up the apron to the side door.",
                       "Cedar gates close both carports from the street, as at Casa 01."])


@site
def s2_trio_onfoot():
    W, L = 50.0, 125.0
    gf, cs = H.CASA02_GF_CARPORT, H.CASITA
    homes = [dict(id="A", plan=gf, t=T(gf, 5, 15), park=True, kind="Casa 02", beds="3 bed / 2.5 bath"),
             dict(id="B", plan=gf, t=T(gf, 25, 15, mirror=True), park=True, kind="Casa 02", beds="3 bed / 2.5 bath"),
             dict(id="C", plan=cs, t=T(cs, 5, 88), park=False, kind="Casita", beds="1 bed + flex", tag=(37, 93.5))]
    return dict(id="L1-T1", name="Trio, Casita on foot", lot=dict(W=W, L=L), homes=homes,
                patios=[(5, 54, 25, 74), (25, 54, 45, 74), (25, 88, 45, 120)],
                pave=[("Apron", (5.25, 0, 15.25, 15)), ("Apron", (34.75, 0, 44.75, 15)),
                      ("Terrace", (8, 54, 16, 60)), ("Terrace", (34, 54, 42, 60)), ("Terrace", (25, 92, 31, 100))],
                paths=[[(2.5, 2), (2.5, 84), (20, 84), (20, 87.5)], [(18.0, 0.5), (18.0, 14.5)], [(32.0, 0.5), (32.0, 14.5)]],
                address_walls=[(19.2, 1.0, 19.87, 7.0), (30.13, 1.0, 30.8, 7.0)],
                walls=[[(25, 54), (25, 74)], [(25, 84), (25, 88)], [(5, 74), (45, 74)]],
                trees=[(12, 68, 10), (38, 68, 10), (37, 108, 11), (12, 81, 7)],
                fence=[[(0, 15), (0, 125), (50, 125), (50, 15)]],
                notes=["The Casita has no parking: no paving is left for it on a 50-ft lot (impervious cap).",
                       "Its path runs along the west side yard as stepping stones in planting, which add no paving.",
                       "Fire access: about 143 ft from the street to the Casita's far corner, inside the 150-ft reach.",
                       "Paved terraces stay small (about 50 sf per home); the rest of each pátio is planted.",
                       "Front walks are stepping stones and carts live in the carports and side yard: the front yard "
                       "is at its paving limit. Nine carts go to the curb on pickup day."])


@site
def s3_alley_trio():
    W, L = 50.0, 125.0
    gf, cs = H.CASA02_GF_CARPORT, H.CASITA
    homes = [dict(id="C", plan=cs, t=T(cs, 5, 15), park=False, kind="Casita", beds="1 bed + flex"),
             dict(id="A", plan=gf, t=T(gf, 5, 81, mirror=True, rot=180), park=True, kind="Casa 02",
                  beds="3 bed / 2.5 bath"),
             dict(id="B", plan=gf, t=T(gf, 25, 81, rot=180), park=True, kind="Casa 02", beds="3 bed / 2.5 bath")]
    return dict(id="L2-T2", name="Trio, Casita at the street, pair on the alley", lot=dict(W=W, L=L, alley=True),
                homes=homes, patios=[(25, 15, 45, 47), (5, 61, 25, 81), (25, 61, 45, 81)],
                pave=[("Apron", (5.25, 120, 15.25, 125)), ("Apron", (34.75, 120, 44.75, 125)),
                      ("Walk", (18.75, 0, 21.25, 15)), ("Terrace", (25, 21, 31, 31)),
                      ("Terrace", (8, 75, 22, 81)), ("Terrace", (28, 75, 42, 81)), ("Carts", (27, 9, 37.5, 12.5))],
                paths=[[(2.5, 2), (2.5, 56), (15, 56), (15, 61)], [(2.5, 56), (35, 56), (35, 61)]],
                walls=[[(25, 61), (25, 81)], [(5, 51), (45, 51)]],
                street_wall=[(25, 15), (45, 15)], garden_gate=(25.0, 29.0), garden_stone=6.75,
                calcada=[(25.4, 15.4, 29.0, 19.4)],              # calçada landing inside the garden gate
                trees=[(38, 34, 9), (12, 70, 9), (38, 70, 9)],
                fence=[[(0, 15), (0, 125)], [(50, 125), (50, 15)]],
                notes=["The street sees a one-story Casita behind its walled garden; the two-story pair sits back.",
                       "The pair parks off the alley with no curb cut on the street; guests enter through the garden.",
                       "The Casita parks on the street. Its garden wall is cobogó between limestone piers, with a "
                       "4 ft cedar gate into its pátio.",
                       "Fire access from the street is about 140 ft to the pair's far corners; confirm whether the "
                       "alley counts as fire access."])


@site
def s4_corner_trio():
    W, L = 60.0, 125.0
    gf, cs = H.CASA02_GF_CARPORT, H.CASITA
    homes = [dict(id="A", plan=gf, t=T(gf, 5, 15), park=True, kind="Casa 02", beds="3 bed / 2.5 bath"),
             dict(id="B", plan=gf, t=T(gf, 25, 15, mirror=True), park=True, kind="Casa 02", beds="3 bed / 2.5 bath"),
             dict(id="C", plan=cs, t=T(cs, 23, 100, mirror=True, rot=90), park=True, kind="Casita", beds="1 bed + flex")]
    return dict(id="L3-T1", name="Trio on a corner, Casita facing the side street",
                lot=dict(W=W, L=L, corner=True), homes=homes,
                patios=[(5, 54, 25, 74), (25, 54, 45, 74), (23, 88, 55, 100)],
                pave=[("Apron", (5.25, 0, 15.25, 15)), ("Apron", (34.75, 0, 44.75, 15)),
                      ("Parking", (40, 76, 60, 86)), ("Walk", (55, 113.5, 60, 116)),
                      ("Terrace", (8, 54, 18, 61)), ("Terrace", (32, 54, 42, 61)), ("Terrace", (42, 92, 52, 100))],
                paths=[[(18.0, 0.5), (18.0, 14.5)], [(32.0, 0.5), (32.0, 14.5)]],
                address_walls=[(19.2, 1.0, 19.87, 7.0), (30.13, 1.0, 30.8, 7.0)],
                walls=[[(25, 54), (25, 74)], [(5, 74), (40, 74)]],
                trees=[(12, 68, 10), (38, 68, 10), (32, 94, 7), (12, 100, 10)],
                fence=[[(0, 15), (0, 125), (55, 125)]],
                notes=["The Casita's door and parking face the side street, so the main street sees only the pair.",
                       "Every home parks on site; the Casita's pad sits between the gardens, off the side street.",
                       "A second street frontage means a second curb cut on its own street.",
                       "Front walks are stepping stones in planting: two aprons already use the front-yard paving limit."])


@site
def s5_wide_duo():
    W, L = 65.0, 125.0
    gs = H.CASA02_GF_SUITE
    homes = [dict(id="A", plan=gs, t=T(gs, 22, 15), park=True, kind="Casa 02 with suite",
                  beds="3 bed + den / 3.5 bath"),
             dict(id="B", plan=gs, t=T(gs, 22, 74), park=True, kind="Casa 02 with suite",
                  beds="3 bed + den / 3.5 bath")]
    return dict(id="L4-D2", name="Duo front and back, ground-floor suites", lot=dict(W=W, L=L), homes=homes,
                patios=[(42, 15, 60, 54), (42, 74, 60, 113)],
                pave=[("Drive", (0, 0, 12, 99)), ("Parking", (12, 20, 22, 40)), ("Parking", (12, 79, 22, 99)),
                      ("Walk", (33.75, 0, 36.25, 15)), ("Walk", (12, 64, 34, 66.5)),
                      ("Terrace", (42, 44, 52, 54)), ("Terrace", (42, 103, 52, 113)), ("Carts", (39, 9, 49, 12.5))],
                address_walls=[(36.6, 1.0, 37.27, 7.0)],
                walls=[[(42, 64), (60, 64)]],
                trees=[(53, 30, 10), (53, 86, 10), (32, 118, 9)],
                fence=[[(0, 15), (0, 125), (65, 125), (65, 15)]],
                notes=["With paving to spare, each home parks on a pad beside the shared drive and its flex bay "
                       "becomes a ground-floor bedroom suite (1,560 sf).",
                       "One curb cut serves both homes; the drive stops at the back home's parking.",
                       "Both pátios face east off the two-story block, shaded in the afternoon."])


@site
def s6_side_drive_trio():
    """P2-23: two side-drive Casa 02s in a row on a shared drive, and the Casita at the back (test-fit L4-T1)."""
    W, L = 65.0, 125.0
    gd, cs = H.CASA02_GF_SIDE, H.CASITA_NP
    homes = [dict(id="A", plan=gd, t=T(gd, 12, 15), park=True, kind="Casa 02, side drive", beds="3 bed / 2.5 bath"),
             dict(id="B", plan=gd, t=T(gd, 12, 59), park=True, kind="Casa 02, side drive", beds="3 bed / 2.5 bath"),
             dict(id="C", plan=cs, t=T(cs, 37, 88, mirror=True), park=True, kind="Casita", beds="1 bed + flex",
                  tag=(47, 85.3))]
    return dict(id="L4-T1", name="Trio on a shared drive, side-drive carports", lot=dict(W=W, L=L), homes=homes,
                patios=[(32, 15, 60, 54), (32, 59, 60, 83), (12, 103, 37, 120)],
                pave=[("Drive", (0, 0, 12, 92)), ("Terrace", (34, 30, 42, 40)), ("Terrace", (34, 70, 42, 80)),
                      ("Terrace", (25, 105, 33, 113)), ("Carts", (52, 9, 62, 12.5))],
                paths=[[(6, 93), (6, 101), (34, 101)]],                  # straight from the drive to the Casita door
                walls=[[(32, 54), (60, 54)]],
                # cobogó privacy screens, 7 ft: across A's pátio at the front setback line (a cedar garden gate by
                # the house, a limestone pier at the lot line), and between B's pátio and the Casita's court
                screens=[dict(y=15.0, x0=32.0, x1=65.0, gate=(32.25, 35.75), stone=2.0, h=7.0),
                         dict(y=83.0, x0=32.0, x1=65.0, gate=None, stone=2.0, h=7.0)],
                drive_walk=(8.5, 0.0, 12.0, 92.0),                       # limestone walk along the drive, recessed lights
                trees=[(50, 34, 10), (50, 72, 9), (20, 112, 8)],
                fence=[[(0, 15), (0, 125), (65, 125), (65, 15)]],
                address_walls=[(12.3, 1.0, 12.97, 7.0)],
                notes=["One 12 ft drive along the west line serves all three homes; one curb cut.",
                       "Each Casa 02 parks across its front, entering from the drive (side-drive ground floor, "
                       "P2-23). The street sees a full limestone wall with the cobogó above.",
                       "Visitors walk up a lit limestone walk along the drive to each front door: the Casa 02 doors "
                       "open off the drive under cedar canopies, and the Casita's faces the end of its path.",
                       "Cobogó screens close A's pátio from the street (a cedar garden gate by the house) and part "
                       "B's pátio from the Casita's court.",
                       "Living rooms open east to their own pátios; the back walls get high windows.",
                       "The Casita parks at the end of the drive and walks behind B. Its porch would sit in the side "
                       "setback here, so this one has none.",
                       "Fire access to the Casita is about 150 ft from the street: confirm with the fire marshal."])


def porch_rect(h):
    """The roofed porch of a home on the lot (x0, y0, x1, y1), or None."""
    p = h["plan"].get("porch")
    if not p:
        return None
    pts = tpoly(h["t"], rect_pts(p["rect"]))
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def garden_wall(s):
    """The Casita's wall at the street. Returns dict(y, piers=[(x0, x1)] of stone, posts=[(x0, x1)] of bronze,
    gate=(x0, x1) or None, cobogo=(x0, x1)), or None.
    With garden_stone (Nov 24): three parts, open, filtered, solid: the cedar gate next to the house on slim bronze
    posts, the cobogó, and a solid limestone wall at the outer end, all 8 ft high. Without it (the facade study):
    limestone piers at the ends, a gate and cobogó between."""
    sw = s.get("street_wall")
    if not sw:
        return None
    (x0, y), (x1, _y) = sw
    g = s.get("garden_gate")
    st = s.get("garden_stone")
    if st and g:
        return dict(y=y, piers=[(x1 - st, x1)], posts=[(g[0], g[0] + 0.25), (g[1], g[1] + 0.25)],
                    gate=(g[0] + 0.25, g[1]), cobogo=(g[1] + 0.25, x1 - st))
    piers = [(x0, x0 + 2.0)] + ([(g[1], g[1] + 1.0)] if g else []) + [(x1 - 2.0, x1)]
    return dict(y=y, piers=piers, posts=[], gate=g, cobogo=((g[1] + 1.0) if g else x0 + 2.0, x1 - 2.0))


def screen_parts(sc):
    """A cobogó privacy screen (sites' "screens") as the garden wall's parts: a cedar gate by the house on bronze
    posts, cobogó, and a limestone pier at the outer end. Same keys as garden_wall()."""
    x0, x1, st, g = sc["x0"], sc["x1"], sc["stone"], sc.get("gate")
    return dict(y=sc["y"], h=sc.get("h", 7.0), piers=[(x1 - st, x1)],
                posts=[(g[0], g[0] + 0.25), (g[1], g[1] + 0.25)] if g else [],
                gate=(g[0] + 0.25, g[1]) if g else None, cobogo=((g[1] + 0.25) if g else x0, x1 - st))


def walk_lights(s, step=8.0, clear=1.0):
    """Recessed lights for the drive walk: flush in-ground, drive-over rated, spaced along the stretches between the
    carport openings and the front-door canopies so nothing sits where a car turns in or a door opens.
    Returns [(x, y)] in site feet, down the middle of the walk."""
    dw = s.get("drive_walk")
    if not dw:
        return []
    blocks = []
    for h in s["homes"]:
        p, t = h["plan"], h["t"]
        spans = []
        if p.get("gate"):
            spans.append(p["gate"])
        if p.get("canopy"):
            r = p["canopy"]["rect"]
            spans.append(((r[0], r[1]), (r[2], r[3])))
        for (ax, ay), (bx, by) in spans:
            ys = (tp(t, ax, ay)[1], tp(t, bx, by)[1])
            blocks.append((min(ys) - clear, max(ys) + clear))
    blocks.sort()
    segs, cur = [], dw[1] + 1.5
    for b0, b1 in blocks:
        if b0 > cur:
            segs.append((cur, b0))
        cur = max(cur, b1)
    segs.append((cur, dw[3] - 1.5))
    x = (dw[0] + dw[2]) / 2
    pts = []
    for a, b in segs:
        if b - a < 2.5:
            continue
        n = max(1, round((b - a) / step))
        pts += [(x, a + (k + 0.5) * (b - a) / n) for k in range(n)]
    return pts


def calcada_rects(s):
    """Every calçada mosaic on the lot (x0, y0, x1, y1): the homes' (from their plans) and the site's own."""
    out = list(s.get("calcada", []))
    for h in s["homes"]:
        for r in h["plan"].get("calcada", []):
            pts = tpoly(h["t"], rect_pts(r))
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def _overlap(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def check_site(s):
    W, L = s["lot"]["W"], s["lot"]["L"]
    A = W * L
    n = len(s["homes"])
    bc = sum((footprint(h["t"])[2] - footprint(h["t"])[0]) * (footprint(h["t"])[3] - footprint(h["t"])[1])
             for h in s["homes"])
    porches = [r for r in (porch_rect(h) for h in s["homes"]) if r]
    bc += sum((r[2] - r[0]) * (r[3] - r[1]) for r in porches)          # a roofed porch counts as footprint
    pave = 0.0
    for _k, r in s["pave"]:
        x0, y0, x1, y1 = max(r[0], 0), max(r[1], 0), min(r[2], W), min(r[3], L)
        pave += max(0, x1 - x0) * max(0, y1 - y0)
        pave -= sum(_overlap((x0, y0, x1, y1), p) for p in porches)       # paving under a porch roof counts once
    pave += sum((r[2] - r[0]) * (r[3] - r[1]) for r in s.get("address_walls", []))   # low stone walls
    for sc in s.get("screens", []):                                                  # cobogó screens and piers
        pave += (sc["x1"] - sc["x0"] - sc["stone"]) * 0.33 + sc["stone"] * 1.0
    roofed = porches + [footprint(h["t"]) for h in s["homes"]]
    for r in calcada_rects(s):                                            # mosaic outside the roofs is paving
        a = (r[2] - r[0]) * (r[3] - r[1])
        pave += max(0.0, a - sum(_overlap(r, q) for q in roofed))
    fy = 0.0
    for k, r in s["pave"]:
        x0, y0, x1, y1 = max(r[0], 0), max(r[1], 0), min(r[2], W), min(r[3], HOME_RULES["front"])
        fy += max(0, x1 - x0) * max(0, y1 - y0)
    fa = sum(h["plan"]["enclosed"] + (H.CASA02_UPPER["enclosed"] if not H.is_casita(h["plan"]) else 0)
             for h in s["homes"])
    far = HOME_RULES["far2"] if n == 2 else HOME_RULES["far3"]
    return dict(fa=fa, fa_cap=max(far[0] * A, far[1]), bc=bc, bc_cap=HOME_RULES["bc"] * A, ic=bc + pave,
                ic_cap=HOME_RULES["ic"] * A, fy=fy, fy_cap=HOME_RULES["fy"] * W * HOME_RULES["front"],
                parking=sum(1 for h in s["homes"] if h["park"]), n=n, carts=3 * n)
