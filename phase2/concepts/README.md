# Phase 2 concept drawings

Casa 02 and Casita floor plans, and site plans that place them on the winning test-fit layouts.

```
python3 phase2/concepts/concepts.py
node casa01/signoff/print_pdf.js phase2/concepts/out/concepts.html phase2/concepts/Phase2_Concepts.pdf
```

- `../model/homes.py` holds the plans as data (walls, doors, windows, rooms, fixtures): Casa 02 ground floor with a
  carport, Casa 02 ground floor with a suite, the shared upper floor, and the Casita.
- `concepts.py` draws them and the site plans from `../model/sites.py`. Each site is checked against the HOME caps:
  floor area, footprint, impervious cover, front-yard paving, parking and carts.
- `Phase2_Concepts.pdf` is the sheet set: C-1 Casa 02, C-2 Casita, C-3 to C-7 site plans.

Still to come: a side-loaded ground floor (car enters the bay from a side drive) for the 65-ft and deep-lot
trios, elevations and massing renders.
