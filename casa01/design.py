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
FOOTPRINT = [(6, 30), (28, 30), (28, 60), (54, 60), (54, 80), (6, 80)]
WING = dict(x0=6, x1=28, y0=30, y1=60)     # bedroom wing
BAR = dict(x0=6, x1=54, y0=60, y1=80)      # living bar
COURTYARD = dict(x0=28, x1=54, y0=30, y1=60)

# --------------------------------------------------------------------------
# Exterior walls: outer-face line a->b, thickness to the LEFT (inside).
# Openings: offset from a along the wall, width, sill & head above FF.
# kind: fixed | casement | slider | pivot | door
# --------------------------------------------------------------------------
EXT_WALLS = [
    dict(id="S-wing", a=(6, 30), b=(28, 30), finish="limestone", openings=[
        dict(kind="fixed", off=2.5, w=2.0, sill=1.0, head=9.0, name="Bed 2 slot window"),
    ]),
    dict(id="E-gallery", a=(28, 30), b=(28, 60), finish="stucco", openings=[
        dict(kind="pivot", off=1.25, w=4.0, sill=0.0, head=9.0, name="Front door (cedar pivot)"),
        dict(kind="slider", off=5.75, w=23.75, sill=0.0, head=9.0, panels=5,
             name="Gallery glass wall"),
    ]),
    dict(id="S-bar", a=(28, 60), b=(54, 60), finish="stucco", openings=[
        dict(kind="slider", off=0.75, w=9.5, sill=0.0, head=9.0, panels=3,
             name="Great room to courtyard"),
        dict(kind="slider", off=15.0, w=7.0, sill=0.0, head=9.0, panels=2,
             name="Primary bedroom to courtyard"),
    ]),
    dict(id="E-bar", a=(54, 60), b=(54, 80), finish="stucco", openings=[
        dict(kind="casement", off=3.0, w=3.0, sill=3.0, head=9.0, name="Primary bedroom east"),
        dict(kind="fixed", off=16.9, w=2.3, sill=3.6, head=9.0, name="Shower garden window"),
    ]),
    dict(id="N-bar", a=(54, 80), b=(6, 80), finish="stucco", openings=[
        dict(kind="fixed", off=1.5, w=5.5, sill=6.0, head=9.0, name="Primary bath clerestory"),
        dict(kind="slider", off=15.5, w=18.0, sill=0.0, head=9.0, panels=4,
             name="Great room to veranda"),
        dict(kind="fixed", off=37.0, w=8.0, sill=3.6, head=9.0, name="Kitchen window"),
    ]),
    dict(id="W", a=(6, 80), b=(6, 30), finish="stucco", openings=[
        dict(kind="casement", off=24.0, w=4.0, sill=2.5, head=9.0, name="Bed 3 window"),
        dict(kind="casement", off=42.0, w=4.0, sill=2.5, head=9.0, name="Bed 2 window"),
    ]),
]

# Limestone feature plane: slides past the west wall like a free-standing fin
LIMESTONE_WALL = dict(x0=4.5, x1=28.0, y_face=30.0 - VENEER_T, y_back=30.0,
                      z0=GRADE, z1=CEIL)

# --------------------------------------------------------------------------
# Interior partitions: centerline a->b. Openings as offset/width along line.
# --------------------------------------------------------------------------
PARTITIONS = [
    # Bedroom wing
    dict(a=(23.0, 30.5), b=(23.0, 60.0), openings=[       # gallery wall
        dict(off=7.0, w=2.67, kind="door", name="Bed 2"),
        dict(off=13.0, w=2.67, kind="door", name="Bath"),
        dict(off=20.0, w=2.67, kind="door", name="Bed 3"),
    ]),
    dict(a=(6.5, 41.5), b=(23.0, 41.5), openings=[dict(off=1.5, w=4.0, kind="closet")]),
    dict(a=(6.5, 48.5), b=(23.0, 48.5), openings=[dict(off=1.5, w=4.0, kind="closet")]),
    dict(a=(13.0, 41.5), b=(13.0, 48.5), openings=[]),
    dict(a=(6.5, 45.0), b=(13.0, 45.0), openings=[]),
    # Bed 3 / kitchen
    dict(a=(6.5, 60.0), b=(23.19, 60.0), openings=[]),
    # Laundry + mechanical
    dict(a=(13.0, 60.0), b=(13.0, 65.5), openings=[dict(off=1.5, w=2.67, kind="door")]),
    dict(a=(6.5, 65.5), b=(13.0, 65.5), openings=[]),
    # Primary suite
    dict(a=(39.0, 60.5), b=(39.0, 79.5), openings=[dict(off=1.0, w=2.67, kind="door", name="Primary")]),
    dict(a=(39.0, 71.5), b=(53.5, 71.5), openings=[
        dict(off=1.25, w=2.5, kind="door", name="WIC"),
        dict(off=8.0, w=2.5, kind="door", name="Primary bath"),
    ]),
    dict(a=(45.5, 71.5), b=(45.5, 79.5), openings=[]),
]

# --------------------------------------------------------------------------
# Rooms (interior clear polygons) for labels & area schedule
# --------------------------------------------------------------------------
ROOMS = [
    dict(name="Living", poly=[(28.5, 60.5), (38.8, 60.5), (38.8, 79.5), (28.5, 79.5)], label=(33.6, 66.0)),
    dict(name="Dining", poly=[(20.0, 60.2), (28.5, 60.2), (28.5, 79.5), (20.0, 79.5)], label=(24.2, 66.0), show_area=False),
    dict(name="Kitchen", poly=[(6.5, 65.7), (20.0, 65.7), (20.0, 79.5), (6.5, 79.5)], label=(14.5, 67.6)),
    dict(name="Laundry", poly=[(6.5, 60.2), (12.8, 60.2), (12.8, 65.3), (6.5, 65.3)], label=(9.7, 62.8), small=True),
    dict(name="Primary Bedroom", poly=[(39.2, 60.5), (53.5, 60.5), (53.5, 71.3), (39.2, 71.3)], label=(46.4, 66.4)),
    dict(name="Walk-in", poly=[(39.2, 71.7), (45.3, 71.7), (45.3, 79.5), (39.2, 79.5)], label=(42.2, 76.0), small=True),
    dict(name="Primary Bath", poly=[(45.7, 71.7), (53.5, 71.7), (53.5, 79.5), (45.7, 79.5)], label=(49.6, 77.8), small=True),
    dict(name="Bedroom 3", poly=[(6.5, 48.7), (22.8, 48.7), (22.8, 59.8), (6.5, 59.8)], label=(14.6, 55.6)),
    dict(name="Bath 2", poly=[(13.2, 41.7), (22.8, 41.7), (22.8, 48.3), (13.2, 48.3)], label=(18.0, 45.0), small=True),
    dict(name="Cl.", poly=[(6.5, 41.7), (12.8, 41.7), (12.8, 44.8), (6.5, 44.8)], label=(9.7, 43.3), small=True, show_area=False),
    dict(name="Cl.", poly=[(6.5, 45.2), (12.8, 45.2), (12.8, 48.3), (6.5, 48.3)], label=(9.7, 46.8), small=True, show_area=False),
    dict(name="Bedroom 2", poly=[(6.5, 30.5), (22.8, 30.5), (22.8, 41.3), (6.5, 41.3)], label=(14.6, 34.6)),
    dict(name="Gallery", poly=[(23.2, 30.5), (27.5, 30.5), (27.5, 60.2), (23.2, 60.2)], label=(25.35, 47.0), vertical=True),
]

OUTDOOR = [
    dict(name="Pátio (courtyard)", poly=[(28, 36), (54, 36), (54, 60), (28, 60)], label=(46.5, 39.0)),
    dict(name="Covered entry", poly=[(28, 30.33), (54, 30.33), (54, 36), (28, 36)], label=(43.0, 33.2)),
    dict(name="Veranda", poly=[(18, 80), (41, 80), (41, 92), (18, 92)], label=(31.0, 90.6)),
]

# --------------------------------------------------------------------------
# Roof: one continuous thin plate (low slope 1/4":12" to scuppers on north)
# --------------------------------------------------------------------------
ROOF = [(3, 27), (57, 27), (57, 36), (31, 36), (31, 56), (57, 56), (57, 83),
        (43, 83), (43, 92.5), (16, 92.5), (16, 83), (3, 83)]

# Soffit zones finished in cedar tongue & groove (the rest: smooth white)
CEDAR_SOFFITS = [
    dict(name="Entry canopy", x0=28.0, x1=57.0, y0=27.0, y1=36.0, dir="y"),
    dict(name="Gallery eave", x0=28.0, x1=31.0, y0=36.0, y1=56.0, dir="y"),
    dict(name="Courtyard eave", x0=28.0, x1=57.0, y0=56.0, y1=60.0, dir="y"),
    dict(name="Veranda", x0=16.0, x1=43.0, y0=80.0, y1=92.5, dir="y"),
]
# Interior ceilings in cedar (continuous with the soffits outside)
CEDAR_CEILINGS = [
    dict(name="Great room", x0=6.5, x1=38.81, y0=60.19, y1=79.5, dir="y"),
    dict(name="Gallery", x0=23.19, x1=27.5, y0=30.5, y1=60.19, dir="y"),
    dict(name="Primary bath", x0=45.69, x1=53.5, y0=71.69, y1=79.5, dir="y"),
]

# Slender steel posts (4" square, dark bronze)
POSTS = [(53.6, 30.8), (53.6, 35.6), (18.4, 91.6), (40.6, 91.6)]

# --------------------------------------------------------------------------
# Signature screens
# --------------------------------------------------------------------------
BLOCK = 1.0  # 12" x 12" x 4" precast concrete breeze block
COBOGO = dict(x0=33.0, x1=54.0, y=30.0, t=0.33, z0=FF, z1=CEIL,
              base=(GRADE, FF))   # cast concrete curb under the blocks
ENTRY_GATE = dict(x0=28.5, x1=32.5, y=30.0, z0=HARDSCAPE, z1=CEIL)  # cedar slat pivot gate
CEDAR_SCREEN = dict(x=54.0, y0=30.33, y1=60.0, z0=HARDSCAPE, z1=CEIL,
                    slat_w=1.5 / 12, slat_d=3.5 / 12, gap=2.0 / 12)

# --------------------------------------------------------------------------
# Furniture & fixtures (plan symbols + 3D). x,y = center; w along x, d along y
# --------------------------------------------------------------------------
FURNITURE = [
    # Kitchen
    dict(t="counter", x=7.75, y=74.25, w=2.5, d=10.5),     # west run (range)
    dict(t="counter", x=13.9, y=78.25, w=10.5, d=2.5),    # north run under window (sink)
    dict(t="tall", x=7.75, y=67.35, w=2.5, d=3.3),        # fridge + pantry column
    dict(t="island", x=14.5, y=71.6, w=8.0, d=3.5),
    dict(t="stool", x=12.2, y=69.2), dict(t="stool", x=14.5, y=69.2), dict(t="stool", x=16.8, y=69.2),
    # Dining
    dict(t="dining_table", x=24.6, y=72.0, w=7.0, d=3.4, chairs=6),
    dict(t="pendant", x=24.6, y=72.0),
    # Living
    dict(t="rug", x=33.6, y=70.0, w=9.0, d=12.0),
    dict(t="sofa", x=37.2, y=70.0, w=3.2, d=8.5, face="w"),
    dict(t="coffee_table", x=33.8, y=70.0, w=2.6, d=4.2),
    dict(t="lounge_chair", x=30.4, y=67.6, face="e"),
    dict(t="lounge_chair", x=30.4, y=72.4, face="e"),
    # Primary
    dict(t="bed", x=50.3, y=66.0, w=6.8, d=6.3, face="w", size="king"),
    dict(t="nightstand", x=52.8, y=62.0), dict(t="nightstand", x=52.8, y=70.0),
    # primary bath: see PRIMARY_BATH below (walk-in wet room, floating vanity, wall-hung wc)
    dict(t="wc_wall", x=53.0, y=73.2, face="w"),
    # Bedroom 2 & 3
    dict(t="bed", x=19.2, y=36.0, w=7.0, d=5.0, face="w", size="queen"),
    dict(t="desk", x=8.0, y=36.0, w=2.0, d=4.5),
    dict(t="bed", x=19.2, y=54.2, w=7.0, d=5.0, face="w", size="queen"),
    dict(t="desk", x=8.0, y=54.2, w=2.0, d=4.5),
    # Bath 2
    dict(t="tub", x=20.3, y=45.0, w=5.0, d=6.2, face="w"),
    dict(t="vanity", x=14.2, y=46.0, w=1.8, d=4.0),
    dict(t="wc", x=14.6, y=42.8, face="e"),
    # Laundry
    dict(t="washer", x=7.7, y=62.0), dict(t="dryer", x=10.4, y=62.0),
    # Veranda
    dict(t="grill_counter", x=19.75, y=85.2, w=2.5, d=7.5),
    dict(t="outdoor_table", x=27.6, y=86.2, w=8.0, d=3.5, chairs=8),
    dict(t="planter", x=39.6, y=81.4), dict(t="planter", x=17.3, y=91.2),
    dict(t="credenza", x=18.0, y=61.0, w=7.0, d=1.5),
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
    room=(45.69, 71.69, 53.5, 79.5),              # x0, y0, x1, y1 (clear)
    shower=(45.69, 76.5, 53.5, 79.5),             # full-width walk-in along the north wall
    glass=(45.69, 50.4, 76.5),                    # fixed glass panel x0..x1 at y; entry 50.4..53.5
    rain_head=(47.4, 78.0),
    bench=(45.69, 76.6, 47.0, 79.4),              # floating limestone bench at the west end
    vanity=(45.69, 72.2, 47.45, 76.2),            # floating rift-oak vanity on the west wall
    sink=(46.55, 74.2), mirror=(74.2, 2.4),       # vessel sink; round mirror center y, diameter
    sconces=(72.85, 75.55),
    plant=(52.8, 75.5),
)
BATH_FINISHES = [
    ("Floor", "Ladrilho hidráulico", "8x8 cement-look porcelain, terracotta / bone / green"),
    ("Shower walls", "Azulejo / zellige", "2.5x8 handmade-look green glazed tile, floor to ceiling"),
    ("Vanity", "Tauari / freijó", "Floating rift white oak, honed limestone top, vessel sink"),
    ("Fixtures", "Metais dourados", "Brushed brass rain head, wall faucet, round mirror, sconces"),
    ("Ceiling", "Freijó forro", "Clear cedar T&G (sealed), continuous with the bedroom wing"),
]

# --------------------------------------------------------------------------
# Site & landscape
# --------------------------------------------------------------------------
TREES = [
    dict(kind="live_oak", x=31.0, y=110.0, h=38, spread=58, seed=7, note="Heritage live oak (protected), house is set back to save it"),
    dict(kind="live_oak", x=44.0, y=46.5, h=24, spread=22, seed=3, crown=0.42, leaf=0.75,
         note="Courtyard tree (Monterrey or live oak), limbed up to ~9 ft"),
    dict(kind="live_oak", x=-3.0, y=6.0, h=28, spread=34, seed=11, note="Front yard live oak (lot corner)"),
    dict(kind="live_oak", x=58.0, y=-8.0, h=24, spread=28, seed=19, note="Street tree"),
]

PATHS = [
    # stepping slabs from the sidewalk to the gate (3' x 1.5' limestone)
    dict(kind="steps", x=30.5, y0=0.0, y1=29.5, w=3.0, d=1.5, gap=1.0),
]
# Ribbon parking pad (east side, beside — not in front of — the cobogó)
DRIVEWAY = dict(strips=[(55.5, 57.5), (61.0, 63.0)], y0=CURB_Y, y1=26.0)

PLANTING = [
    dict(name="Front meadow", poly=[(0.5, 0.5), (29.0, 0.5), (29.0, 27.0), (0.5, 27.0)]),
    dict(name="Front meadow E", poly=[(32.0, 0.5), (54.8, 0.5), (54.8, 26.5), (32.0, 26.5)]),
    dict(name="Courtyard garden", poly=[(31.5, 36.5), (53.5, 36.5), (53.5, 52.0), (31.5, 52.0)]),
    dict(name="Rear meadow", poly=[(0.5, 93.5), (64.5, 93.5), (64.5, 124.5), (0.5, 124.5)]),
]

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
        lot=LOT_W * LOT_D,
    )


FINISHES = [
    # (element, Brazilian reference, Austin specification)
    ("Feature wall", "Pedra São Tomé / moledo", "Lueders cream limestone, sawn-face ashlar, 3 course heights"),
    ("Courtyard screen", "Cobogó (Recife, 1929)", "12x12x4 precast concrete breeze block, white cement, circle pattern"),
    ("Exterior walls", "White mineral plaster", "Smooth 3-coat stucco, warm white, sand finish"),
    ("Roof edge", "Thin concrete slab edge", "15\" dark bronze aluminum fascia, low-slope TPO roof behind"),
    ("Soffits & great room ceiling", "Freijó / tauari ceiling", "Clear western red cedar T&G 1x6, natural oil"),
    ("Screens & gate", "Muxarabi / brise-soleil", "Cedar 2x4 slats @ 5\" o.c. on steel frame"),
    ("Windows & doors", "Slim steel frames", "Dark bronze thermally broken aluminum, 9' sliders"),
    ("Floors (inside)", "Cimento queimado", "Polished, sealed concrete slab, warm gray"),
    ("Floors (outside)", "Pedra São Tomé paving", "Lueders limestone pavers 24x36, thermal finish"),
    ("Kitchen", "Dark stone + light wood", "Rift white oak cabinets, honed black granite, green glazed tile"),
    ("Landscape", "Tropical garden", "Live oak, dwarf palmetto, agave, sotol, muhly grass, decomposed granite"),
]


if __name__ == "__main__":
    import json
    print(json.dumps(area_schedule(), indent=2))
    for r in ROOMS:
        print(f"{r['name']:<18}{poly_area(r['poly']):7.0f} sf")
