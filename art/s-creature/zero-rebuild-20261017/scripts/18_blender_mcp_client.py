"""Local Blender MCP socket client; Blender must be running with the addon.

Usage: python3 18_blender_mcp_client.py script.py [--output response.json]
Runs the given reviewed Python script on Blender's main thread.
"""
import argparse
import json
import socket
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('script', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
script = args.script.resolve()
code = 'exec(compile(' + repr(script.read_text()) + ', ' + repr(str(script)) + ", 'exec'), {'__file__': " + repr(str(script)) + "})"
with socket.create_connection(('127.0.0.1', 9876), timeout=15) as connection:
    connection.settimeout(600)
    connection.sendall(json.dumps({'type': 'execute_code', 'params': {'code': code}}).encode())
    chunks = b''
    while True:
        chunk = connection.recv(1024 * 1024)
        if not chunk:
            raise RuntimeError('MCP disconnected before a complete response')
        chunks += chunk
        try:
            result = json.loads(chunks)
            break
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
if args.output:
    assert not args.output.exists(), args.output
    args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
assert result.get('status') == 'success', result
