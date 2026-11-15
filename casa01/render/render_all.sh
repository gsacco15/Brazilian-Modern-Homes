#!/usr/bin/env bash
# Final render batch (CPU, ~1.5-2 h on 4 cores). Usage: render_all.sh <python-with-bpy>
set -e
PY=${1:-python}
cd "$(dirname "$0")"
$PY render.py --views street,courtyard,street_dusk,aerial,entry,veranda,rear --res 1600 --samples 96
$PY render.py --views interior,kitchen,gallery --res 1600 --samples 128
