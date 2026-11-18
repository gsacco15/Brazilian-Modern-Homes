# Phase 2 test-fit study

Duo and trio layouts as plain boxes on six standard Austin lots, each checked against the HOME rules
(setbacks, building coverage, impervious cover, front-yard paving, floor-area caps, parking, pátio sun).
For every layout the script also finds the deepest Casa 02 that still passes, which sets the design target.

```
python3 phase2/testfit/testfit.py
node casa01/signoff/print_pdf.js phase2/testfit/out/testfit.html phase2/testfit/Phase2_TestFit.pdf
```

- `testfit.py` holds the rules, the six lots and the 19 layouts. Change a number (say the Casa 02 depth or
  the rear setback) and rerun.
- `Phase2_TestFit.pdf` is the 8-sheet result: summary, one sheet per lot, findings.
- `out/results.json` has every number behind the sheets.

Result (Nov 2026): design Casa 02 at 20 x 39 ft (about 1,360 sf plus a carport bay under the upper floor)
and the Casita at 20 x 32 ft. Rules marked "confirm" still need an answer from the city.
