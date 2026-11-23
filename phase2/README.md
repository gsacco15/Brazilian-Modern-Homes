# Phase 2: duo and trio homes

One model, many outputs. Every drawing, the AutoCAD file and the 3D views are generated from the two files
in `model/`, so a change made there shows up everywhere on the next run.

## Names (one ID system)

| Thing | Name | Meaning |
| --- | --- | --- |
| Two-story home | **Casa 02** | 20 x 39 ft, 3 bed / 2.5 bath (1,350 sf), or 3 bed + den / 3.5 bath with the suite (1,560 sf) |
| Casa 02 floors | **C02-GC**, **C02-GS**, **C02-UP** | Ground floor with carport, ground floor with suite, upper floor (same for both) |
| One-story home | **Casita**, **CS** | 20 x 32 ft, 1 bed + flex / 1 bath, 640 sf |
| Lots | **L1 to L6** | 50 x 125, 50 x 125 with alley, 60 x 125 corner, 65 x 125, 50 x 175, small-lot split |
| Layouts | **L1-D1**, **L1-T1**, ... | Lot, then D (duo), T (trio) or S (split), then option number |
| Homes on a lot | **A, B, C** | A and B are the Casa 02 pair, C the Casita or the third home |

The test-fit study tried 19 layouts. Five are developed so far, and each keeps its test-fit ID:

| Layout | Lot | Homes | Parking | Concept sheet |
| --- | --- | --- | --- | --- |
| L1-D1 | 50 x 125 | Casa 02 pair, side by side | Carport bays at the street, cedar gates | C-3 |
| L1-T1 | 50 x 125 | Casa 02 pair + Casita behind | Pair in carports; Casita on foot | C-4 |
| L2-T2 | 50 x 125 with alley | Casita at the street + Casa 02 pair on the alley | Pair off the alley; Casita on the street | C-5 |
| L3-T1 | 60 x 125 corner | Casa 02 pair + Casita on the side street | Every home on site | C-6 |
| L4-D2 | 65 x 125 | Casa 02 front and back, suite versions | Pads beside one shared drive | C-7 |

## Folders

| Folder | What it holds | How to rebuild |
| --- | --- | --- |
| `model/` | `homes.py`: the plans as data. `sites.py`: where each home sits on each lot | Edit these |
| `testfit/` | 19 massing layouts checked against the HOME rules | `python3 phase2/testfit/testfit.py` |
| `concepts/` | `Phase2_Concepts.pdf`: plans, site plans, checks and 3D views | `python3 phase2/concepts/concepts.py`, then `node casa01/signoff/print_pdf.js phase2/concepts/out/concepts.html phase2/concepts/Phase2_Concepts.pdf` |
| `cad/` | `Phase2_Concepts.dxf`: AutoCAD, in inches | `python3 phase2/cad/export_dxf.py` (needs ezdxf) |
| `render/` | Low-detail 3D views of each layout (`out/<layout>_aerial.png`, `_street.png`) | `<blender python> phase2/render/build.py` |

## The AutoCAD file

- Each plan is a block: `C02-GC`, `C02-GS`, `C02-UP`, `CS`. The sites insert those blocks, mirrored or rotated.
  Redefine a block and every layout that uses it updates.
- Layers follow the AIA style: `A-WALL`, `A-DOOR`, `A-GLAZ`, `A-FLOR-FIXT`, `C-PROP` (lot line), `C-SETB`
  (setbacks), `C-PAVE`, `L-PLNT`, `L-TREE`, `L-FENC`, and so on.
- Paper space has one layout per sheet: `C-1 Casa 02`, `C-2 Casita`, `C-3 L1-D1` to `C-7 L4-D2`, each with a
  title block and a viewport at a standard scale.

## To change something

1. Edit `model/homes.py` (a plan) or `model/sites.py` (a layout).
2. Rebuild the concept sheets, the AutoCAD file and the renders with the commands above.
3. To add a layout, give it its test-fit ID and add it to `sites.py`. It then appears in every output.
