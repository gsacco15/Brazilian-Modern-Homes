"""Phase 2 concept plans: Casa 02 (two-story, 20 x 39 ft) and the Casita (one story, 20 x 32 ft).

Feet. Each home is drawn in its own frame: x runs across the front (0 at the left as seen from the
street or drive), y runs from the front face (0) to the back (the pátio end).

A wall is a segment a -> b with a thickness. Exterior walls are listed counter-clockwise, so their
thickness lies to the left of a -> b (inside the house). Partitions are centred on their line.
Openings sit at a distance `off` along the wall from a:
    door    swings to the left ("L") or right ("R") of a -> b, hinged at the start ("s") or end ("e")
    window  glass in the wall (sill noted in `note`)
    slider  sliding glass door
"""

EXT, INT = 0.5, 0.375


def loop(pts, openings=None):
    """Closed exterior wall loop (counter-clockwise). openings: {edge index: [opening, ...]}."""
    openings = openings or {}
    return [dict(a=pts[i], b=pts[(i + 1) % len(pts)], t=EXT, ext=True, openings=openings.get(i, []))
            for i in range(len(pts))]


def part(a, b, *openings):
    return dict(a=a, b=b, t=INT, ext=False, openings=list(openings))


def door(off, w=2.67, side="L", hinge="s"):
    return dict(kind="door", off=off, w=w, side=side, hinge=hinge)


def win(off, w, note=""):
    return dict(kind="window", off=off, w=w, note=note)


def slider(off, w):
    return dict(kind="slider", off=off, w=w)


# ------------------------------------------------------------------ Casa 02
# Developed plans (Nov 2026). x = 20 is the shared wall of a side-by-side pair: a 1-hour fire wall with no
# openings, so the attached versions (C02-GC and the upper floor) put every window on the front, back and outer
# side. The service strip beside the bay (x 10.5 to 20) holds, front to back: the entry and WC behind the cobogó,
# a 4'-9" gallery hall open to the stair through cedar slats, and the stair, which rises from the kitchen to a
# landing behind the cobogó upstairs. The mechanical closet sits under the top of the stair.
W2, D2 = 20.0, 39.0
BAY = (0.0, 0.0, 10.5, 20.0)          # flex bay at the front corner (car comes straight in)
STAIR_X = 16.0                        # stair: x 16 to 20 (3'-3 3/4" clear), y 6 to 19.5

SERVICE_PARTS = [
    part((14.25, 0.0), (14.25, 5.5), door(1.0, 2.83, "R", "s")),      # entry | WC (2'-10" door, visitable)
    part((14.25, 5.5), (20.0, 5.5)),                                  # WC | mechanical
    part((STAIR_X, 5.5), (STAIR_X, 9.5), door(0.75, 2.5, "L", "s")),   # hall | mechanical (under the stair top)
    part((STAIR_X, 9.5), (20.0, 9.5)),                                # mechanical | storage under the stair
]
SERVICE_ROOMS = [
    dict(name="Entry", rect=(10.5, 0.0, 14.25, 5.5), lab=(12.4, 3.6)),
    dict(name="WC", rect=(14.25, 0.0, 20.0, 5.5), lab=(15.7, 4.6)),
    dict(name="Hall", rect=(10.5, 5.5, STAIR_X, 20.0), lab=(14.1, 12.8)),
    dict(name="Mech", rect=(STAIR_X, 5.5, 20.0, 9.5), lab=(18.0, 7.2)),
    dict(name="Kitchen", rect=(0.0, 20.0, 20.0, 27.0), lab=(15.0, 25.4)),
    dict(name="Living + dining", rect=(0.0, 27.0, 20.0, 39.0), lab=(14.6, 30.4)),
]
# 17 risers at 7 7/16 in (10'-6" floor to floor), 16 treads at 10 1/8 in. It rises toward the front.
STAIR = dict(rect=(STAIR_X, 6.0, 20.0, 19.5), top="front", floor="lower", cut=13.0, risers=17)
STAIR_SLATS = [((STAIR_X, 9.5), (STAIR_X, 19.5))]                  # cedar slats between the hall and the stair
# The cobogó lantern (facade direction C, chosen in the study): 12 in concrete blocks in a 9 ft wide screen,
# 1 ft in front of the entry, WC and the landing above, rising both floors to the roof. It stays open for 4 ft
# in front of the front door, under a header of blocks.
LANTERN = dict(x=(11.0, 20.0), y=(-1.0, -0.67), opening=(11.0, 15.0), note="cobogó screen, two stories")
# The Casa 01 staples, used once per home (Nov 2026):
# - Lueders limestone, sawn-face ashlar in three course heights, on the outer side of the ground floor: a pier at
#   the carport's street corner (it carries the upper floor in place of the front column) and the outer wall of
#   the kitchen and living room; on the suite version, the whole outer side and the suite's street wall. The
#   white upper floor floats over a stone base, and a pair reads stone | cedar gate | cobogó | cobogó | gate | stone.
# - Black calçada portuguesa, about 50 sf at the entry, as at Casa 01: a rug in the carport at the no-step door
#   and a threshold under the cobogó at the front door. Both sit under the house, so they add no impervious cover.
# - Pedra São Tomé (Lueders limestone pavers, 24 x 36 thermal) on the terraces and the stepping stones.
STONE_GC = dict(walls=[((0.0, 39.0), (0.0, 20.0))], piers=[(0.0, 0.0, 1.5, 1.5)])
STONE_GS = dict(walls=[((0.0, 39.0), (0.0, 0.0)), ((0.0, 0.0), (10.5, 0.0))], piers=[])
CALCADA_THRESHOLD = (11.0, -0.95, 20.0, 0.0)
BACK_GLASS = {2: [slider(2.0, 16.0)]}                 # back wall: 16 ft slider to the pátio
EAST_GLASS = [slider(28.0, 8.0)]                       # outer long wall of a detached home, where the pátio is
SERVICE_FIX = [
    dict(kind="wc", at=(18.4, 5.0), rot=180),
    dict(kind="lav", rect=(17.4, 0.55, 19.45, 2.0)),
    dict(kind="counter", rect=(11.0, 10.4, 12.35, 14.2), note="bench, coat hooks above"),
    dict(kind="counter", rect=(11.0, 14.6, 12.35, 19.95), note="pantry, floor to ceiling"),
    dict(kind="mech", rect=(17.0, 6.2, 19.4, 8.6), note="air handler + heat-pump water heater"),
]
KITCHEN_FIX = [
    dict(kind="fridge", rect=(0.55, 20.55, 3.1, 23.0)),
    dict(kind="counter", rect=(3.1, 20.55, 10.45, 22.55)),
    dict(kind="range", rect=(4.0, 20.55, 6.5, 22.55)),
    dict(kind="sink", rect=(7.6, 20.75, 9.6, 22.35)),
    dict(kind="island", rect=(3.5, 24.2, 11.5, 26.8)),
    dict(kind="table", rect=(2.5, 29.5, 9.5, 33.0)),
    dict(kind="sofa", rect=(11.5, 34.5, 18.8, 37.4)),
]

CASA02_GF_CARPORT = dict(
    name="Casa 02 · ground floor, carport", W=W2, D=D2,
    walls=loop([(10.5, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0), (0.0, 20.0), (10.5, 20.0)],
               {0: [door(0.5, 3.0, "L", "s"), win(6.0, 2.5, "high")],
                2: BACK_GLASS[2], 3: [win(5.0, 6.0, "sill 3'-6\"")],
                5: [door(10.0, 3.0, "L", "e")]}) + SERVICE_PARTS,
    rooms=SERVICE_ROOMS + [dict(name="Carport", rect=BAY, outdoor=True, note="open bay · cedar gate", lab=(5.25, 17.3))],
    fixtures=KITCHEN_FIX + SERVICE_FIX + [dict(kind="car", rect=(2.15, 2.0, 8.35, 17.5))],
    stair=STAIR, slats=STAIR_SLATS,
    columns=[(0.35, 10.0)],                                            # the street corner is the stone pier
    gate=((1.5, 0.0), (10.5, 0.0)),                                    # 9 ft cedar slat gate
    stone=STONE_GC,
    calcada=[(4.75, 4.5, 10.25, 13.5), CALCADA_THRESHOLD],              # rug at the carport door + threshold
    lantern=LANTERN,
    enclosed=W2 * D2 - (BAY[2] - BAY[0]) * (BAY[3] - BAY[1]),
)

CASA02_GF_SUITE = dict(
    name="Casa 02 · ground floor, suite", W=W2, D=D2,
    walls=loop([(0.0, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0)],
               {0: [win(2.25, 5.0, "egress"), door(11.0, 3.0, "L", "s"), win(16.5, 2.5, "high")],
                1: EAST_GLASS, 2: BACK_GLASS[2],
                3: [win(5.0, 6.0, "sill 3'-6\""), win(22.0, 3.0, "high"), win(29.5, 4.0, "fluted below 5'")]})
    + SERVICE_PARTS + [
        part((10.5, 20.0), (10.5, 0.0), door(10.33, 2.67, "R", "s")),  # suite door off the hall
        part((0.0, 12.5), (10.5, 12.5), door(6.75, 2.67, "L", "s")),    # bedroom | bath (30 in clear)
        part((0.0, 20.0), (10.5, 20.0)),                                # bath | kitchen
    ],
    rooms=[dict(name="Suite bedroom", rect=(0.0, 0.0, 10.5, 12.5), short="Bedroom", lab=(5.25, 2.9)),
           dict(name="Suite bath", rect=(0.0, 12.5, 10.5, 20.0), short="Bath", lab=(3.4, 14.3))] + SERVICE_ROOMS,
    fixtures=KITCHEN_FIX + SERVICE_FIX + [
        dict(kind="bed", rect=(2.75, 5.6, 7.75, 12.1)),
        dict(kind="shower", rect=(0.55, 16.0, 4.5, 19.6)),
        dict(kind="wc", at=(5.9, 19.5), rot=180),
        dict(kind="lav", rect=(7.6, 17.9, 10.1, 19.6)),
    ],
    stair=STAIR, slats=STAIR_SLATS,
    stone=STONE_GS,
    calcada=[CALCADA_THRESHOLD],
    lantern=LANTERN,
    enclosed=W2 * D2,
)

CASA02_UPPER = dict(
    name="Casa 02 · upper floor", W=W2, D=D2,
    walls=loop([(0.0, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0)],
               {0: [win(2.0, 6.0, "egress"), win(12.0, 7.0, "behind the cobogó")],
                2: [win(1.5, 3.0, "high"), win(10.0, 9.0, "to the pátio, cedar-screened")],
                3: [win(5.0, 4.0, "high"), win(14.5, 5.0, "egress, fluted below 5'"), win(24.0, 2.5, "high")]})
    + [
        part((10.5, 0.0), (10.5, 27.0), door(7.0, 2.67, "L", "e"), door(12.0, 2.5, "L", "s"),
             door(18.0, 2.67, "L", "e")),                                 # bedrooms + bath | landing and hall
        part((0.0, 11.0), (10.5, 11.0)),                                  # Bed 2 | Bath 2
        part((0.0, 16.5), (10.5, 16.5)),                                  # Bath 2 | Bed 3
        part((0.0, 27.0), (14.0, 27.0), door(10.75, 2.67, "L", "s")),     # Bed 3 and hall | primary
        part((14.0, 19.5), (20.0, 19.5)),                                 # hall + stair | laundry
        part((14.0, 19.5), (14.0, 39.0), door(1.25, 2.5, "R", "e"), door(8.0, 2.5, "L", "e"),
             door(13.5, 2.5, "L", "s")),                                  # laundry, closet, bath
        part((14.0, 23.5), (20.0, 23.5)),                                 # laundry | closet
        part((14.0, 30.0), (20.0, 30.0)),                                 # closet | primary bath
    ],
    rooms=[dict(name="Bed 2", rect=(0.0, 0.0, 10.5, 11.0), lab=(5.25, 1.9)),
           dict(name="Bath 2", rect=(0.0, 11.0, 10.5, 16.5), short="Bath", lab=(3.2, 12.4)),
           dict(name="Bed 3 / den", rect=(0.0, 16.5, 10.5, 27.0), short="Bed 3", lab=(5.25, 18.0)),
           dict(name="Landing", rect=(10.5, 0.0, 20.0, 6.0), lab=(15.0, 3.6), note="desk under the cobogó"),
           dict(name="Hall", rect=(10.5, 6.0, 14.0, 27.0), label=False),
           dict(name="Laundry", rect=(14.0, 19.5, 20.0, 23.5), short="W/D", lab=(15.4, 20.5)),
           dict(name="Closet", rect=(14.0, 23.5, 20.0, 30.0), lab=(17.6, 25.4)),
           dict(name="Primary", rect=(0.0, 27.0, 14.0, 39.0), lab=(7.0, 36.6)),
           dict(name="Primary bath", rect=(14.0, 30.0, 20.0, 39.0), short="Bath", lab=(18.0, 33.9))],
    fixtures=[
        dict(kind="desk", rect=(11.0, 0.55, 15.5, 2.3)),
        dict(kind="bed", rect=(2.75, 3.9, 7.75, 10.6)),
        dict(kind="tub", rect=(0.55, 13.95, 5.55, 16.3)),
        dict(kind="wc", at=(6.75, 15.95), rot=180),
        dict(kind="lav", rect=(8.0, 14.6, 10.3, 16.3)),
        dict(kind="bed", rect=(2.75, 19.7, 7.75, 26.6)),
        dict(kind="wd", rect=(16.8, 19.95, 19.45, 23.3), note="stacked washer + dryer"),
        dict(kind="bed", rect=(3.75, 27.4, 10.25, 34.4), head="s"),
        dict(kind="wc", at=(15.4, 30.5), rot=0),
        dict(kind="lav", rect=(17.0, 30.4, 19.45, 32.2)),
        dict(kind="shower", rect=(16.3, 35.4, 19.45, 38.5)),
    ],
    stair=dict(STAIR, floor="upper", cut=None),
    slats=[((STAIR_X, 6.0), (STAIR_X, 19.5))],                         # cedar slat guard along the stair opening
    void=(STAIR_X, 6.0, 20.0, 19.5),
    lantern=dict(LANTERN, opening=None),
    enclosed=W2 * D2,
)

# ------------------------------------------------------------------ Casita
W3, D3 = 20.0, 32.0
CASITA = dict(
    name="Casita", W=W3, D=D3,
    walls=loop([(0.0, 0.0), (20.0, 0.0), (20.0, 32.0), (0.0, 32.0)],
               {0: [win(3.0, 6.0, ""), door(13.5, 3.0, "L", "s")],
                1: [slider(3.0, 10.0), win(20.5, 3.0, "high")],
                2: [win(11.0, 6.0, "egress")],
                3: [win(22.0, 6.0, "sill 3'-6\""), win(3.0, 4.0, "fluted below 5'")]})
    + [
        part((8.0, 15.0), (8.0, 22.0)),
        part((11.5, 15.0), (20.0, 15.0)),
        part((11.5, 15.0), (11.5, 32.0), door(0.75, 2.5, "L", "s"), door(4.5, 2.5, "R", "s"), door(11.5, 2.5, "R", "e")),
        part((11.5, 18.5), (20.0, 18.5)),
        part((11.5, 25.0), (20.0, 25.0)),
        part((0.0, 22.0), (11.5, 22.0), door(8.25, 2.67, "L", "s")),
    ],
    rooms=[dict(name="Living + kitchen", rect=(0.0, 0.0, 20.0, 15.0), lab=(10.0, 12.4)),
           dict(name="Flex", rect=(0.0, 15.0, 8.0, 22.0), note="desk or guest bed"),
           dict(name="Hall", rect=(8.0, 15.0, 11.5, 22.0), label=False),
           dict(name="W/D + linen", rect=(11.5, 15.0, 20.0, 18.5), short="W/D", lab=(14.0, 16.9)),
           dict(name="Bath", rect=(11.5, 18.5, 20.0, 25.0), lab=(14.6, 20.4)),
           dict(name="Bedroom", rect=(0.0, 22.0, 11.5, 32.0), lab=(5.75, 23.1)),
           dict(name="Closet", rect=(11.5, 25.0, 20.0, 32.0))],
    fixtures=[
        dict(kind="counter", rect=(0.5, 2.0, 2.5, 13.0)),
        dict(kind="range", rect=(0.5, 5.0, 2.5, 7.5)),
        dict(kind="sink", rect=(0.6, 9.0, 2.4, 11.0)),
        dict(kind="fridge", rect=(0.5, 13.0, 3.0, 14.6)),
        dict(kind="table", rect=(5.0, 5.5, 9.0, 10.0)),
        dict(kind="sofa", rect=(13.0, 4.0, 16.0, 12.0)),
        dict(kind="bed", rect=(3.25, 24.5, 8.25, 31.2)),
        dict(kind="shower", rect=(16.0, 21.5, 19.6, 24.6)),
        dict(kind="wc", at=(13.0, 24.5), rot=180),
        dict(kind="lav", rect=(17.5, 18.9, 19.6, 20.6)),
        dict(kind="wd", rect=(16.8, 15.4, 19.6, 18.1)),
    ],
    # covered porch on the pátio side (facade direction C): roof on two bronze posts, cedar ceiling. It runs
    # along the living room and flex room only (22 ft), which keeps the 50-ft trios under the impervious cap.
    porch=dict(rect=(20.0, 0.0, 27.75, 22.0), roof=(20.0, -1.0, 28.0, 23.0), posts=[(27.45, 0.25), (27.45, 21.75)]),
    calcada=[(13.0, -3.0, 17.0, 0.0)],                                 # calçada stoop at the front door, 12 sf
    enclosed=W3 * D3,
)


def stone_runs(plan):
    """The stone-clad stretches of exterior wall in a plan, in the home's frame. Each run: a (start point),
    u (unit direction), n (unit normal into the house), L (length) and holes: the openings of the wall it lies on,
    as (s0, s1, opening) measured along the run. Used by the drawings, the AutoCAD file and the renders."""
    import math
    runs = []
    for a, b in plan.get("stone", {}).get("walls", []):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-u[1], u[0])
        holes = []
        for w in plan["walls"]:
            if not w["ext"]:
                continue
            (wx0, wy0), (wx1, wy1) = w["a"], w["b"]
            on = all(abs((px - a[0]) * u[1] - (py - a[1]) * u[0]) < 1e-6 for px, py in ((wx0, wy0), (wx1, wy1)))
            if not on:
                continue
            WL = math.hypot(wx1 - wx0, wy1 - wy0)
            wu = ((wx1 - wx0) / WL, (wy1 - wy0) / WL)
            for o in w["openings"]:
                pts = [(wx0 + wu[0] * q, wy0 + wu[1] * q) for q in (o["off"], o["off"] + o["w"])]
                ts = sorted((px - a[0]) * u[0] + (py - a[1]) * u[1] for px, py in pts)
                if ts[1] > 0 and ts[0] < L:
                    holes.append((max(ts[0], 0.0), min(ts[1], L), o))
        runs.append(dict(a=a, b=b, u=u, n=n, L=L, holes=sorted(holes, key=lambda h: h[0])))
    return runs


def area_summary():
    gf_c, gf_s, up = CASA02_GF_CARPORT["enclosed"], CASA02_GF_SUITE["enclosed"], CASA02_UPPER["enclosed"]
    return dict(carport_total=gf_c + up, suite_total=gf_s + up, carport_gf=gf_c, suite_gf=gf_s, upper=up,
                casita=CASITA["enclosed"])
