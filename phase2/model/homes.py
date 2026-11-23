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
W2, D2 = 20.0, 39.0
BAY = (0.0, 0.0, 10.5, 20.0)          # flex bay at the front corner (car comes straight in)

# the service column (entry, WC, pantry, stair) shared by both ground floors
SERVICE_PARTS = [
    part((10.5, 6.0), (16.5, 6.0), door(1.0, 2.5, "L", "s")),       # entry | WC
    part((10.5, 11.0), (16.5, 11.0)),                                 # WC | pantry + mechanical
    part((16.5, 6.0), (16.5, 20.0)),                                  # stair wall (cedar slats above the handrail)
    part((10.5, 20.0), (16.5, 20.0), door(3.5, 2.5, "R", "e")),      # pantry | kitchen
]
SERVICE_ROOMS = [
    dict(name="Entry", rect=(10.5, 0.0, 16.5, 6.0)),
    dict(name="WC", rect=(10.5, 6.0, 16.5, 11.0), lab=(15.2, 7.3)),
    dict(name="Pantry + mech", rect=(10.5, 11.0, 16.5, 20.0), short="Pantry"),
    dict(name="Kitchen", rect=(0.0, 20.0, 20.0, 27.0), lab=(16.4, 24.6)),
    dict(name="Living + dining", rect=(0.0, 27.0, 20.0, 39.0), lab=(14.6, 30.4)),
]
STAIR = dict(rect=(16.5, 6.0, 20.0, 19.5), up=True)   # 16 treads at 10 in, 17 risers at about 7 in
BACK_GLASS = {2: [slider(2.0, 16.0)]}                 # back wall: 16 ft slider to the pátio
EAST_GLASS = [slider(28.0, 8.0)]                       # long wall, where the pátio is at the side
KITCHEN_FIX = [
    dict(kind="counter", rect=(0.5, 20.4, 10.4, 22.4)),
    dict(kind="range", rect=(3.0, 20.4, 5.5, 22.4)),
    dict(kind="sink", rect=(7.0, 20.6, 9.0, 22.2)),
    dict(kind="fridge", rect=(10.6, 20.4, 13.2, 22.9)),
    dict(kind="island", rect=(4.0, 24.0, 12.0, 26.6)),
    dict(kind="table", rect=(2.5, 29.0, 9.5, 32.5)),
    dict(kind="sofa", rect=(11.0, 34.0, 18.5, 37.0)),
    dict(kind="wc", at=(14.9, 10.55), rot=180),
    dict(kind="lav", rect=(10.9, 9.3, 12.6, 10.8)),
]

CASA02_GF_CARPORT = dict(
    name="Casa 02 · ground floor, carport", W=W2, D=D2,
    walls=loop([(10.5, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0), (0.0, 20.0), (10.5, 20.0)],
               {0: [door(1.0, 3.0, "L", "s"), win(6.25, 2.5, "slot")],
                1: EAST_GLASS, 2: BACK_GLASS[2], 3: [win(5.0, 6.0, "sill 3'-6\"")],
                5: [door(15.0, 3.0, "L", "e")]}) + SERVICE_PARTS,
    rooms=SERVICE_ROOMS + [dict(name="Carport", rect=BAY, outdoor=True, note="open bay · cedar gate option")],
    fixtures=KITCHEN_FIX + [dict(kind="car", rect=(2.15, 2.0, 8.35, 17.5))],
    stair=STAIR,
    columns=[(0.35, 0.35), (0.35, 10.0)],
    gate=((0.0, 0.0), (10.5, 0.0)),
    enclosed=W2 * D2 - (BAY[2] - BAY[0]) * (BAY[3] - BAY[1]),
)

CASA02_GF_SUITE = dict(
    name="Casa 02 · ground floor, suite", W=W2, D=D2,
    walls=loop([(0.0, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0)],
               {0: [win(2.25, 5.0, "egress"), door(11.5, 3.0, "L", "s"), win(16.75, 2.5, "slot")],
                1: EAST_GLASS, 2: BACK_GLASS[2],
                3: [win(5.0, 6.0, "sill 3'-6\""), win(22.0, 3.0, "high"), win(29.5, 4.0, "fluted below 5'")]})
    + SERVICE_PARTS + [
        part((10.5, 20.0), (10.5, 0.0), door(15.0, 3.0, "R", "e")),    # suite door off the entry
        part((0.0, 12.5), (10.5, 12.5), door(6.75, 2.5, "L", "s")),     # bedroom | bath
        part((0.0, 20.0), (10.5, 20.0)),                                # bath | kitchen
    ],
    rooms=[dict(name="Suite bedroom", rect=(0.0, 0.0, 10.5, 12.5), short="Bedroom", lab=(5.25, 2.9)),
           dict(name="Suite bath", rect=(0.0, 12.5, 10.5, 20.0), short="Bath", lab=(3.4, 14.3))] + SERVICE_ROOMS,
    fixtures=KITCHEN_FIX + [
        dict(kind="bed", rect=(2.75, 5.6, 7.75, 12.3)),
        dict(kind="shower", rect=(0.5, 16.0, 4.5, 19.6)),
        dict(kind="wc", at=(5.9, 19.5), rot=180),
        dict(kind="lav", rect=(7.6, 17.9, 10.1, 19.6)),
    ],
    stair=STAIR,
    enclosed=W2 * D2,
)

CASA02_UPPER = dict(
    name="Casa 02 · upper floor", W=W2, D=D2,
    walls=loop([(0.0, 0.0), (20.0, 0.0), (20.0, 39.0), (0.0, 39.0)],
               {0: [win(2.0, 6.0, "egress"), win(14.0, 3.0, "high")],
                1: [win(20.5, 2.0, "slot, cedar slats"), win(33.0, 3.0, "high")],
                2: [win(10.0, 9.0, "to the pátio, cedar-screened")],
                3: [win(19.0, 5.0, "egress, fluted below 5'"), win(30.0, 4.0, "high")]})
    + [
        part((10.5, 0.0), (10.5, 24.0), door(8.25, 2.67, "L", "s"), door(13.5, 2.67, "L", "s")),
        part((0.0, 12.0), (10.5, 12.0)),
        part((10.5, 6.0), (20.0, 6.0), door(0.25, 2.5, "R", "s")),
        part((16.5, 6.0), (16.5, 19.5)),
        part((13.5, 6.0), (13.5, 19.5), door(1.25, 2.5, "L", "s"), door(8.25, 2.0, "L", "s")),
        part((13.5, 11.0), (16.5, 11.0)),
        part((0.0, 24.0), (20.0, 24.0), door(10.75, 2.67, "L", "e")),
        part((13.5, 24.0), (13.5, 39.0), door(1.25, 2.5, "R", "s"), door(7.75, 2.5, "R", "s")),
        part((13.5, 30.0), (20.0, 30.0)),
    ],
    rooms=[dict(name="Bed 2", rect=(0.0, 0.0, 10.5, 12.0), lab=(5.25, 9.9)),
           dict(name="Bed 3 / den", rect=(0.0, 12.0, 10.5, 24.0), short="Bed 3", lab=(5.25, 21.9)),
           dict(name="Bath 2", rect=(10.5, 0.0, 20.0, 6.0), short="Bath", lab=(14.6, 4.5)),
           dict(name="Hall", rect=(10.5, 6.0, 13.5, 24.0), label=False),
           dict(name="W/D", rect=(13.5, 6.0, 16.5, 11.0), label=False),
           dict(name="Linen", rect=(13.5, 11.0, 16.5, 19.5), label=False),
           dict(name="Primary", rect=(0.0, 24.0, 13.5, 39.0), lab=(6.5, 27.2)),
           dict(name="Closet", rect=(13.5, 24.0, 20.0, 30.0)),
           dict(name="Primary bath", rect=(13.5, 30.0, 20.0, 39.0), short="Bath", lab=(15.4, 32.3))],
    fixtures=[
        dict(kind="bed", rect=(2.75, 1.0, 7.75, 7.7)),
        dict(kind="bed", rect=(2.75, 13.0, 7.75, 19.7)),
        dict(kind="bed", rect=(3.25, 30.5, 9.75, 37.5)),
        dict(kind="shower", rect=(17.0, 0.5, 19.6, 5.6)),
        dict(kind="wc", at=(14.5, 0.85), rot=0),
        dict(kind="lav", rect=(11.0, 0.5, 12.9, 2.3)),
        dict(kind="wd", rect=(13.8, 6.4, 16.2, 10.6)),
        dict(kind="shower", rect=(16.2, 35.0, 19.6, 38.6)),
        dict(kind="wc", at=(14.6, 38.2), rot=180),
        dict(kind="lav", rect=(17.9, 30.5, 19.6, 34.2)),
    ],
    stair=dict(rect=(16.5, 6.0, 20.0, 19.5), up=False),
    void=(16.5, 6.0, 20.0, 19.5),
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
    enclosed=W3 * D3,
)


def area_summary():
    gf_c, gf_s, up = CASA02_GF_CARPORT["enclosed"], CASA02_GF_SUITE["enclosed"], CASA02_UPPER["enclosed"]
    return dict(carport_total=gf_c + up, suite_total=gf_s + up, carport_gf=gf_c, suite_gf=gf_s, upper=up,
                casita=CASITA["enclosed"])
