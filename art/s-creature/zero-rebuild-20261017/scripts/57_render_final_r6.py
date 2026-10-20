"""Render saved R6 using the established, unchanged R5 cameras and settings."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
log=(ROOT/'evidence/RENDER_R6_FINAL.log').open('x')
old_out=os.dup(1);old_err=os.dup(2);os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
script=ROOT/'scripts/05_review_render.py'
sys.argv=[sys.argv[0],'--','revised_r6']
exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script)})
os.dup2(old_out,1);os.dup2(old_err,2);os.close(old_out);os.close(old_err);log.close()
print('R6 FINAL: five saved-file renders complete.',flush=True)
