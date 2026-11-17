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
print(drawings_cd.floor_plan_cd())
print(drawings.site_plan())
print(drawings_cd.elev_cd("32_elev_s_cd.svg", "s"))
try:
    import drawings_dxf
    drawings_dxf.main(os.path.join(V2, "30_floor_plan_cd.svg"), os.path.join(V2, "A-101_Floor_Plan_V2.dxf"))
except ImportError:
    print("ezdxf not installed: skipped the DXF (pip install ezdxf)")
