# Phase 2: duo and trio homes

One model, many outputs. Every drawing, the AutoCAD file and the 3D views are generated from the two files
in `model/`, so a change made there shows up everywhere on the next run.

## Names (one ID system)

| Thing | Name | Meaning |
| --- | --- | --- |
| Two-story home | **Casa 02** | 20 x 39 ft, 3 bed / 2.5 bath (1,350 sf), or 3 bed + den / 3.5 bath with the suite (1,560 sf). Facade: direction C, the cobogó lantern |
| Casa 02 floors | **C02-GC**, **C02-GS**, **C02-GD**, **C02-UP** | Ground floor with carport, with suite, with a side-drive carport across the front; upper floor (same for all) |
| One-story home | **Casita**, **CS** | 20 x 32 ft, 1 bed + flex / 1 bath, 640 sf |
| Lots | **L1 to L6** | 50 x 125, 50 x 125 with alley, 60 x 125 corner, 65 x 125, 50 x 175, small-lot split |
| Layouts | **L1-D1**, **L1-T1**, ... | Lot, then D (duo), T (trio) or S (split), then option number |
| Homes on a lot | **A, B, C** | A and B are the Casa 02 pair, C the Casita or the third home |

The test-fit study tried 19 layouts. Six are developed so far, and each keeps its test-fit ID:

| Layout | Lot | Homes | Parking | Concept sheet |
| --- | --- | --- | --- | --- |
| L1-D1 | 50 x 125 | Casa 02 pair, side by side | Carport bays at the street, cedar gates | C-3 |
| L1-T1 | 50 x 125 | Casa 02 pair + Casita behind | Pair in carports; Casita on foot | C-4 |
| L2-T2 | 50 x 125 with alley | Casita at the street + Casa 02 pair on the alley | Pair off the alley; Casita on the street | C-5 |
| L3-T1 | 60 x 125 corner | Casa 02 pair + Casita on the side street | Every home on site | C-6 |
| L4-D2 | 65 x 125 | Casa 02 front and back, suite versions | Pads beside one shared drive | C-7 |
| L4-T1 | 65 x 125 | Casa 02 pair (side drive) + Casita behind | One shared drive; bays across each front | C-8 |

## Folders

| Folder | What it holds | How to rebuild |
| --- | --- | --- |
| `model/` | `homes.py`: the plans as data. `sites.py`: where each home sits on each lot. `finishes.py`: the finish schedule and material board | Edit these |
| `testfit/` | 19 massing layouts checked against the HOME rules | `python3 phase2/testfit/testfit.py` |
| `concepts/` | `Phase2_Concepts.pdf`: plans, site plans, checks and 3D views | `python3 phase2/concepts/concepts.py`, then `node casa01/signoff/print_pdf.js phase2/concepts/out/concepts.html phase2/concepts/Phase2_Concepts.pdf` |
| `cad/` | `Phase2_Concepts.dxf`: AutoCAD, in inches | `python3 phase2/cad/export_dxf.py` (needs ezdxf) |
| `render/` | Low-detail 3D views of each layout (`out/<layout>_aerial.png`, `_street.png`); and `hifi.py`, the high-detail scene at Casa 01 quality with interiors and a neighbourhood. The final set is in `final/`: the duo by day and dusk, the entry, the pátio, the kitchen, the primary bath, the upstairs hall, the Casita at the street, the side-drive trio, a trio from above | `<blender python> phase2/render/build.py`; `<blender python> phase2/render/hifi.py --res 1600 --samples 96 --out phase2/render/final` |
| `lookbook/` | `Phase2_Lookbook.pdf` (in `phase2/`): the Casa 01-style lookbook in five parts: I The duo, II Inside, III The trio, IV The homes (plans, elevations, sections), V Finishes | `python3 phase2/lookbook/build.py`, then `node phase2/lookbook/make_pdf.js` |
| `plans/` | `Phase2_Casa02_Plans.pdf`: the developed Casa 02 plans A-101 to A-104 (dimensions, door and window tags and schedules, room areas, general notes), elevations A-201 to A-204 and sections A-301 (`elevations.py`). The same sheets are in the AutoCAD file | `python3 phase2/plans/plans.py`, then `node casa01/signoff/print_pdf.js phase2/plans/out/plans.html phase2/plans/Phase2_Casa02_Plans.pdf` |
| `web/` | The website's `/homes/` page: Single (Casa 01), Duo and Trio, each with photos, site layouts and floor plans, and the material board. Generated from the model and renders; `scripts/vercel-build.sh` serves `web/site/` at `/homes/` | `python3 phase2/web/build.py` |
| `study/` | `Phase2_Facade_Options.pdf`: the Casa 02 facade study (as drawn, A cedar veil, B stepped, C cobogó lantern), same lots and cameras. Chosen: C, plus a cedar gate in the Casita garden wall (`Cplus`, sheet F-6) | `<blender python> phase2/study/facade_study.py`, then `python3 phase2/study/sheet.py` and `node casa01/signoff/print_pdf.js phase2/study/out/facade_options.html phase2/study/Phase2_Facade_Options.pdf` |

## The AutoCAD file

- Each plan is a block: `C02-GC`, `C02-GS`, `C02-GD`, `C02-UP`, `CS`, `CS-NP` (the Casita without its porch). The sites
  insert those blocks, mirrored or rotated.
  Redefine a block and every layout that uses it updates.
- Layers follow the AIA style: `A-WALL`, `A-DOOR`, `A-GLAZ`, `A-FLOR-FIXT`, `C-PROP` (lot line), `C-SETB`
  (setbacks), `C-PAVE`, `L-PLNT`, `L-TREE`, `L-FENC`, and so on.
- Developed sheets `A-101 C02-GC`, `A-102 C02-GS`, `A-104 C02-GD`, `A-103 C02-UP` sit below the concept plans in model
  space, with dimension strings, door and window tags (layer `A-ANNO-SYMB`) and the schedules in paper space
  (`A-ANNO-SCHD`). Elevations and sections (`A-201` to `A-204`, `A-301`) sit below those, on `A-ELEV`, `A-ELEV-PATT`,
  `A-ELEV-GLAZ` and `A-SECT`.
- Paper space has one layout per sheet: `C-1 Casa 02`, `C-2 Casita`, `C-3 L1-D1` to `C-8 L4-T1`, `A-101` to `A-104`,
  `A-201` to `A-204` and `A-301`, each with a title block and a viewport at a standard scale.

## To change something

1. Edit `model/homes.py` (a plan) or `model/sites.py` (a layout).
2. Rebuild the concept sheets, the AutoCAD file and the renders with the commands above.
3. To add a layout, give it its test-fit ID and add it to `sites.py`. It then appears in every output.
