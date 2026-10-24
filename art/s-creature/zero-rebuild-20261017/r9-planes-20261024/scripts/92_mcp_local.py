"""Use the existing Blender MCP addon's local command transport.

The session has no exposed Blender tool schema; no plugin/config installation is
performed. JSON commands are handled by the running addon on Blender's main thread.
Usage: python3 92_mcp_local.py SCRIPT RESPONSE_JSON [JSON_GLOBALS]
"""
import sys,socket,json,hashlib,datetime
from pathlib import Path
script=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);assert not out.exists()
scope=script.parents[1];assert scope.name=='r9-planes-20261024'
extra=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
code='from pathlib import Path\nimport json\np='+repr(str(script))+'\ng={"__file__":p}\ng.update(json.loads('+repr(json.dumps(extra))+'))\nexec(compile(Path(p).read_text(),p,"exec"),g)'
command={'type':'execute_code','params':{'code':code},'user_prompt':'Blender MCPで既存メッシュを実際に編集すること。'}
with socket.create_connection(('localhost',9876),timeout=15) as sock:
    sock.settimeout(300);sock.sendall(json.dumps(command).encode());buffer=b''
    while True:
        chunk=sock.recv(65536)
        if not chunk:raise RuntimeError('Blender MCP disconnected before a complete response')
        buffer+=chunk
        try:response=json.loads(buffer);break
        except (ValueError,UnicodeDecodeError):pass
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'transport':'existing Blender MCP addon localhost:9876','script':str(script.relative_to(scope)),'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'user_prompt':command['user_prompt'],'globals':extra,'response':response}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(response,ensure_ascii=False))
assert response.get('status')=='success',response
assert response.get('result',{}).get('executed') is True,response
