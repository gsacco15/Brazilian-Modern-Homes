"""Casa 01 V2 layout sign-off drawings (V1 files stay untouched for comparison).

    python3 casa01/signoff/build_v2.py   ->  casa01/drawings/v2/*.svg, *.dxf, schedules.json
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
sys.path.insert(0, CASA)
import drawings          # noqa: E402
import drawings_cd       # noqa: E402

V2 = os.path.join(CASA, "drawings", "v2")
os.makedirs(V2, exist_ok=True)
drawings.OUT = drawings_cd.OUT = V2
import design as D       # noqa: E402

# without the carport gate (add alternate 1 left out; the rough-in is still built)
def front(name):   # clean street front for the with/without comparison (no trees or labels)
    orig = drawings.elev_tree
    drawings.elev_tree = lambda *a, **k: None
    try:
        os.replace(drawings.south_elevation(ztop=16, notes=False), os.path.join(V2, name))
    finally:
        drawings.elev_tree = orig
    print(name)


front("32_front_gate.svg")
D.CARPORT_SLIDER["installed"] = False
front("32_front_nogate.svg")
os.replace(os.path.join(V2, drawings_cd.floor_plan_cd()), os.path.join(V2, "30_floor_plan_cd_nogate.svg"))
print(drawings_cd.elev_cd("32_elev_s_cd_nogate.svg", "s"))
D.CARPORT_SLIDER["installed"] = True
# base set, with the gate
print(drawings_cd.floor_plan_cd())
print(drawings.site_plan())
print(drawings_cd.elev_cd("32_elev_s_cd.svg", "s"))
try:
    import drawings_dxf
    drawings_dxf.main(os.path.join(V2, "30_floor_plan_cd.svg"), os.path.join(V2, "A-101_Floor_Plan_V2.dxf"))
except ImportError:
    print("ezdxf not installed: skipped the DXF (pip install ezdxf)")
