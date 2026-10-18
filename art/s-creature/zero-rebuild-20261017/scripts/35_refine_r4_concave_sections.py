"""Keep R3 crown outlines and retopologize their concave interiors in place.

The initial radial fan is unsuitable for the twisted sections; C still had
main-crown overlap candidates near the tapered area. D preserves the original
contour vertices, replaces only the internal fan edges with concave-polygon
triangulation, and gives corresponding front/back surfaces positive depth.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('29_sculpt_r4_crown.py')),
              init_globals={'R4_TRIAL':'D'})
