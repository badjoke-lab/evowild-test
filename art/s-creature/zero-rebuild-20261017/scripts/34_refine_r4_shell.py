"""Crown-only retopology after A/B rear-fan crossing diagnostics.

Reopen protected R3 and retain the trial-B section profile. Edit the existing
main/blue rear cap fans into corresponding front/back facets before twisting.
This local shell repair does not establish rigging suitability.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('29_sculpt_r4_crown.py')),
              init_globals={'R4_TRIAL':'C'})
