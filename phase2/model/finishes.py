"""Phase 2 finishes: one palette for Casa 02 and the Casita, the same family as Casa 01.

Each entry: (element, Brazilian reference, Austin specification, where). Used by the drawings' finish schedule,
the lookbook, the web material board and (by key) the renders. Keys match the Casa 01 material library and
swatches (casa01/render/materials.py, casa01/renders/swatches).
"""

EXTERIOR = [
    dict(key="stucco", name="Warm-white stucco", ref="White mineral plaster",
         spec="Smooth 3-coat stucco, warm white, sand finish; control joints at the floor band",
         where="The upper floor and most walls"),
    dict(key="limestone", name="Lueders limestone", ref="Pedra São Tomé / moledo",
         spec="Thin-cut sawn-face ashlar (1 to 1.5 in), 3 course heights (4, 8, 12 in), adhered; thin limestone cap",
         where="Corner walls, the side-drive street wall, garden and mailbox walls"),
    dict(key="cobogo", name="Concrete cobogó", ref="Cobogó, Recife 1929",
         spec="12x12x4 precast breeze block, white cement, circle pattern; steel frame and ties at 2 stories",
         where="The two-story lantern, the Casita's garden wall"),
    dict(key="cedar_z", name="Western red cedar", ref="Freijó / ipê",
         spec="Clear 2x2 slats at 3.5 in on dark bronze frames; 1x6 T&G soffits; natural oil",
         where="Carport and garden gates, the back sunshade, soffits, carport and porch ceilings"),
    dict(key="bronze", name="Dark bronze aluminum", ref="Slim steel frames",
         spec="Thermally broken windows and sliders, low-E; 15 in fascia; the floor band; posts and columns",
         where="Windows, the floor band, roof edge, posts"),
    dict(key="calcada", name="Black stone mosaic", ref="Calçada portuguesa",
         spec="Black basalt setts on a sand-cement bed, 6 in light concrete band (or Antika Onyx Black pavers)",
         where="About 50 sf a home: carport rug, threshold under the cobogó, Casita stoop"),
    dict(key="pavers", name="Limestone pavers", ref="São Tomé paving",
         spec="Lueders 24x36 thermal finish, sand joints", where="Terraces and stepping stones"),
    dict(key="dg", name="Decomposed granite", ref="Terra batida",
         spec="Stabilized DG with steel edging; agave, sotol, feather grass, boulders",
         where="Front yards"),
]

INTERIOR = [
    dict(key="floor", name="Polished concrete", ref="Cimento queimado",
         spec="Slab on grade, light grind, penetrating sealer, warm gray", where="Ground floors"),
    dict(key="oak", name="Rift white oak", ref="Tauari / freijó",
         spec="Flat-sawn rift oak, matte oil: cabinets, vanities, doors, open stair treads; 5 in floor boards upstairs",
         where="Kitchen, baths, doors, stair, upper floors"),
    dict(key="granite", name="Honed black granite", ref="Preto São Gabriel",
         spec="1.25 in honed counters and island top, eased edge", where="Kitchen"),
    dict(key="tile", name="Green glazed tile", ref="Azulejo",
         spec="2.5x8 zellige-look glazed porcelain, green, stacked: backsplash to the shelf, primary shower to the ceiling",
         where="Kitchen backsplash, primary shower, Casita shower"),
    dict(key="zellige_terracotta", name="Terracotta tile", ref="Azulejo terracota",
         spec="2.5x8 zellige-look glazed porcelain, terracotta, around the tub", where="Bath 2"),
    dict(key="brass", name="Brushed brass", ref="Metais dourados",
         spec="Faucets, shower trims, cabinet pulls, sconces, door levers", where="Kitchen and baths"),
]

KITCHEN = [
    ("Layout", "Counter on the wall; a 10 ft granite island with an oak dining table built onto its living-room side "
               "(seats four); panel-ready fridge in oak"),
    ("Cabinets", "Rift white oak slab doors, 1/8 in reveals, no uppers: one oak shelf over a green tile backsplash"),
    ("Counters", "Honed black granite, 1.25 in; the island top runs as one slab with seating for four"),
    ("Appliances", "30 in induction range with a plaster hood, dishwasher, 30 in panel-ready fridge"),
    ("Sink + faucet", "Undermount single bowl, brushed brass bridge faucet"),
    ("Lighting", "Two opal-glass globe pendants over the island, recessed cans, LED under the shelf"),
]

BATHS = [
    ("Primary bath", "Walk-in shower under a skylight, green zellige to the ceiling, glass panel, brass rain head; "
                     "floating oak vanity with a honed limestone top; round mirror and two brass sconces"),
    ("Bath 2", "Tub with terracotta zellige to the ceiling and a skylight overhead; oak vanity, pill mirror"),
    ("Powder room (WC)", "Lime-wash walls, a floating limestone sink slab, brass faucet; 32 in clear door"),
    ("Casita bath", "Shower under a skylight, green zellige, oak vanity, brass"),
    ("All baths", "Honed concrete or matte mosaic floor, wall-hung wc, exhaust fan to the roof"),
]

DETAILS = [
    ("Stair", "Open rift oak treads with a riser bar, steel stringer, cedar slats on the hall side, wall rail in oak"),
    ("Doors", "8 ft solid-core rift oak slabs, brass levers; bypass oak closet doors"),
    ("Skylights", "Fixed, laminated low-E on 6 in curbs: stair, primary shower, tub, walk-in, laundry; Casita shower, hall, closet"),
    ("Ceilings", "9'-6\" ground floor, painted; upstairs, cedar T&G under the roof as in Casa 01's great room; "
                 "cedar in the carport and porch"),
    ("Lighting", "Warm 2700 K, dimmable; lantern light at the landing behind the cobogó; path lights"),
    ("Mechanical", "Ducted heat pump, heat-pump water heater, ERV; rooftop solar, about 3 kW a home"),
]


def all_materials():
    return EXTERIOR + INTERIOR
