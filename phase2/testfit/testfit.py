"""Phase 2 test-fit study: duo and trio layouts on six standard Austin lots.

    python3 phase2/testfit/testfit.py            -> phase2/testfit/out/ (plans, results.json, testfit.html)
    node casa01/signoff/print_pdf.js phase2/testfit/out/testfit.html phase2/testfit/Phase2_TestFit.pdf

Plain boxes, not floor plans. Every layout is built from a few numbers (lot size, home sizes) and checked
against the HOME rules for 2-3 homes on one lot (or the small-lot rules for a split): setbacks, building
coverage, impervious cover, the front-yard paving limit, floor-area caps (inside the McMansion boundary),
parking, pátio orientation and the gap between buildings. For each layout we also search for the deepest
Casa 02 that still passes, which sets the design target for its floor plan.

Coordinates are feet. x runs east from the west lot line, y runs north from the street (front) lot line.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.join(ROOT, "casa01"))
import design as D  # noqa: E402  (Casa 01, for the Casa 01 + Casita option)

# ---------------------------------------------------------------- rules (HOME Phase 1 and 2; see the Phase 2 study)
HOME_RULES = dict(front=15.0, side=5.0, street_side=5.0, rear=5.0, bc=0.40, ic=0.45, front_yard_ic=0.40,
                  far2=(0.55, 3200.0), far3=(0.65, 4350.0), unit=(0.40, 2300.0))
# small lots (HOME Phase 2): only the lot size and width are confirmed; setbacks and coverage are assumptions
SMALL_RULES = dict(front=15.0, side=5.0, inner=0.0, rear=10.0, bc=0.40, ic=0.45, front_yard_ic=0.40,
                   min_area=1800.0, min_width=15.0)
TERRACE_PER_HOME = 100.0   # paving each home needs beyond drives: a terrace and walks (sf)

# ---------------------------------------------------------------- the homes (massing only)
C2_W = 20.0                # Casa 02 width (decided: 20 ft)
C2_D = 40.0                # baseline depth; the study searches 28-50 ft
BAY = 200.0                # open carport bay under the upper floor (one car), not floor area
CS_W, CS_D = 20.0, 32.0    # Casita, single story


def c2_area(d, w=C2_W):
    return 2 * w * d - BAY


LOTS = [
    dict(id="L1", name="Standard interior lot, no alley", W=50.0, L=125.0),
    dict(id="L2", name="Standard lot with a rear alley", W=50.0, L=125.0, alley=True),
    dict(id="L3", name="Corner lot", W=60.0, L=125.0, corner=True),
    dict(id="L4", name="Wide interior lot", W=65.0, L=125.0),
    dict(id="L5", name="Deep interior lot", W=50.0, L=175.0),
    dict(id="L6", name="Small-lot split of a 50 ft lot", W=50.0, L=125.0, small=True),
]
LOT = {l["id"]: l for l in LOTS}


# ---------------------------------------------------------------- geometry helpers
def area(r):
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def clip(r, c):
    return (max(r[0], c[0]), max(r[1], c[1]), min(r[2], c[2]), min(r[3], c[3]))


def gap(a, b):
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def c2(x0, y0, label, d, rot=False, bay="sw"):
    """Casa 02 box. rot=True turns it to face east or west (depth runs along x)."""
    w, h = (d, C2_W) if rot else (C2_W, d)
    r = (x0, y0, x0 + w, y0 + h)
    bw, bh = (20.0, 10.0) if not rot else (10.0, 20.0)
    if bay == "sw":
        b = (r[0], r[1], r[0] + bw, r[1] + bh) if not rot else (r[0], r[1], r[0] + 20.0, r[1] + 10.0)
    elif bay == "s-half-w":
        b = (r[0], r[1], r[0] + 10.0, r[1] + 20.0)
    elif bay == "s-half-e":
        b = (r[2] - 10.0, r[1], r[2], r[1] + 20.0)
    elif bay == "n-half-w":
        b = (r[0], r[3] - 20.0, r[0] + 10.0, r[3])
    elif bay == "n-half-e":
        b = (r[2] - 10.0, r[3] - 20.0, r[2], r[3])
    elif bay == "e":
        b = (r[2] - 20.0, r[1], r[2], r[1] + 10.0)
    else:
        b = None
    return dict(kind="C2", label=label, rect=r, fa=c2_area(d), stories=2, park=b is not None, bay=b)


def casita(x0, y0, label="Casita", park=False, rot=False):
    w, h = (CS_D, CS_W) if rot else (CS_W, CS_D)
    return dict(kind="CS", label=label, rect=(x0, y0, x0 + w, y0 + h), fa=CS_W * CS_D, stories=1, park=park, bay=None)


def opt(oid, lot, name, homes, patios, pave=(), paths=(), notes=(), sublots=None, extra_ic=0.0, extra_bc=None):
    return dict(id=oid, lot=lot, name=name, homes=list(homes), patios=list(patios), pave=list(pave),
                paths=list(paths), notes=list(notes), sublots=sublots, extra_ic=extra_ic)


# ---------------------------------------------------------------- layouts (each a function of the Casa 02 depth d)
def l1_duo_side(d, lot="L1"):
    l = LOT[lot]
    f = HOME_RULES["front"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    py = min(f + d + 24, l["L"] - HOME_RULES["rear"])
    return opt(f"{lot}-D1", lot, "Duo, side by side", [a, b],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f))],
               notes=["Townhouses with one shared rated wall.", "Each parks in its bay under the upper floor."])


def l1_duo_frontback(d, lot="L1"):
    l = LOT[lot]
    f, g = HOME_RULES["front"], 20.0
    a = c2(13, f, "A", d)
    b = c2(13, f + d + g, "B", d)
    return opt(f"{lot}-D2", lot, "Duo, front and back on a side drive", [a, b],
               [(0, (33, f, l["W"], f + d)), (1, (33, b["rect"][1], l["W"], b["rect"][3]))],
               pave=[("drive", (0, 0, 12, b["rect"][1] + 10))],
               notes=["12 ft drive along the west line to both carports.", "Each pátio east of its home."])


def l1_trio_onfoot(d, lot="L1"):
    l = LOT[lot]
    f, r = HOME_RULES["front"], HOME_RULES["rear"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    cy = l["L"] - r - CS_D
    cs = casita(5, cy)
    py = min(f + d + 20, cy - 4)
    return opt(f"{lot}-T1", lot, "Trio, two at the street, Casita on foot", [a, b, cs],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py)), (2, (25, cy, 45, cy + CS_D))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f))],
               paths=[[(2.5, 0), (2.5, cy + 6), (5, cy + 6)]],
               notes=["The Casita has no on-site parking (legal: no minimums).",
                      "Its path along the side yard is stepping stones in planting."])


def l1_trio_frontback(d, lot="L1"):
    l = LOT[lot]
    f, g = HOME_RULES["front"], 10.0
    a = c2(13, f, "A", d)
    b = c2(13, f + d + g, "B", d)
    cy = b["rect"][3] + g
    cs = casita(13, cy, park=True)
    return opt(f"{lot}-T2", lot, "Trio, front to back on a shared drive", [a, b, cs],
               [(0, (33, f, l["W"], f + d)), (1, (33, b["rect"][1], l["W"], b["rect"][3])),
                (2, (33, cy, l["W"], cy + CS_D))],
               pave=[("drive", (0, 0, 12, cy + 20))],
               notes=["Drive to every home; the Casita parks beside it."])


def l2_duo_alley(d, lot="L2"):
    l = LOT[lot]
    r = HOME_RULES["rear"]
    y0 = l["L"] - r - d
    a = c2(5, y0, "A", d, bay="n-half-w")
    b = c2(25, y0, "B", d, bay="n-half-e")
    return opt(f"{lot}-D1", lot, "Duo on the alley, walled gardens to the street", [a, b],
               [(0, (5, y0 - 24, 25, y0)), (1, (25, y0 - 24, 45, y0))],
               pave=[("apron", (5, l["L"] - r, 15, l["L"])), ("apron", (35, l["L"] - r, 45, l["L"]))],
               paths=[[(15, 0), (15, y0 - 24)], [(35, 0), (35, y0 - 24)]],
               notes=["Cars come from the alley; no curb cuts on the street.",
                      "Each home's garden faces the street behind a wall."])


def l2_trio_street(d, lot="L2"):
    l = LOT[lot]
    f, r = HOME_RULES["front"], HOME_RULES["rear"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    cy = l["L"] - r - CS_D
    cs = casita(5, cy, park=True)
    py = min(f + d + 20, cy - 4)
    return opt(f"{lot}-T1", lot, "Trio, two at the street, Casita on the alley", [a, b, cs],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py)), (2, (25, cy, 35, cy + CS_D))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f)), ("pad", (35, l["L"] - 20, 45, l["L"]))],
               notes=["The Casita parks on a pad off the alley."])


def l2_trio_casita_front(d, lot="L2"):
    l = LOT[lot]
    f, r = HOME_RULES["front"], HOME_RULES["rear"]
    cs = casita(5, f)
    y0 = l["L"] - r - d
    a = c2(5, y0, "A", d, bay="n-half-w")
    b = c2(25, y0, "B", d, bay="n-half-e")
    return opt(f"{lot}-T2", lot, "Trio, Casita at the street, pair on the alley", [cs, a, b],
               [(0, (25, f, 45, f + CS_D)), (1, (5, max(f + CS_D + 4, y0 - 20), 25, y0)),
                (2, (25, max(f + CS_D + 4, y0 - 20), 45, y0))],
               pave=[("apron", (5, l["L"] - r, 15, l["L"])), ("apron", (35, l["L"] - r, 45, l["L"]))],
               paths=[[(2.5, 0), (2.5, y0 - 6)]],
               notes=["The street sees a one-story Casita; the two-story pair sits back.",
                      "Pair parks off the alley; the Casita on the street."])


def l3_duo(d, lot="L3"):
    l = LOT[lot]
    f, r, ss = HOME_RULES["front"], HOME_RULES["rear"], HOME_RULES["street_side"]
    a = c2(5, f, "A", d, bay="s-half-w")
    bx = l["W"] - ss - d
    b = c2(bx, l["L"] - r - C2_W, "B", d, rot=True, bay="e")
    return opt(f"{lot}-D1", lot, "Duo, one home facing each street", [a, b],
               [(0, (25, f, 45, f + d)), (1, (bx, b["rect"][1] - 22, l["W"] - ss, b["rect"][1]))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (l["W"] - ss, b["rect"][1], l["W"], b["rect"][1] + 10))],
               notes=["B faces the side street and parks off it."])


def l3_trio(d, lot="L3"):
    l = LOT[lot]
    f, r, ss = HOME_RULES["front"], HOME_RULES["rear"], HOME_RULES["street_side"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    cx = l["W"] - ss - CS_D
    cs = casita(cx, l["L"] - r - CS_W, park=True, rot=True)
    py = f + d + 20
    pad_y = cs["rect"][1] - 12
    return opt(f"{lot}-T1", lot, "Trio, Casita facing the side street", [a, b, cs],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py)), (2, (cx, py + 2, l["W"] - 22, cs["rect"][1]))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f)), ("pad", (l["W"] - 20, pad_y - 10, l["W"], pad_y))],
               notes=["The Casita faces the side street and parks off it."])


def l3_trio3(d, lot="L3"):
    l = LOT[lot]
    f, r, ss = HOME_RULES["front"], HOME_RULES["rear"], HOME_RULES["street_side"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    cx = l["W"] - ss - d
    c = c2(cx, l["L"] - r - C2_W, "C", d, rot=True, bay="e")
    py = f + d + 20
    return opt(f"{lot}-T2", lot, "Trio, three Casa 02", [a, b, c],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py)), (2, (cx, py + 2, l["W"] - ss, c["rect"][1]))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f)),
                     ("apron", (l["W"] - ss, c["rect"][1], l["W"], c["rect"][1] + 10))],
               notes=["C faces the side street and parks off it."])


def casa01_footprint(shift):
    roof = [(x, y - shift) for x, y in D.ROOF]
    walls = [(x, y - shift) for x, y in D.FOOTPRINT]
    return roof, walls


def l4_casa01_casita(d, lot="L4"):
    l = LOT[lot]
    shift = 30.0 - HOME_RULES["front"]          # Casa 01 walls start 30 ft back; HOME allows 15
    roof, walls = casa01_footprint(shift)
    xs, ys = [p[0] for p in walls], [p[1] for p in walls]
    home = dict(kind="C01", label="Casa 01", rect=(min(xs), min(ys), max(xs), max(ys)), fa=1670.0, stories=1,
                park=True, bay=None, poly=roof, bc=poly_area(roof))
    cy = l["L"] - HOME_RULES["rear"] - CS_D
    cs = casita(38, cy)
    terr = sum(area(p["rect"]) for p in D.PAVING if p["name"] in ("Great room terrace", "Courtyard ell terrace"))
    strips = sum((b - a) for a, b in D.DRIVEWAY["strips"]) * (D.CARPORT["y0"] - shift)
    steps = 27.0
    return opt(f"{lot}-D1", lot, "Duo, Casa 01 + Casita", [home, cs],
               [(1, (12, cy, 38, cy + CS_D))],
               pave=[("strips", (50.5, 0, 57.5, D.CARPORT["y0"] - shift))],
               paths=[[(2.5, 0), (2.5, cy + 6), (12, cy + 6)]],
               notes=["Casa 01 as designed, moved up to the 15 ft setback.",
                      "Its roof (2,996 sf) counts as building coverage."],
               extra_ic=terr + steps + strips - area((50.5, 0, 57.5, D.CARPORT["y0"] - shift)))


def l4_duo_frontback(d, lot="L4"):
    o = l1_duo_frontback(d, lot)
    o["id"] = f"{lot}-D2"
    return o


def l4_trio_drive(d, lot="L4"):
    l = LOT[lot]
    f, r = HOME_RULES["front"], HOME_RULES["rear"]
    a = c2(12, f, "A", d)
    b = c2(12, f + d + 5, "B", d)
    cy = l["L"] - r - CS_D
    cs = casita(37, cy, park=True)
    end = b["rect"][1] + 20          # past B's carport, plus one spot for the Casita
    return opt(f"{lot}-T1", lot, "Trio, shared drive stops at the middle home", [a, b, cs],
               [(0, (32, f, 60, f + d)), (1, (32, b["rect"][1], 60, min(b["rect"][3], cy - 6))),
                (2, (12, b["rect"][3], 37, l["L"] - r))],
               pave=[("drive", (0, 0, 12, end))],
               notes=["The Casita parks at the end of the drive, beside B, and walks about 30 ft."])


def l4_trio_row(d, lot="L4"):
    l = LOT[lot]
    f = HOME_RULES["front"]
    homes = [c2(5 + i * C2_W, f, "ABC"[i], d, bay="s-half-w") for i in range(3)]
    py = f + d + 24
    return opt(f"{lot}-T2", lot, "Trio, three in a row", homes,
               [(i, (5 + i * C2_W, f + d, 5 + (i + 1) * C2_W, py)) for i in range(3)],
               pave=[("apron", (5 + i * C2_W, 0, 15 + i * C2_W, f)) for i in range(3)],
               notes=["Three townhouses side by side."])


def l5_duo(d, lot="L5"):
    o = l1_duo_frontback(d, lot)
    o["id"] = f"{lot}-D1"
    return o


def l5_trio_onfoot(d, lot="L5"):
    l = LOT[lot]
    f, g, r = HOME_RULES["front"], 20.0, HOME_RULES["rear"]
    a = c2(13, f, "A", d)
    b = c2(13, f + d + g, "B", d)
    cy = l["L"] - r - CS_D
    cs = casita(13, cy, park=True)
    return opt(f"{lot}-T1", lot, "Trio, drive stops at the middle home", [a, b, cs],
               [(0, (33, f, l["W"], f + d)), (1, (33, b["rect"][1], l["W"], b["rect"][3])),
                (2, (33, cy, l["W"], cy + CS_D))],
               pave=[("drive", (0, 0, 12, b["rect"][1] + 20))],
               paths=[[(6, b["rect"][1] + 20), (6, cy + 6), (13, cy + 6)]],
               notes=["The Casita parks at the end of the drive and walks back."])


def l5_trio_drive(d, lot="L5"):
    l = LOT[lot]
    f, g, r = HOME_RULES["front"], 20.0, HOME_RULES["rear"]
    a = c2(13, f, "A", d)
    b = c2(13, f + d + g, "B", d)
    cy = l["L"] - r - CS_D
    cs = casita(13, cy, park=True)
    return opt(f"{lot}-T2", lot, "Trio, drive to every home", [a, b, cs],
               [(0, (33, f, l["W"], f + d)), (1, (33, b["rect"][1], l["W"], b["rect"][3])),
                (2, (33, cy, l["W"], cy + CS_D))],
               pave=[("drive", (0, 0, 12, cy + 20))],
               notes=["Drive runs to the Casita at the back."])


def l6_split2(d, lot="L6"):
    l = LOT[lot]
    f = SMALL_RULES["front"]
    a = c2(5, f, "A", d, bay="s-half-w")
    b = c2(25, f, "B", d, bay="s-half-e")
    py = min(f + d + 24, l["L"] - SMALL_RULES["rear"])
    return opt(f"{lot}-S2", lot, "Two small lots, one Casa 02 each", [a, b],
               [(0, (5, f + d, 25, py)), (1, (25, f + d, 45, py))],
               pave=[("apron", (5, 0, 15, f)), ("apron", (35, 0, 45, f))],
               sublots=[((0, 0, 25, l["L"]), [0]), ((25, 0, 50, l["L"]), [1])],
               notes=["Each owner gets their own 25 x 125 lot.", "Needs a resubdivision (replat)."])


def l6_split3(d, lot="L6"):
    l = LOT[lot]
    f = SMALL_RULES["front"]
    w = l["W"] / 3
    homes = [c2(5, f, "A", d, bay="s-half-w"), c2(w, f, "B", d, bay="s-half-w"), c2(2 * w, f, "C", d, bay="s-half-w")]
    return opt(f"{lot}-S3", lot, "Three small lots, one Casa 02 each", homes,
               [(i, (h["rect"][0], f + d, h["rect"][2], f + d + 20)) for i, h in enumerate(homes)],
               pave=[("apron", (h["rect"][0], 0, h["rect"][0] + 10, f)) for h in homes],
               sublots=[((i * w, 0, (i + 1) * w, l["L"]), [i]) for i in range(3)],
               notes=["Each lot is 16.7 ft wide (minimum 15)."])


LAYOUTS = [l1_duo_side, l1_duo_frontback, l1_trio_onfoot, l1_trio_frontback,
           l2_duo_alley, l2_trio_street, l2_trio_casita_front,
           l3_duo, l3_trio, l3_trio3,
           l4_casa01_casita, l4_duo_frontback, l4_trio_drive, l4_trio_row,
           l5_duo, l5_trio_onfoot, l5_trio_drive,
           l6_split2, l6_split3]


# ---------------------------------------------------------------- checks
def envelope(l, rules, sub=None):
    """Buildable rectangle after setbacks."""
    W, L = l["W"], l["L"]
    if sub is not None:
        x0, _, x1, _ = sub
        west = rules["side"] if x0 <= 0.01 else rules["inner"]
        east = rules["side"] if x1 >= W - 0.01 else rules["inner"]
        return (x0 + west, rules["front"], x1 - east, L - rules["rear"])
    east = rules["street_side"] if l.get("corner") else rules["side"]
    return (rules["side"], rules["front"], W - east, L - rules["rear"])


def direction(p, h):
    if p[0] >= h[2] - 0.01:
        return "east"
    if p[2] <= h[0] + 0.01:
        return "west"
    if p[1] >= h[3] - 0.01:
        return "north"
    return "south"


SUN = {"east": ("Afternoon shade", "ok"), "north": ("In the house's shadow", "note"),
       "south": ("Full sun; needs a tree", "note"), "west": ("Hot afternoons", "bad")}


def who(h):
    return h["label"] if h["kind"] != "C2" else f"Home {h['label']}"


def check(o):
    l = LOT[o["lot"]]
    W, L = l["W"], l["L"]
    A = W * L
    small = l.get("small")
    rules = SMALL_RULES if small else HOME_RULES
    homes = o["homes"]
    n = len(homes)
    fails, flags = [], []

    # setbacks
    groups = o["sublots"] or [((0, 0, W, L), list(range(n)))]
    for sub, idx in groups:
        env = envelope(l, rules, sub if small else None)
        for i in idx:
            r = homes[i]["rect"]
            if r[0] < env[0] - 0.01 or r[1] < env[1] - 0.01 or r[2] > env[2] + 0.01 or r[3] > env[3] + 0.01:
                fails.append(f"{who(homes[i])} is outside the setbacks")
    # building separation
    gaps = []
    for i in range(n):
        for j in range(i + 1, n):
            g = gap(homes[i]["rect"], homes[j]["rect"])
            if g < 0:
                continue
            gaps.append(g)
            if 0 < g < 6:
                flags.append(f"{homes[i]['label']}-{homes[j]['label']} {g:.0f} ft apart: rated walls, no windows facing")
            elif 6 <= g < 10:
                flags.append(f"{homes[i]['label']}-{homes[j]['label']} {g:.0f} ft apart: rated walls, few windows facing")
    overlaps = [(i, j) for i in range(n) for j in range(i + 1, n) if area(clip(homes[i]["rect"], homes[j]["rect"])) > 0.01]
    if overlaps:
        fails.append("Homes overlap")

    bc = sum(h.get("bc", area(h["rect"])) for h in homes)
    pave = sum(area(clip(r, (0, 0, W, L))) for _k, r in o["pave"]) + o.get("extra_ic", 0.0)
    fy_zone = (0, 0, W, rules["front"])
    fy = sum(area(clip(r, fy_zone)) for _k, r in o["pave"])
    fy_cap = rules["front_yard_ic"] * W * rules["front"]
    fa = sum(h["fa"] for h in homes)
    res = dict(id=o["id"], lot=o["lot"], name=o["name"], n=n, lot_area=A,
               homes=", ".join(f"{h['label']}: {('Casa 02' if h['kind'] == 'C2' else 'Casita' if h['kind'] == 'CS' else 'Casa 01')}"
                               for h in homes),
               fa=fa, bc=bc, pave=pave, ic=bc + pave, fy=fy, fy_cap=fy_cap,
               parking=sum(1 for h in homes if h["park"]), gaps=gaps)

    if small:
        sub_rows = []
        for sub, idx in groups:
            sa = area(sub)
            sw = sub[2] - sub[0]
            sbc = sum(area(homes[i]["rect"]) for i in idx)
            spv = sum(area(clip(r, sub)) for _k, r in o["pave"])
            sfy = sum(area(clip(r, clip(sub, fy_zone))) for _k, r in o["pave"])
            sub_rows.append(dict(area=sa, width=sw, bc=sbc, bc_cap=rules["bc"] * sa, ic=sbc + spv,
                                 ic_cap=rules["ic"] * sa))
            if sa < rules["min_area"]:
                fails.append(f"Lot of {sa:,.0f} sf is under the 1,800 sf minimum")
            if sw < rules["min_width"]:
                fails.append(f"Lot {sw:.1f} ft wide is under the 15 ft minimum")
            if sbc > rules["bc"] * sa:
                fails.append("Building coverage over 40% on a small lot")
            if sbc + spv > rules["ic"] * sa:
                fails.append("Impervious cover over 45% on a small lot")
            if sfy > rules["front_yard_ic"] * sw * rules["front"]:
                fails.append("Front yard paving over 40% on a small lot")
        res["sub"] = sub_rows
        res.update(bc_cap=rules["bc"] * A, ic_cap=rules["ic"] * A, fa_cap=None)
        left = min(s["ic_cap"] - s["ic"] for s in sub_rows)
        res["ic_left"] = sum(s["ic_cap"] - s["ic"] for s in sub_rows)
        res["ic_left_home"] = left
        flags.append("Small-lot setbacks, coverage and size limits assumed; confirm with the city")
    else:
        bc_cap, ic_cap = rules["bc"] * A, rules["ic"] * A
        far = rules["far2"] if n == 2 else rules["far3"]
        fa_cap = max(far[0] * A, far[1]) if n >= 2 else None
        unit_cap = max(rules["unit"][0] * A, rules["unit"][1])
        res.update(bc_cap=bc_cap, ic_cap=ic_cap, fa_cap=fa_cap, unit_cap=unit_cap)
        if bc > bc_cap + 0.5:
            fails.append(f"Building coverage {bc:,.0f} sf is over the {bc_cap:,.0f} sf cap")
        if bc + pave > ic_cap + 0.5:
            fails.append(f"Impervious cover {bc + pave:,.0f} sf is over the {ic_cap:,.0f} sf cap")
        if fa_cap and fa > fa_cap + 0.5:
            fails.append(f"Floor area {fa:,.0f} sf is over the {fa_cap:,.0f} sf cap")
        if any(h["fa"] > unit_cap + 0.5 for h in homes):
            fails.append("One home is over the single-home floor-area cap")
        res["ic_left"] = ic_cap - bc - pave
        res["ic_left_home"] = res["ic_left"] / n
    if fy > fy_cap + 0.5:
        fails.append(f"Front-yard paving {fy:,.0f} sf is over the {fy_cap:,.0f} sf limit")
    if any(h["rect"][3] > L for h in homes):
        fails.append("Does not fit the lot depth")

    pats = []
    for i, p in o["patios"]:
        h = homes[i]
        dirn = direction(p, h["rect"])
        sun, tone = SUN[dirn] if h["stories"] == 2 else ("One story", "ok")
        pats.append(dict(home=h["label"], area=area(p), dir=dirn, sun=sun, tone=tone))
        if area(p) < 150:
            flags.append(f"{h['label']}'s pátio is only {area(p):.0f} sf")
    res["patios"] = pats
    if res["parking"] < n:
        flags.append(f"{n - res['parking']} home(s) without on-site parking")

    res["fails"] = list(dict.fromkeys(fails))
    res["flags"] = list(dict.fromkeys(flags))
    if fails:
        res["verdict"] = "Fails"
    elif res["ic_left_home"] < TERRACE_PER_HOME:
        res["verdict"] = "Tight"
    else:
        res["verdict"] = "Fits"
    return res


def max_depth(fn):
    """Deepest Casa 02 (whole feet, 28-50) for which the layout passes with a terrace's worth of paving left."""
    best = None
    for d in range(28, 51):
        r = check(fn(float(d)))
        if not r["fails"] and r["ic_left_home"] >= TERRACE_PER_HOME:
            best = d
    return best


# ---------------------------------------------------------------- drawing
COL = dict(C2=("#d8e4ef", "#2f5f8a"), CS=("#f6e1d3", "#b55a35"), C01=("#ece6d6", "#6b5d3e"))


def plan_svg(o, res, d):
    l = LOT[o["lot"]]
    W, L = l["W"], l["L"]
    fs = 2.7 * max(1.0, L / 125.0) ** 0.5
    ml, mr = 4.0, 4.0 + (9.0 if l.get("corner") else 0.0)
    over = max([0.0] + [h["rect"][3] - L for h in o["homes"]])
    mt, mb = 4.0 + (9.0 if l.get("alley") else 0.0) + over, 11.0
    vw, vh = W + ml + mr, L + mt + mb

    def X(x):
        return ml + x

    def Y(y):
        return mt + (L - y)

    def R(r, **kw):
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
        return f'<rect x="{X(r[0]):.2f}" y="{Y(r[3]):.2f}" width="{r[2] - r[0]:.2f}" height="{r[3] - r[1]:.2f}" {a}/>'

    def T(x, y, s, size=None, weight=400, fill="#1b1d1f", anchor="middle", rot=None):
        tr = f' transform="rotate({rot} {X(x):.2f} {Y(y):.2f})"' if rot else ""
        return (f'<text x="{X(x):.2f}" y="{Y(y):.2f}" font-size="{(size or fs):.2f}" font-weight="{weight}" '
                f'fill="{fill}" text-anchor="{anchor}"{tr}>{s}</text>')

    out = []
    # street, alley, side street
    out.append(f'<rect x="0" y="{mt + L + 2:.2f}" width="{vw:.2f}" height="7" fill="#e6e2d8"/>')
    out.append(f'<text x="{X(W / 2):.2f}" y="{mt + L + 6.9:.2f}" font-size="{fs * .9:.2f}" text-anchor="middle" '
               f'fill="#5b625b" letter-spacing=".3">STREET</text>')
    if l.get("alley"):
        out.append(f'<rect x="0" y="{mt - 9:.2f}" width="{vw:.2f}" height="7" fill="#e6e2d8"/>')
        out.append(f'<text x="{X(W / 2):.2f}" y="{mt - 4.1:.2f}" font-size="{fs * .9:.2f}" text-anchor="middle" '
                   f'fill="#5b625b">ALLEY</text>')
    if l.get("corner"):
        out.append(f'<rect x="{X(W) + 2:.2f}" y="0" width="7" height="{vh:.2f}" fill="#e6e2d8"/>')
        out.append(f'<text x="{X(W) + 6.9:.2f}" y="{Y(L / 2):.2f}" font-size="{fs * .9:.2f}" text-anchor="middle" '
                   f'fill="#5b625b" transform="rotate(-90 {X(W) + 6.9:.2f} {Y(L / 2):.2f})">SIDE STREET</text>')
    # sublot lines, lot line, setbacks
    out.append(R((0, 0, W, L), fill="#fbfaf6", stroke="#1b1d1f", stroke_width=".35"))
    small = l.get("small")
    rules = SMALL_RULES if small else HOME_RULES
    groups = o["sublots"] or [((0, 0, W, L), None)]
    for sub, _ in groups:
        env = envelope(l, rules, sub if small else None)
        out.append(R(env, fill="none", stroke="#9a9488", stroke_width=".22", stroke_dasharray="1.2 .8"))
        if small and sub[0] > 0.01:
            out.append(f'<line x1="{X(sub[0]):.2f}" y1="{Y(0):.2f}" x2="{X(sub[0]):.2f}" y2="{Y(L):.2f}" '
                       f'stroke="#1b1d1f" stroke-width=".3" stroke-dasharray="3 1.2"/>')
    # pátios, paving, paths
    for i, p in o["patios"]:
        out.append(R(p, fill="#e3ecd9", stroke="none"))
        cx, cy = (p[0] + p[2]) / 2, (p[1] + p[3]) / 2
        if p[2] - p[0] >= 7 and p[3] - p[1] >= 6:
            out.append(T(cx, cy - fs * .2, "Pátio", fs * .85, fill="#4b6a3e"))
            out.append(T(cx, cy - fs * 1.15, f"{area(p):,.0f} sf", fs * .72, fill="#4b6a3e"))
    for k, r in o["pave"]:
        rr = clip(r, (0, 0, W, L)) if k != "apron" or not l.get("alley") else r
        out.append(R(r, fill="#d6d1c4", stroke="none"))
        if k in ("drive", "pad") and r[3] - r[1] > 14:
            out.append(T((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, "Drive" if k == "drive" else "Parking", fs * .8,
                         fill="#5b625b", rot=-90 if r[2] - r[0] < 14 else None))
        del rr
    for pts in o["paths"]:
        dd = " ".join(f"{X(x):.2f},{Y(y):.2f}" for x, y in pts)
        out.append(f'<polyline points="{dd}" fill="none" stroke="#8a826f" stroke-width=".45" stroke-dasharray=".9 .9"/>')
    # homes
    for h in o["homes"]:
        fill, stroke = COL[h["kind"]]
        if h["kind"] == "C01":
            pts = " ".join(f"{X(x):.2f},{Y(y):.2f}" for x, y in h["poly"])
            out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width=".45"/>')
            cx, cy = 18.0, (h["rect"][1] + h["rect"][3]) / 2
        else:
            out.append(R(h["rect"], fill=fill, stroke=stroke, stroke_width=".45"))
            if h.get("bay"):
                out.append(R(h["bay"], fill="#ffffff", fill_opacity=".55", stroke=stroke, stroke_width=".22",
                             stroke_dasharray=".8 .6"))
                b = h["bay"]
                out.append(T((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - fs * .3, "car", fs * .7, fill=stroke))
            r = h["rect"]
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            if h.get("bay"):
                b = h["bay"]
                # put the label in the larger part of the box, away from the carport
                if b[3] - b[1] < r[3] - r[1] - 8:
                    cy = (max(b[3], r[1]) + r[3]) / 2 if abs(b[1] - r[1]) < .1 else (r[1] + min(b[1], r[3])) / 2
        name = {"C2": "Casa 02", "CS": "Casita", "C01": "Casa 01"}[h["kind"]]
        out.append(T(cx, cy + fs * .9, f"{h['label']} · {name}" if h["kind"] == "C2" else name, fs, 700, fill="#1b1d1f"))
        out.append(T(cx, cy - fs * .25, f"{h['fa']:,.0f} sf", fs * .8))
        out.append(T(cx, cy - fs * 1.25, "2 story" if h["stories"] == 2 else "1 story", fs * .8, fill="#5b625b"))
    # north arrow
    nx, ny = X(W) - 3.0, Y(L) + 4.0
    out.append(f'<g transform="translate({nx:.2f} {ny:.2f})"><circle r="2.4" fill="#fff" stroke="#1b1d1f" stroke-width=".25"/>'
               f'<path d="M0 -1.9 L1 1.2 L0 .6 L-1 1.2 Z" fill="#1b1d1f"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.2f} {vh:.2f}" '
            f'font-family="Lato, Helvetica Neue, Arial, sans-serif">{"".join(out)}</svg>')


# ---------------------------------------------------------------- report
VERDICT_COL = {"Fits": "#2e7d4f", "Tight": "#b7791f", "Fails": "#a3361f"}


def fmt(v):
    return f"{v:,.0f}"


def metric_rows(r):
    rows = []
    if r.get("fa_cap"):
        rows.append(("Floor area", f"{fmt(r['fa'])} of {fmt(r['fa_cap'])} sf", r["fa"] <= r["fa_cap"]))
    else:
        rows.append(("Floor area", f"{fmt(r['fa'])} sf (size cap to confirm)" if LOT[r['lot']].get('small')
                     else f"{fmt(r['fa'])} sf", True))
    if r.get("sub"):
        s = r["sub"][0]
        rows.append(("Each lot", f"{fmt(s['area'])} sf, {s['width']:.1f} ft wide", s["area"] >= 1800 and s["width"] >= 15))
        ok_bc = all(x["bc"] <= x["bc_cap"] for x in r["sub"])
        ok_ic = all(x["ic"] <= x["ic_cap"] for x in r["sub"])
        rows.append(("Footprint per lot", " / ".join(f"{fmt(x['bc'])} of {fmt(x['bc_cap'])}" for x in r["sub"]), ok_bc))
        rows.append(("Impervious per lot", " / ".join(f"{fmt(x['ic'])} of {fmt(x['ic_cap'])}" for x in r["sub"]), ok_ic))
    else:
        rows.append(("Footprint", f"{fmt(r['bc'])} of {fmt(r['bc_cap'])} sf ({r['bc'] / r['lot_area']:.0%})",
                     r["bc"] <= r["bc_cap"] + .5))
        rows.append(("Impervious", f"{fmt(r['ic'])} of {fmt(r['ic_cap'])} sf ({r['ic'] / r['lot_area']:.0%})",
                     r["ic"] <= r["ic_cap"] + .5))
        rows.append(("Left for terraces", f"{fmt(r['ic_left'])} sf ({fmt(r['ic_left_home'])} per home)",
                     r["ic_left_home"] >= TERRACE_PER_HOME))
    rows.append(("Front-yard paving", f"{fmt(r['fy'])} of {fmt(r['fy_cap'])} sf", r["fy"] <= r["fy_cap"] + .5))
    rows.append(("Parking on site", f"{r['parking']} of {r['n']} homes", r["parking"] == r["n"]))
    pats = "; ".join(f"{p['home']} {p['dir']}, {fmt(p['area'])} sf" for p in r["patios"])
    rows.append(("Pátios", pats, all(p["tone"] != "bad" for p in r["patios"])))
    return rows


CSS = open(os.path.join(ROOT, "casa01", "signoff", "signoff_v2.py")).read().split('CSS = """')[1].split('"""')[0]
CSS += """
.lots{display:grid;gap:.18in;min-height:0}
.opt{display:grid;grid-template-rows:2.2em auto auto;gap:5px;min-height:0;min-width:0;align-content:start}
.opt .pl{height:6.35in;display:flex;align-items:flex-end;justify-content:center}
.opt .pl svg{height:100%;width:auto;max-width:100%}
.opt h3{margin:0;font-size:11.5px;display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.opt h3 small{font-weight:400;color:#5b625b;font-size:9.5px}
.vd{font-size:9.5px;font-weight:900;letter-spacing:.1em;text-transform:uppercase;padding:2px 6px;border-radius:3px;color:#fff;white-space:nowrap}
.m{font-size:9.4px;border-collapse:collapse;width:100%}
.m td{border-bottom:1px solid #ebe6da;padding:2px 3px;vertical-align:top}
.m td:first-child{color:#5b625b;white-space:nowrap;width:1%}
.m td.x{color:#a3361f;font-weight:700}
.why{font-size:9.2px;line-height:1.35;color:#1b1d1f;margin:0;padding-left:12px}
.why li.f{color:#a3361f}
.sum td,.sum th{font-size:10px;padding:3px 5px}
.lead{font-size:12.5px;line-height:1.45;max-width:10.5in;margin:0}
.k{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.2in}
"""


def title_block(sheet, title, scale="As noted"):
    return (f'<aside class="tb"><div class="brand">Brazilian Modern Homes<small>Residential design · Austin</small></div>'
            f'<div class="proj">Phase 2<br>Duo + Trio<small>Test-fit study · massing only</small></div>'
            f'<div class="grow"></div><div class="kv"><span>Sheet title</span><b>{title}</b><span>Scale</span><b>{scale}</b>'
            f'<span>Date / phase</span><b>Nov 2026 · Phase 2 study</b></div><div class="sheet">{sheet}</div>'
            f'<div class="warn">Concept study. Rules to confirm with the city.</div></aside>')


def opt_block(o, r, svg, md):
    col = VERDICT_COL[r["verdict"]]
    rows = "".join(f'<tr><td>{k}</td><td class="{"" if ok else "x"}">{v}</td></tr>' for k, v, ok in metric_rows(r))
    md_txt = f"{md} ft" if md else "none"
    rows += f'<tr><td>Deepest Casa 02</td><td>{md_txt}</td></tr>'
    why = "".join(f'<li class="f">{t}</li>' for t in r["fails"]) + "".join(f"<li>{t}</li>" for t in r["flags"][:3])
    why += "".join(f"<li>{t}</li>" for t in o["notes"][:2])
    return (f'<div class="opt"><h3><span>{o["id"]} · {o["name"]}</span><span class="vd" style="background:{col}">'
            f'{r["verdict"]}</span></h3><div class="pl">{svg}</div><div><table class="m">{rows}</table>'
            f'<ul class="why">{why}</ul></div></div>')


def main():
    os.makedirs(os.path.join(OUT, "plans"), exist_ok=True)
    results, by_lot = [], {}
    for fn in LAYOUTS:
        o = fn(C2_D)
        r = check(o)
        r["max_depth"] = max_depth(fn) if any(h["kind"] == "C2" for h in o["homes"]) else None
        r["max_depth_fa"] = c2_area(r["max_depth"]) if r["max_depth"] else None
        svg = plan_svg(o, r, C2_D)
        open(os.path.join(OUT, "plans", f"{o['id']}.svg"), "w").write(svg)
        results.append(r)
        by_lot.setdefault(o["lot"], []).append((o, r, svg))
    json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=str)

    pages = []
    # summary sheet
    rows = ""
    for r in results:
        col = VERDICT_COL[r["verdict"]]
        md = f'{r["max_depth"]} ft ({fmt(r["max_depth_fa"])} sf)' if r["max_depth"] else "–"
        lot = LOT[r["lot"]]
        rows += (f'<tr><td><b>{r["id"]}</b></td><td>{lot["W"]:.0f} × {lot["L"]:.0f}{" alley" if lot.get("alley") else ""}'
                 f'{" corner" if lot.get("corner") else ""}{" split" if lot.get("small") else ""}</td><td>{r["name"]}</td>'
                 f'<td class="n">{fmt(r["fa"])}</td><td class="n">{r["bc"] / r["lot_area"]:.0%}</td>'
                 f'<td class="n">{r["ic"] / r["lot_area"]:.0%}</td><td class="n">{fmt(r["ic_left_home"])}</td>'
                 f'<td class="n">{r["parking"]}/{r["n"]}</td><td>{md}</td>'
                 f'<td><b style="color:{col}">{r["verdict"]}</b></td></tr>')
    pages.append(summary_page(rows, results))
    for i, l in enumerate(LOTS):
        items = by_lot[l["id"]]
        cols = len(items)
        blocks = "".join(opt_block(o, r, svg, r["max_depth"]) for o, r, svg in items)
        head = (f'<h1>{l["id"]} · {l["name"]}, {l["W"]:.0f} × {l["L"]:.0f} ft ({l["W"] * l["L"]:,.0f} sf)</h1>')
        pages.append(f'<section class="page"><div class="main" style="grid-template-rows:auto 1fr">{head}'
                     f'<div class="lots" style="grid-template-columns:repeat({cols},1fr)">{blocks}</div></div>'
                     f'{title_block(f"T-{i + 1}", l["name"], "Plans to scale")}</section>')
    pages.append(findings_page(results))
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Phase 2 test-fit study</title>'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(os.path.join(OUT, "testfit.html"), "w").write(html)
    print("wrote", os.path.join(OUT, "testfit.html"))
    for r in results:
        print(f'{r["id"]:6} {r["verdict"]:6} fa {r["fa"]:6.0f} bc {r["bc"]:6.0f}/{r["bc_cap"]:5.0f} ic {r["ic"]:6.0f}/'
              f'{r["ic_cap"]:5.0f} left/home {r["ic_left_home"]:5.0f} park {r["parking"]}/{r["n"]} maxD {r["max_depth"]} '
              f'| {"; ".join(r["fails"])}')


def summary_page(rows, results):
    lead = ("Each layout below is a set of plain boxes on a standard Austin lot, checked against the rules for 2–3 homes "
            "on one lot (HOME Phase 1) or for a small-lot split (Phase 2). Casa 02 is drawn 20 × 40 ft (1,400 sf, two "
            "stories, its carport under the upper floor); the Casita 20 × 32 ft (640 sf, one story). "
            "\"Deepest Casa 02\" is the longest Casa 02 that still passes with 100 sf of terrace paving per home.")
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto auto auto;align-content:start">'
            f'<h1>Test-fit study · 19 layouts on 6 standard lots</h1><p class="lead">{lead}</p>'
            f'<table class="sum"><thead><tr><th>Layout</th><th>Lot (ft)</th><th>Option</th><th class="n">Floor area sf</th>'
            f'<th class="n">Footprint</th><th class="n">Impervious</th><th class="n">Paving left per home sf</th>'
            f'<th class="n">Parking</th><th>Deepest Casa 02</th><th>Verdict</th></tr></thead><tbody>{rows}</tbody></table>'
            f'</div>{title_block("T-0", "Summary")}</section>')


def findings_page(results):
    R = {r["id"]: r for r in results}
    winners = [("Standard 50 × 125", "L1-D1", "Duo side by side"),
               ("Standard 50 × 125", "L1-T1", "Trio: two at the street, Casita on foot"),
               ("50 × 125 with alley", "L2-T2", "Trio: Casita at the street, pair on the alley"),
               ("Corner 60 × 125", "L3-T1", "Trio: Casita facing the side street"),
               ("Corner 60 × 125", "L3-T2", "Trio: three Casa 02"),
               ("Wide 65 × 125", "L4-T1", "Trio: drive stops at the middle home"),
               ("Deep 50 × 175", "L5-T1", "Trio: drive stops at the middle home"),
               ("Small-lot split", "L6-S2", "Two 25 × 125 lots, one Casa 02 each")]
    wr = ""
    for lot, i, txt in winners:
        r = R[i]
        wr += (f'<tr><td><b>{i}</b></td><td>{lot}</td><td>{txt}</td>'
               f'<td><b style="color:{VERDICT_COL[r["verdict"]]}">{r["verdict"]}</b></td>'
               f'<td class="n">{r["max_depth"]} ft</td><td class="n">{fmt(c2_area(r["max_depth"]))}</td></tr>')
    ds = {i: R[i]["max_depth"] for _l, i, _t in winners}
    target = min(ds.values())
    binding = [i for i, d in ds.items() if d == target]
    t40 = R[binding[0]]
    lessons = [
        f"Floor area, not footprint, caps the 50-ft duo: two Casa 02 hit the 3,437 sf cap at "
        f"{R['L1-D1']['max_depth']} ft deep.",
        f"Casa 01 + Casita fails on a 65-ft lot: Casa 01's roof covers {fmt(R['L4-D1']['bc'] - 640)} sf, so the pair "
        f"needs {fmt(R['L4-D1']['bc'])} sf of the {fmt(R['L4-D1']['bc_cap'])} sf footprint cap. Casa 01 stays a "
        f"single-family design.",
        "Drives decide trios. A drive to the back home fails the impervious cap on the 50-ft and the deep lot "
        "(L1-T2, L5-T2); a drive that stops at the middle home passes (L4-T1, L5-T1).",
        "Three Casa 02 fit on a corner (L3-T2), with the third facing the side street, but not in a row on a "
        "65-ft lot (L4-T2): a row of three 20-ft homes needs a 70-ft lot.",
        "A 50-ft lot splits into two small lots that each take a Casa 02 (L6-S2), but not three (L6-S3): "
        "16.7-ft lots are too narrow.",
        "Parking under the upper floor costs each Casa 02 200 sf of floor area but adds no footprint or paving. "
        "An open pad instead would add 200 sf of paving per home, which the trios cannot spare.",
    ]
    li = "".join(f"<li>{t}</li>" for t in lessons)
    return (f'<section class="page"><div class="main" style="grid-template-rows:auto auto auto auto 1fr">'
            f'<h1>What the test-fit tells us</h1>'
            f'<table><thead><tr><th>Layout</th><th>Lot</th><th>Winning layout</th><th>At 40 ft</th>'
            f'<th class="n">Deepest Casa 02</th><th class="n">Casa 02 sf at that depth</th></tr></thead>'
            f'<tbody>{wr}</tbody></table>'
            f'<div class="k"><div class="box rec"><b>Casa 02 design target: 20 × {target} ft</b>'
            f'About {fmt(c2_area(target))} sf on two floors, plus the carport bay under the upper floor. At this depth '
            f'every winning layout passes with room for a terrace per home. {", ".join(binding)} sets the limit; '
            f'at 40 ft it is tight, with {fmt(t40["ic_left_home"])} sf of paving left per home. A 3-bed, 2.5-bath plan '
            f'in that size is a compact townhouse; a 2-bed + flex plan is the fallback.</div>'
            f'<div class="box"><b>Casita design target: 20 × 32 ft</b>640 sf, one story. It must work with and '
            f'without its own parking, and with its entry from the side yard, the street or an alley.</div>'
            f'<div class="box"><b>Confirm with the city</b>How ribbon drives, pervious pavers, gravel and decks count '
            f'toward impervious cover; the small-lot setbacks, coverage and size cap; and that the rear setback is '
            f'5 ft next to homes, as assumed here.</div></div>'
            f'<div><h2>Lessons</h2><ul>{li}</ul></div><div></div></div>{title_block("T-7", "Findings")}</section>')


if __name__ == "__main__":
    main()
