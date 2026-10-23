"""Restart only the installed MCP server in this Blender session after a crash.

Does not install or update anything, change preferences, or save startup files.
The Blender command line opens the saved R8 C trial before running this script.
"""
import bpy
def resume():
    server=getattr(bpy.types,'blendermcp_server',None)
    if not server or not server.running:
        result=bpy.ops.blendermcp.start_server()
        print('R8_SESSION_MCP_RESUMED',result,flush=True)
    return None
bpy.app.timers.register(resume,first_interval=1.0)
