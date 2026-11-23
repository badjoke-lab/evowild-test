"""Measure unioned event durations inside each of 96 Chromium callback intervals."""
import csv
import json
import sys
from pathlib import Path

trace,out=map(Path,sys.argv[1:3])
events=json.loads(trace.read_text())['traceEvents']
pids={e['args']['name']:e['pid'] for e in events if e['name']=='process_name'}
marks=sorted(e['ts'] for e in events if e['name'].startswith('ridgeFollowFrame'))
assert len(marks)==121
tracked={
    'renderer_main_animation_callbacks':('Renderer',{'FireAnimationFrame'}),
    'renderer_main_style_layout_paint':('Renderer',{'UpdateLayoutTree','Layout','PrePaint','Paint','Layerize'}),
    'renderer_main_command_flush':('Renderer',{'GpuChannelHost::VerifyFlush','CommandBufferHelper::Flush','CommandBufferProxyImpl::Flush'}),
    'gpu_process_main_scheduled_task':('GPU Process',{'Scheduler::RunTask'}),
    'gpu_process_main_deferred_request':('GPU Process',{'GpuChannel::ExecuteDeferredRequest'}),
}
def union(intervals,left,right):
    last=left
    duration=0
    for start,end in intervals:
        if start>=right:break
        duration+=max(0,min(end,right)-max(left,start,last))
        last=max(last,end)
    return round(duration/1000,3)
by_group={}
for group,(process,names) in tracked.items():
    pid=pids[process]
    by_group[group]=sorted((e['ts'],e['ts']+e['dur']) for e in events
        if e.get('ph')=='X' and e.get('dur') and e['pid']==pid and e['tid']==pid and e['name'] in names)
rows=[]
for end in range(24,120):
    left,right=marks[end-1:end+1]
    rows.append(dict(end_mark=end+1,gap_ms=round((right-left)/1000,3),
                     **{k+'_ms':union(v,left,right) for k,v in by_group.items()}))
with out.open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');writer.writeheader();writer.writerows(rows)
