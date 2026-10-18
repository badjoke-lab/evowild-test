"""Revert trial A and sculpt trial B from the protected R3 mesh, via MCP.

Visual A review: retain its root seating; reduce its angular mid-height flare
and replace the approximate lateral field with interpolated cage depth so
each crown remains a closed lenticular volume. No non-crown edits.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('29_sculpt_r4_crown.py')),
              init_globals={'R4_TRIAL':'B'})
