"""
Casa 01 / Casa Pátio — single source of truth for the concept design.

Every drawing (plans, elevations, section) and every 3D render is generated
from the numbers in this file, so the visuals always agree with the plans.

Units: feet. Origin: south-west corner of the lot. +x = east, +y = north,
z = height above average grade. Street is on the SOUTH (y < 0).

Concept: an L-shaped, single-story house wrapped around a private entry
courtyard. One long horizontal roof plate ties the street facade together.
Street side: a Texas limestone wall + a full-height cobogó screen.
Rear: a deep cedar-lined veranda facing a heritage live oak.

V2 (in review, Nov 2026): living bar +4 ft east for a larger great room; one-car carport at the
front-east under the same roof behind a sliding cedar gate; one L-shaped courtyard that wraps
behind the carport; bedroom wing 2 ft narrower to keep the courtyard wide; Bath 2 re-planned,
stock-size sliders, two skylights, HVAC (1 outdoor unit + 2 concealed air handlers),
water heater in the laundry, door swings cleared. V1 is in git history.
"""

# --------------------------------------------------------------------------
# Lot & zoning (typical central-Austin SF-3 infill lot)
# --------------------------------------------------------------------------
LOT_W = 65.0
LOT_D = 125.0
SETBACK_FRONT = 25.0
SETBACK_SIDE = 5.0
SETBACK_REAR = 10.0

# Right-of-way south of the lot line (y < 0)
SIDEWALK = (-5.0, -0.5)        # y range
PARKWAY = (-11.0, -5.0)
CURB_Y = -11.0

# --------------------------------------------------------------------------
# Vertical datums (ft above grade)
# --------------------------------------------------------------------------
GRADE = 0.0
FF = 1.0                 # finished floor (slab on grade)
HARDSCAPE = 0.85         # courtyard / veranda paving, 2" below FF
CEIL = FF + 10.0         # 10'-0" ceilings everywhere, = exterior soffit
HEAD = FF + 9.0          # head height of large openings
FASCIA_BOT = CEIL        # soffit and ceiling are one continuous plane
FASCIA_TOP = CEIL + 1.25  # 15" thin roof edge (low-slope roof behind)

EXT_T = 0.5              # exterior wall (2x6 + finishes)
INT_T = 0.375            # interior partition (2x4 + gyp)
VENEER_T = 0.33          # limestone veneer thickness incl. air gap

# --------------------------------------------------------------------------
# Building footprint (outer face of exterior walls), CCW, interior on left
# --------------------------------------------------------------------------
FOOTPRINT = [(6, 30), (26, 30), (26, 60), (58, 60), (58, 80), (6, 80)]
WING = dict(x0=6, x1=26, y0=30, y1=60)     # bedroom wing (V2: 2 ft narrower)
BAR = dict(x0=6, x1=58, y0=60, y1=80)      # living bar (V2: +4 ft east)
COURTYARD = dict(x0=26, x1=48.5, y0=30, y1=60)   # main rectangle; V2 adds an ell behind the carport (OUTDOOR)

# --------------------------------------------------------------------------
# Exterior walls: outer-face line a->b, thickness to the LEFT (inside).
# Openings: offset from a along the wall, width, sill & head above FF.
# kind: fixed | casement | slider | pivot | door
# --------------------------------------------------------------------------
EXT_WALLS = [
    dict(id="S-wing", a=(6, 30), b=(26, 30), finish="limestone", openings=[
        dict(kind="fixed", off=2.5, w=2.0, sill=1.0, head=9.0, name="Bed 2 slot window"),
    ]),
    dict(id="E-gallery", a=(26, 30), b=(26, 60), finish="stucco", openings=[
        dict(kind="pivot", off=1.25, w=4.0, sill=0.0, head=9.0, name="Front door (cedar pivot)"),
        dict(kind="slider", off=5.75, w=23.75, sill=0.0, head=9.0, panels=5,
             name="Gallery glass wall"),
    ]),
    dict(id="S-bar", a=(26, 60), b=(58, 60), finish="stucco", openings=[
        dict(kind="slider", off=3.75, w=12.0, sill=0.0, head=9.0, panels=3,
             name="Great room to courtyard"),                       # stock 12' 3-panel
        dict(kind="fixed", off=18.0, w=4.0, sill=1.5, head=9.0, name="Primary bedroom window"),
        dict(kind="slider", off=23.25, w=8.0, sill=0.0, head=9.0, panels=2,
             name="Primary bedroom to courtyard"),                  # stock 8' 2-panel, onto the courtyard ell
    ]),
    dict(id="E-bar", a=(58, 60), b=(58, 80), finish="stucco", openings=[
        dict(kind="casement", off=3.0, w=3.0, sill=3.0, head=9.0, name="Primary bedroom east"),
        dict(kind="fixed", off=16.9, w=2.3, sill=3.6, head=9.0, name="Shower garden window"),
    ]),
    dict(id="N-bar", a=(58, 80), b=(6, 80), finish="stucco", openings=[
        dict(kind="fixed", off=1.5, w=5.5, sill=6.0, head=9.0, name="Primary bath clerestory"),
        dict(kind="slider", off=18.0, w=16.0, sill=0.0, head=9.0, panels=4,
             name="Great room to veranda"),                         # stock 16' 4-panel (was 18')
        dict(kind="fixed", off=40.0, w=8.0, sill=3.6, head=9.0, name="Kitchen window"),
    ]),
    dict(id="W", a=(6, 80), b=(6, 30), finish="stucco", openings=[
        dict(kind="casement", off=24.0, w=4.0, sill=2.5, head=9.0, name="Bed 3 window"),
        dict(kind="casement", off=42.0, w=4.0, sill=2.5, head=9.0, name="Bed 2 window"),
    ]),
]

# Limestone feature plane: slides past the west wall like a free-standing fin
LIMESTONE_WALL = dict(x0=4.5, x1=26.0, y_face=30.0 - VENEER_T, y_back=30.0,
                      z0=GRADE, z1=CEIL)

# --------------------------------------------------------------------------
# Interior partitions: centerline a->b. Openings as offset/width along line.
# --------------------------------------------------------------------------
PARTITIONS = [
    # Bedroom wing
    dict(a=(21.0, 30.5), b=(21.0, 60.0), openings=[       # gallery wall
        dict(off=8.0, w=2.67, kind="door", name="Bed 2"),            # V2: clear of the bed
        dict(off=13.0, w=2.67, kind="door", name="Bath"),
        dict(off=18.5, w=2.67, kind="door", name="Bed 3"),           # V2: clear of the bed
    ]),
    dict(a=(6.5, 41.5), b=(21.0, 41.5), openings=[dict(off=1.5, w=4.0, kind="closet")]),
    dict(a=(6.5, 48.5), b=(21.0, 48.5), openings=[dict(off=1.5, w=4.0, kind="closet")]),
    dict(a=(13.0, 41.5), b=(13.0, 48.5), openings=[]),
    dict(a=(6.5, 45.0), b=(13.0, 45.0), openings=[]),
    # Bed 3 / kitchen
    dict(a=(6.5, 60.0), b=(21.19, 60.0), openings=[]),
    # Laundry + mechanical
    dict(a=(13.0, 60.0), b=(13.0, 65.5), openings=[dict(off=1.5, w=2.67, kind="door", name="Laundry", swing=-1)]),
    dict(a=(6.5, 65.5), b=(13.0, 65.5), openings=[]),
    # Primary suite
    dict(a=(43.0, 60.5), b=(43.0, 79.5), openings=[dict(off=1.0, w=2.67, kind="door", name="Primary", swing=-1)]),
    dict(a=(43.0, 71.5), b=(57.5, 71.5), openings=[
        dict(off=1.25, w=2.5, kind="door", name="WIC"),
        dict(off=8.5, w=2.5, kind="door", name="Primary bath"),      # V2: clear of the vanity
    ]),
    dict(a=(49.5, 71.5), b=(49.5, 79.5), openings=[]),
]

# --------------------------------------------------------------------------
# Rooms (interior clear polygons) for labels & area schedule
# --------------------------------------------------------------------------
ROOMS = [
    dict(name="Living", poly=[(29.0, 60.5), (42.8, 60.5), (42.8, 79.5), (29.0, 79.5)], label=(36.0, 64.6)),
    dict(name="Dining", poly=[(19.0, 60.2), (29.0, 60.2), (29.0, 79.5), (19.0, 79.5)], label=(24.0, 64.6), show_area=False),
    dict(name="Kitchen", poly=[(6.5, 65.7), (19.0, 65.7), (19.0, 79.5), (6.5, 79.5)], label=(13.5, 67.6)),
    dict(name="Laundry", poly=[(6.5, 60.2), (12.8, 60.2), (12.8, 65.3), (6.5, 65.3)], label=(9.7, 63.3), small=True),
    dict(name="Primary Bedroom", poly=[(43.2, 60.5), (57.5, 60.5), (57.5, 71.3), (43.2, 71.3)], label=(47.6, 68.6)),
    dict(name="Walk-in", poly=[(43.2, 71.7), (49.3, 71.7), (49.3, 79.5), (43.2, 79.5)], label=(46.2, 78.0), small=True),
    dict(name="Primary Bath", poly=[(49.7, 71.7), (57.5, 71.7), (57.5, 79.5), (49.7, 79.5)], label=(54.5, 75.0), small=True),
    dict(name="Bedroom 3", poly=[(6.5, 48.7), (20.8, 48.7), (20.8, 59.8), (6.5, 59.8)], label=(13.6, 55.6)),
    dict(name="Bath 2", poly=[(13.2, 41.7), (20.8, 41.7), (20.8, 48.3), (13.2, 48.3)], label=(17.0, 45.0), small=True),
    dict(name="Cl.", poly=[(6.5, 41.7), (12.8, 41.7), (12.8, 44.8), (6.5, 44.8)], label=(9.7, 43.3), small=True, show_area=False),
    dict(name="Cl.", poly=[(6.5, 45.2), (12.8, 45.2), (12.8, 48.3), (6.5, 48.3)], label=(9.7, 46.8), small=True, show_area=False),
    dict(name="Bedroom 2", poly=[(6.5, 30.5), (20.8, 30.5), (20.8, 41.3), (6.5, 41.3)], label=(13.6, 34.6)),
    dict(name="Gallery", poly=[(21.2, 30.5), (25.5, 30.5), (25.5, 60.2), (21.2, 60.2)], label=(23.35, 47.0), vertical=True),
]

OUTDOOR = [
    dict(name="Pátio (courtyard)", poly=[(26, 36), (48.5, 36), (48.5, 50), (58, 50), (58, 60), (26, 60)],
         label=(37.2, 39.0)),                                    # V2: one L-shaped courtyard
    dict(name="Covered entry", poly=[(26, 30.33), (48.5, 30.33), (48.5, 36), (26, 36)], label=(43.3, 33.2)),
    dict(name="Veranda", poly=[(18, 80), (41, 80), (41, 92), (18, 92)], label=(31.0, 90.6)),
    dict(name="Carport", poly=[(48.5, 30), (59.5, 30), (59.5, 50), (48.5, 50)], label=(54.0, 48.5)),
]

# --------------------------------------------------------------------------
# Roof: one continuous thin plate (low slope 1/4":12" to scuppers on north)
# --------------------------------------------------------------------------
# V2: the plate runs on over the carport; the courtyard and the primary garden stay open to the sky
ROOF = [(3, 27), (60, 27), (60, 50), (48, 50), (48, 36), (29, 36), (29, 56), (60, 56), (60, 83),
        (43, 83), (43, 92.5), (16, 92.5), (16, 83), (3, 83)]

# Soffit zones finished in cedar tongue & groove (the rest: smooth white)
CEDAR_SOFFITS = [
    dict(name="Entry canopy", x0=26.0, x1=60.0, y0=27.0, y1=36.0, dir="y"),   # street edge, over the carport too
    dict(name="Gallery eave", x0=26.0, x1=29.0, y0=36.0, y1=56.0, dir="y"),
    dict(name="Courtyard eave", x0=26.0, x1=60.0, y0=56.0, y1=60.0, dir="y"),
    dict(name="Veranda", x0=16.0, x1=43.0, y0=80.0, y1=92.5, dir="y"),
]
# Interior ceilings in cedar (continuous with the soffits outside). V2: great room only;
# bedrooms, gallery and baths are painted gypsum (tracker P1-24)
CEDAR_CEILINGS = [
    dict(name="Great room", x0=6.5, x1=42.81, y0=60.19, y1=79.5, dir="y"),
]

# Entry feature: monochrome black calçada portuguesa under the canopy, inside the gate,
# framed by a 6" band of smooth light concrete (about 50 sf of mosaic). Shaded, so the
# dark stone stays comfortable in summer; the pátio and veranda keep light limestone.
ENTRY_MOSAIC = dict(x0=26.0, x1=38.0, y0=30.4, y1=36.0, band=0.5)

# Slender steel posts (4" square, dark bronze)
POSTS = [(48.75, 31.2), (59.25, 31.2), (48.75, 49.6), (59.25, 49.6), (18.4, 91.6), (40.6, 91.6)]  # carport + veranda

# --------------------------------------------------------------------------
# Signature screens
# --------------------------------------------------------------------------
BLOCK = 1.0  # 12" x 12" x 4" precast concrete breeze block
COBOGO = dict(x0=31.0, x1=48.0, y=30.0, t=0.33, z0=FF, z1=CEIL,    # V2: 17 blocks wide (V1: 21)
              base=(GRADE, FF))   # cast concrete curb under the blocks
ENTRY_GATE = dict(x0=26.5, x1=30.5, y=30.0, z0=HARDSCAPE, z1=CEIL)  # cedar slat pivot gate
CEDAR_SCREEN = dict(x=48.5, y0=30.33, y1=50.0, z0=HARDSCAPE, z1=CEIL,       # V2: carport | courtyard
                    slat_w=1.5 / 12, slat_d=3.5 / 12, gap=2.0 / 12,
                    openings=[(31.0, 34.5)])                    # V2: gate from the carport to the entry
CARPORT = dict(x0=48.5, x1=59.5, y0=30.0, y1=50.0)            # one car, open to the street, under the roof
CARPORT_GATE = dict(x=48.5, y0=31.0, y1=34.5, z0=HARDSCAPE, z1=CEIL)
# Other cedar slat screens (same slats as CEDAR_SCREEN): carport | courtyard ell, and the ell's
# east edge to the side yard, which brings morning light into the courtyard
SLAT_SCREENS = [dict(name="Carport north", axis="x", y=50.0, x0=48.5, x1=59.5),
                dict(name="Courtyard east", axis="y", x=58.0, y0=50.0, y1=60.0)]
# Motorized sliding cedar gate across the carport; when open it parks behind the cobogó
CARPORT_SLIDER = dict(x0=48.5, x1=59.5, y=30.55, park_x0=37.5, z0=HARDSCAPE, z1=CEIL)

# --------------------------------------------------------------------------
# Furniture & fixtures (plan symbols + 3D). x,y = center; w along x, d along y
# --------------------------------------------------------------------------
FURNITURE = [
    # Kitchen
    dict(t="counter", x=7.75, y=74.25, w=2.5, d=10.5),     # west run (range)
    dict(t="counter", x=13.3, y=78.25, w=9.4, d=2.5),     # north run under window (sink)
    dict(t="tall", x=7.75, y=67.35, w=2.5, d=3.3),        # fridge + pantry column
    dict(t="island", x=13.6, y=71.6, w=8.0, d=3.5),
    dict(t="stool", x=11.3, y=69.2), dict(t="stool", x=13.6, y=69.2), dict(t="stool", x=15.9, y=69.2),
    # Dining (V2: table turned to run north-south, so the living area gets its own space)
    dict(t="dining_table", x=24.0, y=71.0, w=3.4, d=7.0, chairs=6),
    dict(t="pendant", x=24.0, y=71.0),
    # Living (V2: about 14 ft wide)
    dict(t="rug", x=36.4, y=70.0, w=10.0, d=12.0),
    dict(t="sofa", x=41.0, y=70.0, w=3.2, d=8.5, face="w"),
    dict(t="coffee_table", x=36.8, y=70.0, w=2.6, d=4.2),
    dict(t="lounge_chair", x=32.4, y=67.6, face="e"),
    dict(t="lounge_chair", x=32.4, y=72.4, face="e"),
    # Primary
    dict(t="bed", x=54.3, y=66.0, w=6.8, d=6.3, face="w", size="king"),
    dict(t="nightstand", x=56.8, y=62.0), dict(t="nightstand", x=56.8, y=70.0),
    # primary bath: see PRIMARY_BATH below (walk-in wet room, floating vanity, wall-hung wc)
    dict(t="wc_wall", x=57.0, y=73.2, face="w"),
    # Bedroom 2 & 3
    dict(t="bed", x=17.3, y=36.0, w=7.0, d=5.0, face="w", size="queen"),
    dict(t="desk", x=8.0, y=36.0, w=2.0, d=4.5),
    dict(t="bed", x=17.3, y=55.0, w=7.0, d=5.0, face="w", size="queen"),
    dict(t="desk", x=8.0, y=55.0, w=2.0, d=4.5),
    # Bath 2 (V2): tub/shower on the far wall, vanity + toilet on the long walls, door swing clear
    dict(t="tub", x=14.55, y=44.2, w=2.67, d=5.0, face="n"),
    dict(t="vanity", x=17.9, y=47.42, w=3.0, d=1.75),
    dict(t="wc", x=17.4, y=42.75, face="n"),
    # Laundry (V2): stacked washer/dryer + heat-pump water heater; door swings out
    dict(t="washer", x=7.8, y=61.35, label="W/D"), dict(t="wh", x=10.4, y=61.25),
    # Veranda
    dict(t="grill_counter", x=19.75, y=85.2, w=2.5, d=7.5),
    dict(t="outdoor_table", x=27.6, y=86.2, w=8.0, d=3.5, chairs=8),
    dict(t="planter", x=39.6, y=81.4), dict(t="planter", x=17.3, y=91.2),
    dict(t="credenza", x=18.3, y=61.0, w=5.0, d=1.5),   # clear of the gallery opening and laundry door
    # rear yard: a pair of lounge chairs on the lawn under the heritage oak
    dict(t="lounge_chair", x=24.5, y=101.5, face="s"),
    dict(t="lounge_chair", x=28.5, y=101.0, face="s"),
    dict(t="side_table", x=26.5, y=100.3),
    dict(t="fan", x=27.6, y=86.2), dict(t="fan", x=36.6, y=86.2),
]

# --------------------------------------------------------------------------
# Primary bathroom (7'-10" x 7'-10"): a Brazilian spa-style wet room
# --------------------------------------------------------------------------
PRIMARY_BATH = dict(
    room=(49.69, 71.69, 57.5, 79.5),              # x0, y0, x1, y1 (clear)  (V2: +4 ft east)
    shower=(49.69, 76.5, 57.5, 79.5),             # full-width walk-in along the north wall
    glass=(49.69, 54.4, 76.5),                    # fixed glass panel x0..x1 at y; entry 54.4..57.5
    rain_head=(51.4, 78.0),
    bench=(49.69, 76.6, 51.0, 79.4),              # floating limestone bench at the west end
    vanity=(49.69, 72.2, 51.45, 76.2),            # floating rift-oak vanity on the west wall
    sink=(50.55, 74.2), mirror=(74.2, 2.4),       # vessel sink; round mirror center y, diameter
    sconces=(72.85, 75.55),
    plant=(56.8, 75.5),
)
BATH_FINISHES = [
    ("Floor", "Ladrilho hidráulico", "8x8 cement-look porcelain, terracotta / bone / green"),
    ("Shower walls", "Azulejo / zellige", "2.5x8 zellige-look glazed porcelain, green, floor to ceiling"),
    ("Vanity", "Tauari / freijó", "Floating rift white oak, honed limestone top, vessel sink"),
    ("Fixtures", "Metais dourados", "Brushed brass rain head, wall faucet, round mirror, sconces"),
    ("Ceiling", "Forro branco", "Painted moisture-resistant gypsum, warm white (cedar kept for the great room)"),
]

# --------------------------------------------------------------------------
# Site & landscape
# --------------------------------------------------------------------------
TREES = [
    dict(kind="live_oak", x=31.0, y=110.0, h=38, spread=58, seed=7, note="Heritage live oak (protected), house is set back to save it"),
    dict(kind="live_oak", x=44.0, y=46.5, h=24, spread=22, seed=3, crown=0.42, leaf=0.75,
         note="Courtyard tree (Monterrey or live oak), limbed up to ~9 ft"),
    dict(kind="live_oak", x=-3.0, y=6.0, h=28, spread=34, seed=11, note="Front yard live oak (lot corner)"),
    dict(kind="live_oak", x=40.0, y=-8.0, h=24, spread=28, seed=19,
         note="Street tree, in front of the cobogó; V2 moved it 18 ft west, clear of the drive"),
]

PATHS = [
    # stepping slabs from the sidewalk to the gate (3' x 1.5' limestone)
    dict(kind="steps", x=28.5, y0=0.0, y1=29.5, w=3.0, d=1.5, gap=1.0),
]
# Ribbon drive into the carport (east side, beside — not in front of — the cobogó)
DRIVEWAY = dict(strips=[(50.5, 52.5), (55.5, 57.5)], y0=CURB_Y, y1=30.0)

PLANTING = [
    dict(name="Front meadow", poly=[(0.5, 0.5), (27.0, 0.5), (27.0, 27.0), (0.5, 27.0)]),
    dict(name="Front meadow E", poly=[(30.0, 0.5), (49.5, 0.5), (49.5, 26.5), (30.0, 26.5)]),
    dict(name="Courtyard garden", poly=[(29.5, 36.5), (48.0, 36.5), (48.0, 50.5), (57.5, 50.5), (57.5, 55.5),
                                        (42.5, 55.5), (42.5, 52.0), (29.5, 52.0)]),
    dict(name="Rear meadow", poly=[(0.5, 93.5), (64.5, 93.5), (64.5, 124.5), (0.5, 124.5)]),
]

# V2 skylights (low-slope roof): daylight for the windowless Bath 2 and the walk-in closet
SKYLIGHTS = [dict(name="Bath 2", rect=(15.9, 44.0, 19.9, 46.0)),
             dict(name="Walk-in", rect=(45.25, 74.6, 47.25, 76.6))]

# V2 HVAC (tracker P1-32, option A): one variable-speed outdoor heat pump on a pad in the west
# side yard, two concealed ducted air handlers in dropped ceilings; living spaces keep 10 ft
HVAC = dict(pad=(1.2, 61.0, 4.4, 64.6),
            ahu=[dict(name="AHU-1", serves="kitchen, great room, bedroom wing", at=(9.7, 64.85)),
                 dict(name="AHU-2", serves="primary suite", at=(48.05, 73.3))],
            dropped=[dict(name="Laundry", rect=(6.5, 60.2, 12.8, 65.3)),
                     dict(name="Walk-in", rect=(43.2, 71.7, 49.3, 79.5)),
                     dict(name="Bath 2", rect=(13.2, 41.7, 20.8, 48.3)),
                     dict(name="Closets", rect=(6.5, 41.7, 12.8, 48.3))],
            dropped_height="8'-6\"")

# Hard paving shown on the plans
PAVING = [dict(name="Covered entry", rect=(26.0, 30.33, 48.2, 36.0)),
          dict(name="Gallery walk", rect=(26.0, 36.0, 29.5, 60.0)),
          dict(name="Great room terrace", rect=(29.5, 52.0, 42.5, 60.0)),
          dict(name="Courtyard ell terrace", rect=(42.5, 55.5, 58.0, 60.0)),
          dict(name="Veranda", rect=(16.5, 80.0, 42.5, 92.5))]

FENCE_H = 6.0  # horizontal-slat cedar fence on side & rear lot lines
FENCES = [((0.0, 30.0), (0.0, 125.0)), ((0.0, 125.0), (65.0, 125.0)), ((65.0, 125.0), (65.0, 30.0))]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def poly_area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def conditioned_area():
    return poly_area(FOOTPRINT)


def area_schedule():
    return dict(
        conditioned=conditioned_area(),
        veranda=poly_area(OUTDOOR[2]["poly"]),
        courtyard=poly_area(OUTDOOR[0]["poly"]) + poly_area(OUTDOOR[1]["poly"]),
        covered_entry=poly_area(OUTDOOR[1]["poly"]),
        roof=poly_area(ROOF),
        carport=poly_area(OUTDOOR[3]["poly"]),
        lot=LOT_W * LOT_D,
    )


FINISHES = [
    # (element, Brazilian reference, Austin specification)
    ("Feature wall", "Pedra São Tomé / moledo", "Lueders buff limestone, sawn-face ashlar, 3 course heights"),
    ("Courtyard screen", "Cobogó (Recife, 1929)", "12x12x4 precast concrete breeze block, white cement, circle pattern"),
    ("Exterior walls", "White mineral plaster", "Smooth 3-coat stucco, warm white, sand finish"),
    ("Roof edge", "Thin concrete slab edge", "15\" dark bronze aluminum fascia, low-slope TPO roof behind"),
    ("Soffits & great room ceiling", "Freijó / tauari ceiling", "Clear western red cedar T&G 1x6, natural oil (great room, veranda, street + courtyard soffits)"),
    ("Screens & gate", "Muxarabi / brise-soleil", "Cedar 2x4 slats @ 5\" o.c. on steel frame"),
    ("Windows & doors", "Slim steel frames", "Dark bronze thermally broken aluminum, stock-size 9' sliders, low-E"),
    ("Floors (inside)", "Cimento queimado", "Polished, sealed concrete slab, warm gray"),
    ("Floors (outside)", "Pedra São Tomé paving", "Lueders limestone pavers 24x36, thermal finish"),
    ("Entry paving", "Calçada portuguesa (black)", "50 sf black basalt mosaic or Techo-Bloc Antika Onyx Black, light concrete band"),
    ("Kitchen", "Dark stone + light wood", "Rift white oak cabinets, honed black granite, green glazed tile"),
    ("Landscape", "Tropical garden", "Live oak, dwarf palmetto, agave, sotol, muhly grass, decomposed granite"),
]


if __name__ == "__main__":
    import json
    print(json.dumps(area_schedule(), indent=2))
    for r in ROOMS:
        print(f"{r['name']:<18}{poly_area(r['poly']):7.0f} sf")
