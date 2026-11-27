"""Serve the frozen integrated game with explicitly selected surface candidates."""
import argparse
import hashlib
import http.server
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile

root=Path(__file__).resolve().parents[2]
baseline=root/'public/ridge-performance/ridge-optimized.zip'
modes=('base','group','color','both')
page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Ridge Oval 表面試験</title>
<style>body{max-width:780px;margin:32px auto;padding:16px;font:18px/1.7 system-ui}a{display:block;margin:16px 0}small{display:block}</style>
<h1>Ridge Oval 表面試験</h1><p>開始HEAD 2606922 と三つの試作を同じレースで操作できます。</p>
<a href="/base/evowild-test/?raceTrial=1">基準版</a><a href="/group/evowild-test/?raceTrial=1">三角形群カリング</a>
<a href="/color/evowild-test/?raceTrial=1">単色領域</a><a href="/both/evowild-test/?raceTrial=1">併用</a>
<a href="/report/">判定・画像・動画・測定値</a><p>頭数と編成は「出走設定」、表示は「S型表示」から選べます。</p>'''
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        address=unquote(urlsplit(self.path).path)
        if address=='/':return self.send(page.encode(),'text/html')
        if address.startswith('/report/'):
            relative=address.removeprefix('/report/') or 'index.html'
            path=(root/'public/ridge-surface'/relative).resolve()
            if not path.is_relative_to(root/'public/ridge-surface') or not path.is_file():return self.send_error(404)
            return self.send(path.read_bytes(),mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        parts=address.lstrip('/').split('/',1)
        if len(parts)!=2 or parts[0] not in modes or not parts[1].startswith('evowild-test/'):return self.send_error(404)
        mode,name=parts
        if name.endswith('/'):name+='index.html'
        if name=='evowild-test/race-integration/actors.js' and mode!='base':
            content=(root/'public/ridge-surface/variants'/(mode+'.js')).read_bytes()
        elif name=='evowild-test/ridge-surface/candidate.js':
            content=(root/'public/ridge-surface/candidate.js').read_bytes()
        else:
            with zipfile.ZipFile(baseline) as z:
                try:content=z.read(name)
                except KeyError:return self.send_error(404)
        mime=mimetypes.guess_type(name)[0] or 'application/octet-stream'
        if name.endswith(('.html','.js')):
            content=content.replace(b'/evowild-test/',('/'+mode+'/evowild-test/').encode())
            if mode!='base':
                content=content.replace(b'ridge-surface-ground-1',('surface-trial-'+mode).encode())
            if name=='evowild-test/index.html':
                title={'base':'基準2606922','group':'群カリング試作','color':'単色領域試作','both':'併用試作'}[mode]
                content=content.replace('S型レース試験</h2>'.encode(),('S型レース試験　'+title+'</h2>').encode())
        self.send(content,mime)
    def send(self,content,mime):
        self.send_response(200);self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(content)));self.end_headers()
        try:self.wfile.write(content)
        except BrokenPipeError:pass
    def log_message(self,*args):pass
if __name__=='__main__':
    args=argparse.ArgumentParser()
    args.add_argument('--port',type=int,default=8000);args.add_argument('--bind',default='0.0.0.0')
    config=args.parse_args()
    expected=json.loads((root/'public/ridge-performance/archive-check.json').read_text())['sha256']
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==expected,'Frozen baseline archive mismatch'
    print(f'Open http://localhost:{config.port}/',flush=True)
    http.server.ThreadingHTTPServer((config.bind,config.port),Handler).serve_forever()
