"""Start the extracted demo with the Python standard library."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse, webbrowser
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=4173)
    args=parser.parse_args()
    handler=partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parent)
    with ThreadingHTTPServer(('127.0.0.1',args.port),handler) as server:
        url=f'http://127.0.0.1:{server.server_port}/index.html'
        print(url,flush=True)
        webbrowser.open(url)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
