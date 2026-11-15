# Brazilian Modern Homes — Casa 01 (Casa Pátio)

A 1,620 sf, 3-bed / 2-bath Brazilian-modern courtyard house for a central-Austin infill lot,
with photoreal renders, plans, elevations, a section, a finish board, an interactive 3D model
and a lookbook PDF. Everything is generated from **one design file**, so the pictures and the
plans always agree.

| Output | Where |
| --- | --- |
| Lookbook PDF (16 pages, 16:9) | `casa01/Casa01_Lookbook.pdf` |
| Web lookbook + interactive 3D model | `casa01/lookbook/web/` (`index.html`, `casa01.glb`) |
| Photoreal renders (Blender Cycles) | `casa01/renders/*.png` |
| Finish samples | `casa01/renders/swatches/*.png` |
| Drawings (SVG) | `casa01/drawings/` — site plan, floor plan, 4 elevations, section A-A, cobogó detail |

## The design in one paragraph

An L-shaped single-story house wraps a private pátio. One thin roof plate (15" dark bronze
fascia, 12'-3" tall) runs the full street front. The street sees a Lueders limestone wall, a
cedar slat pivot gate and a full-height 12x12 concrete cobogó screen. Inside the screen you
walk through the garden to the front door. The great room opens south to the pátio and north
to a 276 sf cedar-ceilinged veranda under a heritage live oak. Structure and systems stay
conventional: slab on grade, 2x6 framing, low-slope roof, standard 9' sliders.

## How it is built

```
casa01/design.py          single source of truth (feet): lot, walls, openings, rooms, roof,
                          screens, furniture, trees, finishes
casa01/drawings.py        -> casa01/drawings/*.svg
casa01/render/            Blender 5.3 (pip `bpy`) + Cycles scene builder
  materials.py            PBR materials (scanned CC0 maps + procedural variation)
  house.py                walls, openings, limestone ashlar, roof, cedar soffits, cobogó blocks
  landscape.py            site, street, fences, live oaks, agave, grasses, palmetto
  plants.py               procedural Texas plants (space-colonization live oak, etc.)
  furniture.py            millwork, furniture, fixtures
  render.py               cameras, sky (real HDRIs), night lights -> casa01/renders/
  swatches.py             material board tiles
  export_web.py           light GLB for the browser viewer
  fetch_assets.py         downloads the CC0 textures, skies and models (Poly Haven, ambientCG)
casa01/lookbook/          build.py (print + web HTML), webpage.py (3D viewer), make_pdf.js
```

### Regenerate everything

```bash
pip install bpy==5.3.0            # Python 3.13; Blender as a module
python3 casa01/render/fetch_assets.py
python3 casa01/drawings.py
bash casa01/render/render_all.sh python     # ~1.5-2 h on 4 CPU cores
python casa01/render/swatches.py
python casa01/render/export_web.py
python3 casa01/lookbook/build.py
node casa01/lookbook/make_pdf.js            # needs Playwright + Chromium
```

Change a number in `design.py` (say, the courtyard width or a window) and rerun: the plans,
renders, quantities and 3D model all update together.

## Status

Concept study for discussion, not for construction. Zoning, structure, energy code and site
conditions need a licensed Texas team. Budget figures are planning ranges, not bids.
Textures and models: Poly Haven and ambientCG (CC0).
